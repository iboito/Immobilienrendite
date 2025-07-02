# immo_streamlit_app.py

import streamlit as st
from pathlib import Path
from PIL import Image
import immo_core
import pdf_generator

# Seite konfigurieren
st.set_page_config(
    page_title="Immobilien-Analyse",
    page_icon="🏠",
    layout="wide"
)

# Überschrift und optionales Icon
try:
    icon = Image.open(Path(__file__).with_name("10751558.png")).resize((64, 64))
    st.image(icon)
except FileNotFoundError:
    pass
st.title("🏠 Immobilien-Analyse-Tool (Streamlit Edition)")

# Abschnitt: Objekt & Investition
st.header("1. Objekt & Investition")
wohnort            = st.text_input("Wohnort", "Nürnberg")
baujahr            = st.selectbox("Baujahr", ["1925 - 2022", "vor 1925", "ab 2023"])
wohnflaeche_qm     = st.number_input("Wohnfläche (qm)", min_value=10, max_value=500, value=80)
stockwerk          = st.selectbox("Stockwerk", ["EG","1","2","3","4","5","6","DG"])
zimmeranzahl       = st.selectbox("Zimmeranzahl", ["1","1,5","2","2,5","3","3,5","4","4,5","5"], index=4)
energieeffizienz   = st.selectbox("Energieeffizienz", ["A+","A","B","C","D","E","F","G","H"], index=2)
oepnv_anbindung    = st.selectbox("ÖPNV-Anbindung", ["Sehr gut","Gut","Okay"])
besonderheiten     = st.text_input("Besonderheiten", "Balkon, Einbauküche")

st.markdown("---")

# Abschnitt: Finanzierung
st.header("2. Finanzierung")
kaufpreis          = st.number_input("Kaufpreis (€)", min_value=0, max_value=10_000_000, value=250_000, step=1_000)
garage_stellplatz  = st.number_input("Garage/Stellplatz (€)", min_value=0, max_value=50_000, value=0, step=1_000)
invest_bedarf      = st.number_input("Investitionsbedarf (€)", min_value=0, max_value=1_000_000, value=10_000, step=1_000)
eigenkapital       = st.number_input("Eigenkapital (€)", min_value=0, max_value=10_000_000, value=80_000, step=1_000)

st.subheader("Kaufnebenkosten (%)")
grunderwerbsteuer  = st.number_input("Grunderwerbsteuer %", min_value=0.0, max_value=15.0, value=3.5, step=0.1)
notar              = st.number_input("Notar %",             min_value=0.0, max_value=10.0, value=1.5, step=0.1)
grundbuch          = st.number_input("Grundbuch %",         min_value=0.0, max_value=10.0, value=0.5, step=0.1)
makler             = st.number_input("Makler %",            min_value=0.0, max_value=10.0, value=3.57, step=0.01)

st.subheader("Darlehen")
zins1              = st.number_input("Zins I (%)",          min_value=0.0, max_value=10.0, value=3.5, step=0.05)
tilgung1_modus     = st.selectbox("Tilgungsmodus I", ["Tilgungssatz (%)","Tilgungsbetrag (€ mtl.)","Laufzeit (Jahre)"])
if tilgung1_modus == "Tilgungssatz (%)":
    tilgung1       = st.number_input("Tilgung I (%)",       min_value=0.0, max_value=10.0, value=2.0, step=0.1)
    tilg_eur1      = None; laufzeit1 = None
elif tilgung1_modus == "Tilgungsbetrag (€ mtl.)":
    tilg_eur1      = st.number_input("Tilgung I (€ mtl.)",   min_value=0, max_value=50_000, value=350, step=50)
    tilgung1       = None; laufzeit1 = None
else:
    laufzeit1      = st.number_input("Laufzeit I (Jahre)",   min_value=1, max_value=50, value=25, step=1)
    tilgung1       = None; tilg_eur1  = None

# Finanzierung Darlehen II (optional)
show_darlehen2     = st.checkbox("Weiteres Darlehen hinzufügen")
zins2              = st.number_input("Zins II (%)",         min_value=0.0, max_value=10.0, value=0.0, step=0.05, disabled=not show_darlehen2)
tilgung2_modus     = st.selectbox("Tilgungsmodus II", ["Tilgungssatz (%)","Tilgungsbetrag (€ mtl.)","Laufzeit (Jahre)"], disabled=not show_darlehen2)
if show_darlehen2:
    if tilgung2_modus == "Tilgungssatz (%)":
        tilgung2   = st.number_input("Tilgung II (%)",       min_value=0.0, max_value=10.0, value=2.0, step=0.1)
        tilg_eur2  = None; laufzeit2 = None
    elif tilgung2_modus == "Tilgungsbetrag (€ mtl.)":
        tilg_eur2  = st.number_input("Tilgung II (€ mtl.)",   min_value=0, max_value=50_000, value=350, step=50)
        tilgung2   = None; laufzeit2 = None
    else:
        laufzeit2  = st.number_input("Laufzeit II (Jahre)",   min_value=1, max_value=50, value=25, step=1)
        tilgung2   = None; tilg_eur2  = None
else:
    tilgung2 = tilg_eur2 = laufzeit2 = None

st.markdown("---")

# Abschnitt: Laufende Posten & Steuer
st.header("3. Laufende Posten & Steuer")
kaltmiete_monatlich    = st.number_input("Kaltmiete mtl. (€)",         min_value=0, max_value=10_000, value=1_000, step=50)
umlagefaehige_monat    = st.number_input("Umlagefähige Kosten mtl. (€)", min_value=0, max_value=1_000, value=150, step=10)
nicht_umlagefaehige_pa = st.number_input("Nicht uml.agef. Kosten p.a. (€)", min_value=0, max_value=10_000, value=960, step=10)
steuersatz             = st.number_input("Persönl. Steuersatz (%)",       min_value=0.0, max_value=100.0, value=42.0, step=0.5)

st.subheader("Persönliche Finanzsituation")
verfuegbares_einkommen = st.number_input("Monatl. verfügbares Einkommen (€)", min_value=0, max_value=100_000, value=2_500, step=100)

st.markdown("---")

# Ausführen-Button
if st.button("Analyse berechnen"):
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
        'modus_d1': 'tilgungssatz' if tilgung1_modus.startswith("Tilgungssatz") else 'tilgung_euro' if tilgung1_modus.startswith("Tilgungsbetrag") else 'laufzeit',
        'tilgung1_prozent': tilgung1,
        'tilgung1_euro_mtl': tilg_eur1,
        'laufzeit1_jahre': laufzeit1,
        'darlehen2_summe': 0,
        'zins2_prozent': zins2,
        'modus_d2': 'tilgungssatz' if tilgung2_modus.startswith("Tilgungssatz") else 'tilgung_euro' if tilgung2_modus.startswith("Tilgungsbetrag") else 'laufzeit',
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
        st.stop()

    # Ergebnistabelle
    st.subheader("Ergebnisse")
    df = {
        row['kennzahl']: [row['val1'], row['val2']]
        for row in results['display_table']
        if row['val1'] is not None or row['val2'] is not None
    }
    st.dataframe(df, use_container_width=True)

    # KPIs
    st.subheader("Kennzahlen (KPIs)")
    cols = st.columns(len(results['kpi_table']))
    for col, kpi in zip(cols, results['kpi_table']):
        with col:
            st.metric(kpi['Kennzahl'], kpi['Wert'])

    # Grafiken
    st.subheader("Grafiken")
    pie_col, bar_col = st.columns(2)
    with pie_col:
        labels = list(results['pie_data'].keys())
        sizes  = list(results['pie_data'].values())
        st.pyplot(immo_core.plt_pie(labels, sizes, ret_fig=True))
    with bar_col:
        st.pyplot(immo_core.plt_bar(results['bar_data'], ret_fig=True))

    # PDF-Export
    if st.button("PDF-Bericht erstellen"):
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_generator.create_bank_report(
                {**results, 'inputs': inputs, 'figures': {'pie': immo_core.plt_pie(labels, sizes, ret_fig=True), 'bar': immo_core.plt_bar(results['bar_data'], ret_fig=True)}},
                tmp.name
            )
            st.success("PDF generiert!")
            st.download_button("PDF herunterladen", data=open(tmp.name,"rb").read(), file_name="Immobilienanalyse.pdf", mime="application/pdf")
