import streamlit as st
from pathlib import Path
from PIL import Image
import immo_core
import pdf_generator
import base64
import matplotlib.pyplot as plt

st.set_page_config(page_title="Immobilien-Analyse", page_icon="🏠", layout="wide")

# Titel und Icon
try:
    icon_path = Path(__file__).with_name("10751558.png")
    st.image(Image.open(icon_path).resize((64, 64)))
except Exception:
    pass

st.title("🏠 Immobilien-Analyse-Tool (Streamlit Edition)")
st.markdown("---")

# Nutzungsart-Auswahl
nutzungsart = st.selectbox(
    "Nutzungsart wählen",
    ["Vermietung", "Eigennutzung"],
    index=0
)
st.markdown("---")

# 1. Objekt & Investition
st.header("1. Objekt & Investition")
wohnort = st.text_input("Wohnort", "Nürnberg")
baujahr = st.selectbox("Baujahr", ["1925 - 2022", "vor 1925", "ab 2023"])
wohnflaeche_qm = st.number_input("Wohnfläche (qm)", min_value=10, max_value=500, value=80)
stockwerk = st.selectbox("Stockwerk", ["EG","1","2","3","4","5","6","DG"])
zimmeranzahl = st.selectbox("Zimmeranzahl", ["1","1,5","2","2,5","3","3,5","4","4,5","5"], index=4)
energieeffizienz = st.selectbox("Energieeffizienz", ["A+","A","B","C","D","E","F","G","H"], index=2)
oepnv_anbindung = st.selectbox("ÖPNV-Anbindung", ["Sehr gut","Gut","Okay"])
besonderheiten = st.text_input("Besonderheiten", "Balkon, Einbauküche")
st.markdown("---")

# 2. Finanzierung
st.header("2. Finanzierung")
kaufpreis = st.number_input("Kaufpreis (€)", min_value=0, max_value=10_000_000, value=250_000, step=1_000)
garage_stellplatz = st.number_input("Garage/Stellplatz (€)", min_value=0, max_value=50_000, value=0, step=1_000)
invest_bedarf = st.number_input("Zusätzl. Investitionsbedarf (€)", min_value=0, max_value=1_000_000, value=10_000, step=1_000)
eigenkapital = st.number_input("Eigenkapital (€)", min_value=0, max_value=10_000_000, value=80_000, step=1_000)

st.subheader("Kaufnebenkosten (%)")
grunderwerbsteuer = st.number_input("Grunderwerbsteuer %", min_value=0.0, max_value=15.0, value=3.5, step=0.1)
notar = st.number_input("Notar %", min_value=0.0, max_value=10.0, value=1.5, step=0.1)
grundbuch = st.number_input("Grundbuch %", min_value=0.0, max_value=10.0, value=0.5, step=0.1)
makler = st.number_input("Makler %", min_value=0.0, max_value=10.0, value=3.57, step=0.01)

# Darlehenssumme automatisch berechnen
nebenkosten_summe = (kaufpreis + garage_stellplatz) * (grunderwerbsteuer + notar + grundbuch + makler) / 100
gesamtfinanzierung = kaufpreis + garage_stellplatz + invest_bedarf + nebenkosten_summe
darlehen1_summe = gesamtfinanzierung - eigenkapital

st.subheader("Darlehen")
st.info(f"**Automatisch berechnete Darlehenssumme:** {darlehen1_summe:,.2f} €")

zins1 = st.number_input("Zins (%)", min_value=0.0, max_value=10.0, value=3.5, step=0.05)
tilgung1_modus = st.selectbox("Tilgungsmodus", ["Tilgungssatz (%)","Tilgungsbetrag (€ mtl.)","Laufzeit (Jahre)"], index=0)
if tilgung1_modus.startswith("Tilgungssatz"):
    tilgung1 = st.number_input("Tilgung (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.1)
    tilg_eur1, laufzeit1 = None, None
elif tilgung1_modus.startswith("Tilgungsbetrag"):
    tilg_eur1 = st.number_input("Tilgung (€ mtl.)", min_value=0, max_value=50_000, value=350, step=50)
    tilgung1, laufzeit1 = None, None
else:
    laufzeit1 = st.number_input("Laufzeit (Jahre)", min_value=1, max_value=50, value=25, step=1)
    tilgung1, tilg_eur1 = None, None

show_darlehen2 = st.checkbox("Weiteres Darlehen hinzufügen")
if show_darlehen2:
    st.subheader("Darlehen II")
    zins2 = st.number_input("Zins II (%)", min_value=0.0, max_value=10.0, value=0.0, step=0.05)
    tilgung2_modus = st.selectbox("Tilgungsmodus II", ["Tilgungssatz (%)","Tilgungsbetrag (€ mtl.)","Laufzeit (Jahre)"])
    if tilgung2_modus.startswith("Tilgungssatz"):
        tilgung2 = st.number_input("Tilgung II (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.1)
        tilg_eur2, laufzeit2 = None, None
    elif tilgung2_modus.startswith("Tilgungsbetrag"):
        tilg_eur2 = st.number_input("Tilgung II (€ mtl.)", min_value=0, max_value=50_000, value=350, step=50)
        tilgung2, laufzeit2 = None, None
    else:
        laufzeit2 = st.number_input("Laufzeit II (Jahre)", min_value=1, max_value=50, value=25, step=1)
        tilgung2, tilg_eur2 = None, None
else:
    zins2 = tilgung2 = tilg_eur2 = laufzeit2 = tilgung2_modus = None

from immo_core import berechne_darlehen_details
modus_d1 = 'tilgungssatz' if tilgung1_modus.startswith("Tilgungssatz") else 'tilgung_euro' if tilgung1_modus.startswith("Tilgungsbetrag") else 'laufzeit'
d1 = berechne_darlehen_details(
    darlehen1_summe, zins1, tilgung_p=tilgung1, tilgung_euro_mtl=tilg_eur1, laufzeit_jahre=laufzeit1, modus=modus_d1
)
st.markdown(
    f"""
    **Darlehen Übersicht:**
    - Darlehenssumme: **{darlehen1_summe:,.2f} €**
    - Rate: **{d1['monatsrate']:,.2f} €**
    - Laufzeit: **{d1['laufzeit_jahre']:.1f} Jahre**
    - Tilgungssatz: **{d1['tilgung_p_ergebnis']:.2f} %**
    """
)
if show_darlehen2:
    d2 = berechne_darlehen_details(
        0, zins2, tilgung_p=tilgung2, tilgung_euro_mtl=tilg_eur2, laufzeit_jahre=laufzeit2,
        modus=('tilgungssatz' if tilgung2_modus and tilgung2_modus.startswith("Tilgungssatz")
               else 'tilgung_euro' if tilgung2_modus and tilgung2_modus.startswith("Tilgungsbetrag")
               else 'laufzeit')
    )
    st.markdown(
        f"""
        **Darlehen II Übersicht:**
        - Rate: **{d2['monatsrate']:,.2f} €**
        - Laufzeit: **{d2['laufzeit_jahre']:.1f} Jahre**
        - Tilgungssatz: **{d2['tilgung_p_ergebnis']:.2f} %**
        """
    )

st.markdown("---")

# 3. Laufende Posten & Steuer
st.header("3. Laufende Posten & Steuer")
if nutzungsart == "Vermietung":
    kaltmiete_monatlich = st.number_input("Kaltmiete mtl. (€)", min_value=0, max_value=10_000, value=1_000, step=50)
    umlagefaehige_monat = st.number_input("Umlagefähige Kosten (€ mtl.)", min_value=0, max_value=1_000, value=150, step=10)
    nicht_umlagefaehige_pa = st.number_input("Nicht umlagef. Kosten p.a. (€)", min_value=0, max_value=10_000, value=960, step=10)
else:
    kaltmiete_monatlich = 0
    umlagefaehige_monat = 0
    nicht_umlagefaehige_pa = st.number_input("Laufende Kosten p.a. (Hausgeld etc.)", min_value=0, max_value=10_000, value=960, step=10)

steuersatz = st.number_input("Persönl. Steuersatz (%)", min_value=0.0, max_value=100.0, value=42.0, step=0.5)

st.subheader("Persönliche Finanzsituation")
verfuegbares_einkommen = st.number_input("Monatl. verfügbares Einkommen (€)", min_value=0, max_value=100_000, value=2_500, step=100)
st.markdown("---")

# Inputs-Dictionary
inputs = {
    'wohnort': wohnort,
    'baujahr_kategorie': baujahr,
    'wohnflaeche_qm': wohnflaeche_qm,
    'stockwerk': stockwerk,
    'zimmeranzahl': zimmeranzahl,
    'energieeffizienz': energieeffizienz,
    'oepnv_anbindung': oepnv_anbindung,
    'besonderheiten': besonderheiten,
    'kaufpreis': kaufpreis,
    'garage_stellplatz_kosten': garage_stellplatz,
    'invest_bedarf': invest_bedarf,
    'eigenkapital': eigenkapital,
    'nebenkosten_prozente': {
        'grunderwerbsteuer': grunderwerbsteuer,
        'notar': notar,
        'grundbuch': grundbuch,
        'makler': makler
    },
    'nutzungsart': nutzungsart,
    'zins1_prozent': zins1,
    'modus_d1': modus_d1,
    'tilgung1_prozent': tilgung1 if tilgung1_modus.startswith("Tilgungssatz") else None,
    'tilgung1_euro_mtl': tilg_eur1 if tilgung1_modus.startswith("Tilgungsbetrag") else None,
    'laufzeit1_jahre': laufzeit1 if tilgung1_modus.startswith("Laufzeit") else None,
    'darlehen2_summe': 0,
    'zins2_prozent': zins2,
    'modus_d2': ('tilgungssatz' if tilgung2_modus and tilgung2_modus.startswith("Tilgungssatz")
                 else 'tilgung_euro' if tilgung2_modus and tilgung2_modus.startswith("Tilgungsbetrag")
                 else 'laufzeit'),
    'tilgung2_prozent': tilgung2,
    'tilgung2_euro_mtl': tilg_eur2,
    'laufzeit2_jahre': laufzeit2,
    'kaltmiete_monatlich': kaltmiete_monatlich,
    'umlagefaehige_kosten_monatlich': umlagefaehige_monat,
    'nicht_umlagefaehige_kosten_pa': nicht_umlagefaehige_pa,
    'steuersatz': steuersatz,
    'verfuegbares_einkommen_mtl': verfuegbares_einkommen
}

# --- Berechnung und Ergebnisanzeige ---
if st.button("Analyse berechnen"):
    results = immo_core.calculate_analytics(inputs)
    if 'error' in results:
        st.error(results['error'])
    else:
        st.subheader("Ergebnisse")

        # Unterschiedliche Kennzahlen je nach Nutzungsart
        if nutzungsart == "Vermietung":
            all_keys = [
                "Einnahmen p.a. (Kaltmiete)",
                "Umlagefähige Kosten p.a.",
                "Nicht umlagef. Kosten p.a.",
                "Rückzahlung Darlehen p.a.",
                "- Zinsen p.a.",
                "Jährliche Gesamtkosten",
                "= Cashflow vor Steuern p.a.",
                "- AfA p.a.",
                "- Absetzbare Kaufnebenkosten (Jahr 1)",
                "= Steuerlicher Gewinn/Verlust p.a.",
                "+ Steuerersparnis / -last p.a.",
                "= Effektiver Cashflow n. St. p.a.",
                "Gesamt-Cashflow (Ihre persönliche Si)",
                "Ihr monatl. Einkommen (vorher)",
                "- Mtl. Kosten Immobilie",
                "= Neues verfügbares Einkommen"
            ]
        else:  # Eigennutzung
            all_keys = [
                "Laufende Kosten p.a.",
                "Rückzahlung Darlehen p.a.",
                "- Zinsen p.a.",
                "Jährliche Gesamtkosten",
                "Gesamt-Cashflow (Ihre persönliche Si)",
                "Ihr monatl. Einkommen (vorher)",
                "- Mtl. Kosten Immobilie",
                "= Neues verfügbares Einkommen"
            ]

        def get_val(key, col):
            row = next((r for r in results['display_table'] if key in r['kennzahl']), None)
            if row:
                val = row['val1'] if col == 0 else row['val2']
                if isinstance(val, (int, float)):
                    return f"{val:,.2f} €"
                return val
            return ""

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Jahr der Anschaffung (€)")
            for key in all_keys:
                val = get_val(key, 0)
                if val != "":
                    style = "font-weight: bold;" if key.startswith("=") or "+ Steuerersparnis" in key else ""
                    st.markdown(f"<div style='{style}'>{key}: {val}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("#### Laufende Jahre (€)")
            for key in all_keys:
                val = get_val(key, 1)
                if val != "":
                    style = "font-weight: bold;" if key.startswith("=") or "+ Steuerersparnis" in key else ""
                    st.markdown(f"<div style='{style}'>{key}: {val}</div>", unsafe_allow_html=True)
        st.markdown("---")

        # --- Finanzierungsstruktur-Grafik (kompakt) ---
        ek = eigenkapital
        fk = gesamtfinanzierung - eigenkapital
        labels = ['Eigenkapital', 'Darlehen']
        sizes = [ek, fk]
        colors = ['#4e79a7', '#f28e2b']
        fig, ax = plt.subplots(figsize=(3.5, 3.5))  # Kompakte Größe [3.5 Zoll x 3.5 Zoll]
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=colors, autopct='%1.1f%%',
            startangle=90, counterclock=False, textprops={'fontsize': 11}
        )
        ax.axis('equal')
        ax.set_title('Finanzierungsstruktur', fontsize=13)
        st.pyplot(fig)
        st.markdown("---")

        # --- PDF Export ---
        st.subheader("Bericht als PDF exportieren")
        if st.button("PDF-Bericht erstellen"):
            pdf_bytes = pdf_generator.create_bank_report_streamlit(results, inputs)
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="Immo_Bericht.pdf">PDF herunterladen</a>'
            st.markdown(href, unsafe_allow_html=True)
