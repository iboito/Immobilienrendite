# immo_streamlit_app.py
"""
Streamlit-Frontend für das Immobilien-Analyse-Tool
Voraussetzung: immo_core.py, pdf_generator.py liegen im selben Ordner.
"""

import streamlit as st
from pathlib import Path
import immo_core
import pdf_generator
from PIL import Image

##############################################################################
# 0) Seiten-Konfiguration & Logo
##############################################################################
st.set_page_config(page_title="Immobilien-Analyse",
                   page_icon="🏠",
                   layout="wide")

st.image(Image.open(Path(__file__).with_name("house_icon.png")).resize((96, 96)))
st.title("🏠 Immobilien-Analyse-Tool (Streamlit Edition)")

##############################################################################
# 1) Eingabespalten anlegen
##############################################################################
col1, col2, col3 = st.columns(3)

with col1:
    st.header("Objekt & Investition")
    wohnort               = st.text_input("Wohnort", "Nürnberg")
    baujahr_kategorie     = st.selectbox("Baujahr", ["1925 - 2022", "vor 1925", "ab 2023"])
    wohnflaeche_qm        = st.number_input("Wohnfläche (qm)", 10, 500, 80)
    stockwerk             = st.selectbox("Stockwerk", ["EG","1","2","3","4","5","6","DG"])
    zimmeranzahl          = st.selectbox("Zimmeranzahl", ["1","1,5","2","2,5","3","3,5","4","4,5","5"], index=4)
    energieeffizienz      = st.selectbox("Energieeffizienz", list("ABCDEFGH"), index=2)
    oepnv_anbindung       = st.selectbox("ÖPNV-Anbindung", ["Sehr gut","Gut","Okay"])
    besonderheiten        = st.text_input("Besonderheiten", "Balkon, Einbauküche")

with col2:
    st.header("Finanzielle Eckdaten")
    kaufpreis             = st.number_input("Kaufpreis (€)", 0, 10_000_000, 250_000, step=1_000)
    garage_stellplatz     = st.number_input("Garage / Stellplatz (€)", 0, 50_000, 0, step=1_000)
    invest_bedarf         = st.number_input("Zusätzl. Investitionsbedarf (€)", 0, 1_000_000, 10_000, step=1_000)
    eigenkapital          = st.number_input("Eigenkapital (€)", 0, 10_000_000, 80_000, step=1_000)

    st.subheader("Kaufnebenkosten (%)")
    grunderwerbsteuer = st.number_input("Grunderwerbsteuer %", 0.0, 15.0, 3.5, step=0.1)
    notar             = st.number_input("Notar %",             0.0, 10.0, 1.5, step=0.1)
    grundbuch         = st.number_input("Grundbuch %",         0.0, 10.0, 0.5, step=0.1)
    makler            = st.number_input("Makler %",            0.0, 10.0, 3.57, step=0.01)

with col3:
    st.header("Persönliche Annahmen")
    nutzungsart   = st.radio("Nutzungsart", ["Kapitalanlage (Vermietung)", "Eigennutzung"],
                              horizontal=False, index=0)
    verfuegbare_monatsrate = st.number_input("Monatl. verfügbares Einkommen (€)", 0, 100_000, 2_500, step=100)

    st.subheader("Darlehen I")
    zins1  = st.number_input("Zins %", 0.0, 10.0, 3.5, step=0.05, key="zins1")
    tilgung1_modus = st.selectbox("Tilgungsmodus", ["Tilgungssatz (%)", "Tilgungsbetrag (€ mtl.)", "Laufzeit (Jahre)"], index=0, key="mod1")
    if tilgung1_modus == "Tilgungssatz (%)":
        tilgung1 = st.number_input("Tilgung % p.a.", 0.0, 10.0, 2.0, step=0.1)
        tilg_eur1 = None; laufzeit1 = None
    elif tilgung1_modus == "Tilgungsbetrag (€ mtl.)":
        tilg_eur1 = st.number_input("Tilgung (€ mtl.)", 0, 50_000, 350, step=50)
        tilgung1 = None; laufzeit1 = None
    else:
        laufzeit1 = st.number_input("Laufzeit (Jahre)", 1, 50, 25, step=1)
        tilgung1 = None; tilg_eur1 = None

##############################################################################
# 2) Berechnen-Button
##############################################################################
if st.button("Analyse berechnen"):
    nebenkosten_prozente = {"grunderwerbsteuer": grunderwerbsteuer,
                            "notar": notar,
                            "grundbuch": grundbuch,
                            "makler": makler}

    inputs = {
        "wohnort": wohnort, "baujahr_kategorie": baujahr_kategorie,
        "wohnflaeche_qm": wohnflaeche_qm, "stockwerk": stockwerk,
        "zimmeranzahl": zimmeranzahl, "energieeffizienz": energieeffizienz,
        "oepnv_anbindung": oepnv_anbindung, "besonderheiten": besonderheiten,
        "kaufpreis": kaufpreis, "garage_stellplatz_kosten": garage_stellplatz,
        "invest_bedarf": invest_bedarf, "eigenkapital": eigenkapital,
        "nebenkosten_prozente": nebenkosten_prozente,
        "nutzungsart": "Vermietung" if nutzungsart.startswith("Kapital") else "Eigennutzung",
        "verfuegbares_einkommen_mtl": verfuegbare_monatsrate,
        "darlehen1_summe": 0,  # wird von core gesetzt
        "zins1_prozent": zins1,
        "modus_d1": "tilgungssatz" if tilgung1_modus.startswith("Tilgungssatz") else
                    "tilgung_euro" if tilgung1_modus.startswith("Tilgungsbetrag") else "laufzeit",
        "tilgung1_prozent": tilgung1,
        "tilgung1_euro_mtl": tilg_eur1,
        "laufzeit1_jahre": laufzeit1,
        # Darlehen II deaktiviert
        "darlehen2_summe": 0, "zins2_prozent": 0,
    }

    results = immo_core.calculate_analytics(inputs)
    if "error" in results:
        st.error(results["error"])
        st.stop()

    ### 2a) Ergebnistabelle anzeigen
    st.subheader("🏁 Ergebnisse")
    table_data = results["display_table"]
    st.dataframe(
        {r['kennzahl']: [r['val1'], r['val2']] for r in table_data if not r['kennzahl'].startswith("---")},
        use_container_width=True
    )

    ### 2b) Kennzahlen
    st.subheader("Kennzahlen (KPIs)")
    kpi_cols = st.columns(len(results["kpi_table"]))
    for col, row in zip(kpi_cols, results["kpi_table"]):
        with col:
            st.metric(row["Kennzahl"], row["Wert"])

    ### 2c) Grafiken
    st.subheader("Grafiken")
    col_pie, col_bar = st.columns(2)
    with col_pie:
        labels = list(results["pie_data"].keys())
        sizes  = list(results["pie_data"].values())
        st.pyplot(immo_core.plt_pie(labels, sizes))  # kleine Hilfsfunktion
    with col_bar:
        data = results["bar_data"]
        st.pyplot(immo_core.plt_bar(data))

    ### 2d) PDF-Export
    if st.button("📄 PDF-Bericht erstellen"):
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_generator.create_bank_report({**results, "inputs": inputs,
                                              "figures": {"pie": immo_core.plt_pie(labels, sizes, ret_fig=True),
                                                          "bar": immo_core.plt_bar(data, ret_fig=True)}},
                                             tmp.name)
            st.success("PDF generiert!")
            st.download_button("PDF herunterladen", data=open(tmp.name, "rb").read(),
                               file_name="Immobilienanalyse.pdf", mime="application/pdf")
