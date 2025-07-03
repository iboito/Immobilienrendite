import streamlit as st
from pathlib import Path
from PIL import Image
import immo_core
import pdf_generator
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

# 1. Objekt
st.header("1. Objekt")
wohnort            = st.text_input("Wohnort", "Nürnberg")
baujahr            = st.selectbox("Baujahr", ["1925 - 2022", "vor 1925", "ab 2023"])
wohnflaeche_qm     = st.number_input("Wohnfläche (qm)", min_value=10, max_value=500, value=80)
stockwerk          = st.selectbox("Stockwerk", ["EG","1","2","3","4","5","6","DG"])
zimmeranzahl       = st.selectbox("Zimmeranzahl", ["1","1,5","2","2,5","3","3,5","4","4,5","5"], index=4)
energieeffizienz   = st.selectbox("Energieeffizienz", ["A+","A","B","C","D","E","F","G","H"], index=2)
oepnv_anbindung    = st.selectbox("ÖPNV-Anbindung", ["Sehr gut","Gut","Okay"])
besonderheiten     = st.text_input("Besonderheiten", "Balkon, Einbauküche")

st.markdown("---")

# 2. Finanzierung
st.header("2. Finanzierung")
kaufpreis             = st.number_input("Kaufpreis (€)", min_value=0, max_value=10_000_000, value=250_000, step=1_000)
garage_stellplatz     = st.number_input("Garage/Stellplatz (€)", min_value=0, max_value=50_000, value=0, step=1_000)
invest_bedarf         = st.number_input("Zusätzl. Investitionsbedarf (€)", min_value=0, max_value=1_000_000, value=10_000, step=1_000)
eigenkapital          = st.number_input("Eigenkapital (€)", min_value=0, max_value=10_000_000, value=80_000, step=1_000)

st.subheader("Kaufnebenkosten (%)")
grunderwerbsteuer     = st.number_input("Grunderwerbsteuer %", min_value=0.0, max_value=15.0, value=3.5, step=0.1)
notar                 = st.number_input("Notar %", min_value=0.0, max_value=10.0, value=1.5, step=0.1)
grundbuch             = st.number_input("Grundbuch %", min_value=0.0, max_value=10.0, value=0.5, step=0.1)
makler                = st.number_input("Makler %", min_value=0.0, max_value=10.0, value=3.57, step=0.01)

# Darlehenssumme automatisch berechnen
nebenkosten_summe = (kaufpreis + garage_stellplatz) * (grunderwerbsteuer + notar + grundbuch + makler) / 100
darlehen1_summe = kaufpreis + garage_stellplatz + invest_bedarf + nebenkosten_summe - eigenkapital

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

# LIVE Darlehensdetails wie in der GUI
from immo_core import berechne_darlehen_details
modus_d1 = 'tilgungssatz' if tilgung1_modus.startswith("Tilgungssatz") else 'tilgung_euro' if tilgung1_modus.startswith("Tilgungsbetrag") else 'laufzeit'
d1 = berechne_darlehen_details(
    darlehen1_summe, zins1,
    tilgung_p=tilgung1,
    tilgung_euro_mtl=tilg_eur1,
    laufzeit_jahre=laufzeit1,
    modus=modus_d1
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

# Checkbox für weiteres Darlehen nach dem ersten Darlehen
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

    d2 = berechne_darlehen_details(
        0, zins2,
        tilgung_p=tilgung2,
        tilgung_euro_mtl=tilg_eur2,
        laufzeit_jahre=laufzeit2,
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
else:
    zins2 = tilgung2 = tilg_eur2 = laufzeit2 = tilgung2_modus = None

st.markdown("---")

# 3. Laufende Posten & Steuer
st.header("3. Laufende Posten & Steuer")
kaltmiete_monatlich    = st.number_input("Kaltmiete mtl. (€)", min_value=0, max_value=10_000, value=1_000, step=50)
umlagefaehige_monat    = st.number_input("Umlagefähige Kosten (€ mtl.)", min_value=0, max_value=1_000, value=150, step=10)
nicht_umlagefaehige_pa = st.number_input("Nicht umlagef. Kosten p.a. (€)", min_value=0, max_value=10_000, value=960, step=10)
steuersatz             = st.number_input("Persönl. Steuersatz (%)", min_value=0.0, max_value=100.0, value=42.0, step=0.5)

st.subheader("Persönliche Finanzsituation")
verfuegbares_einkommen = st.number_input("Monatl. verfügbares Einkommen (€)", min_value=0, max_value=100_000, value=2_500, step=100)

st.markdown("---")

st.subheader("Ergebnisse")
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
    'nutzungsart': 'Vermietung',
    'zins1_prozent': zins1,
    'modus_d1': modus_d1,
    'tilgung1_prozent': tilgung1,
    'tilgung1_euro_mtl': tilg_eur1,
    'laufzeit1_jahre': laufzeit1,
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

results = immo_core.calculate_analytics(inputs)

if 'error' in results:
    st.error(results['error'])
else:
    df = {r['kennzahl']: [r['val1'], r['val2']] for r in results['display_table']}
    st.dataframe(df, use_container_width=True)

    st.subheader("Kennzahlen (KPIs)")
    cols = st.columns(len(results['kpi_table']))
    for col, k in zip(cols, results['kpi_table']):
        with col:
            st.metric(k['Kennzahl'], k['Wert'])

    st.subheader("Grafiken")
    c1, c2 = st.columns(2)

    # Dynamische Pie-Labels und Werte
    pie_labels = []
    pie_values = []
    if show_darlehen2 and zins2 and zins2 > 0:
        pie_labels = ["Darlehen I", "Darlehen II", "Eigenkapital"]
        # Hier ggf. echte Summe für Darlehen II eintragen!
        pie_values = [darlehen1_summe, 0, eigenkapital]
    else:
        pie_labels = ["Darlehen", "Eigenkapital"]
        pie_values = [darlehen1_summe, eigenkapital]

    with c1:
        fig, ax = plt.subplots()
        ax.pie(pie_values, labels=pie_labels, autopct='%1.1f%%', startangle=90)
        ax.set_title("Finanzierungsstruktur")
        st.pyplot(fig)
    with c2:
        st.pyplot(immo_core.plt_bar(results['bar_data'], ret_fig=True))

    if st.button("📄 PDF-Bericht erstellen"):
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_generator.create_bank_report(
                {**results, 'inputs': inputs,
                 'figures': {
                     'pie': fig,
                     'bar': immo_core.plt_bar(results['bar_data'], ret_fig=True)
                 }},
                tmp.name
            )
            st.success("PDF generiert!")
            st.download_button(
                "PDF herunterladen",
                data=open(tmp.name, "rb").read(),
                file_name="Immobilienanalyse.pdf",
                mime="application/pdf"
            )
