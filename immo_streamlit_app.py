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

# ... Ihre bisherigen Eingabeabschnitte (wie gehabt) ...

# Nach allen Eingaben:
results = immo_core.calculate_analytics(inputs)

if 'error' in results:
    st.error(results['error'])
else:
    st.subheader("Ergebnisse")

    # Liste aller gewünschten Kennzahlen wie in Ihrer GUI
    all_keys = [
        "Einnahmen p.a. (Kaltmiete)",
        "Nicht umlagef. Kosten p.a.",
        "Rückzahlung Darlehen p.a.",
        "= Cashflow vor Steuern p.a.",
        "- Zinsen p.a.",
        "- AfA p.a.",
        "- Absetzbare Kaufnebenkosten (Jahr 1)",
        "= Steuerlicher Gewinn/Verlust p.a.",
        "+ Steuerersparnis / -last p.a.",
        "= Effektiver Cashflow n. St. p.a.",
        "Gesamt-Cashflow (Ihre persönliche Si)",
        "Ihr monatl. Einkommen (vorher)",
        "+/- Mtl. Cashflow Immobilie",
        "= Neues verfügbares Einkommen"
    ]

    # Hilfsfunktion für Werte aus display_table
    def get_val(key, col):
        row = next((r for r in results['display_table'] if key in r['kennzahl']), None)
        if row:
            val = row['val1'] if col == 0 else row['val2']
            if isinstance(val, (int, float)):
                return f"{val:,.2f} €"
            return val
        return ""

    # Zwei Spalten für Anschaffungsjahr und Laufende Jahre
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

    # KPIs
    st.subheader("Kennzahlen (KPIs)")
    cols = st.columns(len(results['kpi_table']))
    for col, k in zip(cols, results['kpi_table']):
        with col:
            st.metric(k['Kennzahl'], k['Wert'])

    # Grafiken
    st.subheader("Grafiken")
    c1, c2 = st.columns(2)
    with c1:
        pie_labels = ["Darlehen", "Eigenkapital"]
        pie_values = [darlehen1_summe, eigenkapital]
        fig, ax = plt.subplots()
        ax.pie(pie_values, labels=pie_labels, autopct='%1.1f%%', startangle=90)
        ax.set_title("Finanzierungsstruktur")
        st.pyplot(fig)
    with c2:
        st.pyplot(immo_core.plt_bar(results['bar_data'], ret_fig=True))

    # PDF-Export wie gehabt
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
