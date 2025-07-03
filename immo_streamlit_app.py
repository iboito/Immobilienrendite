import streamlit as st
from pathlib import Path
from PIL import Image
import immo_core
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Immobilien-Analyse", page_icon="🏠", layout="wide")

# --- CHECKLISTE: GANZ OBEN DEFINIEREN! ---
checklist_items = [
    "Grundbuchauszug",
    "Flurkarte",
    "Energieausweis",
    "Teilungserklärung & Gemeinschaftsordnung",
    "Protokolle der letzten 3–5 Eigentümerversammlungen",
    "Jahresabrechnung & Wirtschaftsplan",
    "Höhe der Instandhaltungsrücklage",
    "Exposé & Grundrisse",
    "WEG-Protokolle: Hinweise auf Streit, Sanierungen, Rückstände"
]

# --- Nutzungsart-Auswahl und ggf. Erweiterung der Checkliste ---
nutzungsart = st.selectbox("Nutzungsart wählen", ["Vermietung", "Eigennutzung"])
if nutzungsart == "Vermietung" and "Bei vermieteter Wohnung: Mietvertrag" not in checklist_items:
    checklist_items.append("Bei vermieteter Wohnung: Mietvertrag")

# --- Eingaben ---
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

# --- EINZIGER Checklistenblock! (NUR HIER, nirgendwo sonst!) ---
st.header("4. Checkliste: Wichtige Dokumente für den Immobilienkauf")
if 'checklist_status' not in st.session_state:
    st.session_state['checklist_status'] = {}
for item in checklist_items:
    st.session_state['checklist_status'][item] = st.checkbox(item, key=f"check_{item}", value=st.session_state['checklist_status'].get(item, False))

# --- Alle weiteren Variablen und Inputs ---
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
    'verfuegbares_einkommen_mtl': verfuegbares_einkommen,
    'checklist_status': st.session_state['checklist_status']
}

if 'results' not in st.session_state:
    st.session_state['results'] = None
if 'pdf_bytes' not in st.session_state:
    st.session_state['pdf_bytes'] = None

if st.button("Analyse berechnen"):
    results = immo_core.calculate_analytics(inputs)
    if 'error' in results:
        st.session_state['results'] = None
        st.error(results['error'])
    else:
        st.session_state['results'] = results

results = st.session_state['results']

if results:
    st.subheader("Ergebnisse")

    # ... Ergebnisanzeige, wie gehabt ...

    # Checkliste-Status NUR anzeigen (KEINE Checkboxen mehr!)
    st.markdown("---")
    st.subheader("Checkliste Status (nur Anzeige, keine Checkboxen):")
    for item in checklist_items:
        checked = st.session_state['checklist_status'][item]
        box = "☑" if checked else "☐"
        st.write(f"{box} {item}")

    st.markdown("---")
    st.subheader("Bericht als PDF exportieren")
    if st.button("PDF-Bericht erstellen"):
        pdf_bytes = create_pdf_report(results, inputs, checklist_items)
        st.session_state['pdf_bytes'] = pdf_bytes
        st.success("PDF wurde erstellt. Klicke unten zum Herunterladen:")
    if st.session_state['pdf_bytes']:
        st.download_button(
            label="PDF herunterladen",
            data=st.session_state['pdf_bytes'],
            file_name="Immo_Bericht.pdf",
            mime="application/pdf"
        )
