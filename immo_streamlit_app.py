import streamlit as st
from pathlib import Path
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

st.set_page_config(page_title="Immobilien-Analyse", page_icon="🏠", layout="wide")

checklist_items = [
    "Grundbuchauszug",
    "Energieausweis", 
    "Teilungserklärung",
    "Hausverwaltungsunterlagen",
    "Mietverträge (bei Vermietung)",
    "Wirtschaftsplan",
    "Protokolle Eigentümerversammlungen",
    "Baugenehmigung",
    "Versicherungsunterlagen",
    "Finanzierungsbestätigung"
]

def format_eur(val):
    try:
        f = float(str(val).replace(",", "."))
        return f"{f:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(val)

def format_percent(val):
    try:
        f = float(val)
        return f"{f:.2f} %"
    except Exception:
        return str(val)

def is_number(val):
    try:
        float(str(val).replace(",", "."))
        return True
    except:
        return False

def berechne_darlehen_details(summe, zins, tilgung_p=None, tilgung_euro_mtl=None, laufzeit_jahre=None, modus='tilgungssatz'):
    if modus == 'tilgungssatz' and tilgung_p:
        monatsrate = summe * (zins + tilgung_p) / 100 / 12
        laufzeit = summe / (summe * tilgung_p / 100) if tilgung_p > 0 else 0
        return {
            'monatsrate': monatsrate,
            'laufzeit_jahre': laufzeit,
            'tilgung_p_ergebnis': tilgung_p
        }
    elif modus == 'tilgung_euro' and tilgung_euro_mtl:
        zins_mtl = summe * zins / 100 / 12
        tilgung_mtl = tilgung_euro_mtl - zins_mtl
        laufzeit = summe / (tilgung_mtl * 12) if tilgung_mtl > 0 else 0
        tilgung_p_ergebnis = (tilgung_mtl * 12 / summe * 100) if summe > 0 else 0
        return {
            'monatsrate': tilgung_euro_mtl,
            'laufzeit_jahre': laufzeit,
            'tilgung_p_ergebnis': tilgung_p_ergebnis
        }
    elif modus == 'laufzeit' and laufzeit_jahre:
        tilgung_mtl = summe / (laufzeit_jahre * 12)
        zins_mtl = summe * zins / 100 / 12
        monatsrate = tilgung_mtl + zins_mtl
        tilgung_p_ergebnis = (tilgung_mtl * 12 / summe * 100) if summe > 0 else 0
        return {
            'monatsrate': monatsrate,
            'laufzeit_jahre': laufzeit_jahre,
            'tilgung_p_ergebnis': tilgung_p_ergebnis
        }
    else:
        return {'monatsrate': 0, 'laufzeit_jahre': 0, 'tilgung_p_ergebnis': 0}

def calculate_analytics(inputs):
    kaufpreis = inputs.get('kaufpreis', 0)
    garage_stellplatz = inputs.get('garage_stellplatz_kosten', 0)
    invest_bedarf = inputs.get('invest_bedarf', 0)
    nebenkosten_prozente = inputs.get('nebenkosten_prozente', {})
    nebenkosten_summe = (kaufpreis + garage_stellplatz) * sum(nebenkosten_prozente.values()) / 100
    gesamtinvestition = kaufpreis + garage_stellplatz + invest_bedarf + nebenkosten_summe
    eigenkapital = inputs.get('eigenkapital', 0)
    darlehen_summe = gesamtinvestition - eigenkapital
    
    d1 = berechne_darlehen_details(
        darlehen_summe,
        inputs.get('zins1_prozent', 0),
        tilgung_p=inputs.get('tilgung1_prozent'),
        tilgung_euro_mtl=inputs.get('tilgung1_euro_mtl'),
        laufzeit_jahre=inputs.get('laufzeit1_jahre'),
        modus=inputs.get('modus_d1', 'tilgungssatz')
    )
    
    kaltmiete_jahr = inputs.get('kaltmiete_monatlich', 0) * 12
    umlagefaehige_jahr = inputs.get('umlagefaehige_kosten_monatlich', 0) * 12
    nicht_umlagefaehige_jahr = inputs.get('nicht_umlagefaehige_kosten_pa', 0)
    
    zinsen_jahr = darlehen_summe * inputs.get('zins1_prozent', 0) / 100
    darlehen_rueckzahlung_jahr = d1['monatsrate'] * 12
    
    afa_jahr = kaufpreis * 0.8 * 0.02
    
    verfuegbares_einkommen_mtl = inputs.get('verfuegbares_einkommen_mtl', 0)
    
    if inputs.get('nutzungsart') == 'Vermietung':
        steuerlicher_gewinn = kaltmiete_jahr - nicht_umlagefaehige_jahr - zinsen_jahr - afa_jahr
        steuerlicher_gewinn_jahr1 = steuerlicher_gewinn - nebenkosten_summe
        steuerersparnis_jahr1 = steuerlicher_gewinn_jahr1 * inputs.get('steuersatz', 0) / 100
        steuerersparnis_laufend = steuerlicher_gewinn * inputs.get('steuersatz', 0) / 100
        
        cashflow_vor_steuer = kaltmiete_jahr + umlagefaehige_jahr - nicht_umlagefaehige_jahr - darlehen_rueckzahlung_jahr
        cashflow_nach_steuer_jahr1 = cashflow_vor_steuer + steuerersparnis_jahr1
        cashflow_nach_steuer_laufend = cashflow_vor_steuer + steuerersparnis_laufend
        
        neues_verfuegbares_einkommen_jahr1 = verfuegbares_einkommen_mtl + (cashflow_nach_steuer_jahr1 / 12)
        neues_verfuegbares_einkommen_laufend = verfuegbares_einkommen_mtl + (cashflow_nach_steuer_laufend / 12)
        
        display_table = [
            {'kennzahl': 'Einnahmen p.a. (Kaltmiete)', 'val1': kaltmiete_jahr, 'val2': kaltmiete_jahr},
            {'kennzahl': 'Umlagefähige Kosten p.a.', 'val1': umlagefaehige_jahr, 'val2': umlagefaehige_jahr},
            {'kennzahl': 'Nicht umlagef. Kosten p.a.', 'val1': -nicht_umlagefaehige_jahr, 'val2': -nicht_umlagefaehige_jahr},
            {'kennzahl': 'Rückzahlung Darlehen p.a.', 'val1': -darlehen_rueckzahlung_jahr, 'val2': -darlehen_rueckzahlung_jahr},
            {'kennzahl': '- Zinsen p.a.', 'val1': zinsen_jahr, 'val2': zinsen_jahr},
            {'kennzahl': 'Jährliche Gesamtkosten', 'val1': -(nicht_umlagefaehige_jahr + darlehen_rueckzahlung_jahr), 'val2': -(nicht_umlagefaehige_jahr + darlehen_rueckzahlung_jahr)},
            {'kennzahl': '= Cashflow vor Steuern p.a.', 'val1': cashflow_vor_steuer, 'val2': cashflow_vor_steuer},
            {'kennzahl': '- AfA p.a.', 'val1': -afa_jahr, 'val2': -afa_jahr},
            {'kennzahl': '- Absetzbare Kaufnebenkosten (Jahr 1)', 'val1': -nebenkosten_summe, 'val2': 0},
            {'kennzahl': '= Steuerlicher Gewinn/Verlust p.a.', 'val1': steuerlicher_gewinn_jahr1, 'val2': steuerlicher_gewinn},
            {'kennzahl': '+ Steuerersparnis / -last p.a.', 'val1': steuerersparnis_jahr1, 'val2': steuerersparnis_laufend},
            {'kennzahl': '= Effektiver Cashflow n. St. p.a.', 'val1': cashflow_nach_steuer_jahr1, 'val2': cashflow_nach_steuer_laufend},
            {'kennzahl': 'Ihr monatl. Einkommen (vorher)', 'val1': verfuegbares_einkommen_mtl, 'val2': verfuegbares_einkommen_mtl},
            {'kennzahl': '+/- Mtl. Cashflow Immobilie', 'val1': cashflow_nach_steuer_jahr1 / 12, 'val2': cashflow_nach_steuer_laufend / 12},
            {'kennzahl': '= Neues verfügbares Einkommen', 'val1': neues_verfuegbares_einkommen_jahr1, 'val2': neues_verfuegbares_einkommen_laufend}
        ]
        
        bruttomietrendite = (kaltmiete_jahr / gesamtinvestition * 100) if gesamtinvestition > 0 else 0
        eigenkapitalrendite = (cashflow_nach_steuer_laufend / eigenkapital * 100) if eigenkapital > 0 else 0
        finanzkennzahlen = {
            'Bruttomietrendite': bruttomietrendite,
            'Eigenkapitalrendite': eigenkapitalrendite
        }
    else:
        jaehrliche_kosten = darlehen_rueckzahlung_jahr + nicht_umlagefaehige_jahr
        neues_verfuegbares_einkommen = verfuegbares_einkommen_mtl - (jaehrliche_kosten / 12)
        
        display_table = [
            {'kennzahl': 'Laufende Kosten p.a.', 'val1': -nicht_umlagefaehige_jahr, 'val2': -nicht_umlagefaehige_jahr},
            {'kennzahl': 'Rückzahlung Darlehen p.a.', 'val1': -darlehen_rueckzahlung_jahr, 'val2': -darlehen_rueckzahlung_jahr},
            {'kennzahl': '- Zinsen p.a.', 'val1': zinsen_jahr, 'val2': zinsen_jahr},
            {'kennzahl': 'Jährliche Gesamtkosten', 'val1': -jaehrliche_kosten, 'val2': -jaehrliche_kosten},
            {'kennzahl': 'Ihr monatl. Einkommen (vorher)', 'val1': verfuegbares_einkommen_mtl, 'val2': verfuegbares_einkommen_mtl},
            {'kennzahl': '- Mtl. Kosten Immobilie', 'val1': -jaehrliche_kosten / 12, 'val2': -jaehrliche_kosten / 12},
            {'kennzahl': '= Neues verfügbares Einkommen', 'val1': neues_verfuegbares_einkommen, 'val2': neues_verfuegbares_einkommen}
        ]
        finanzkennzahlen = {}
    
    return {
        'display_table': display_table,
        'finanzkennzahlen': finanzkennzahlen
    }

def create_pdf_report(results, inputs, checklist_items):
    pdf = FPDF()
    pdf.add_page()
    
    def format_eur_pdf(val):
        try:
            f = float(str(val).replace(",", "."))
            return f"{f:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return str(val)
    
    def format_percent_pdf(val):
        try:
            f = float(val)
            return f"{f:.2f} %"
        except Exception:
            return str(val)
    
    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, "Finanzanalyse Immobilieninvestment", ln=True, align='C')
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Erstellt am: {datetime.now().strftime('%d.%m.%Y')}", ln=True)
    pdf.cell(0, 8, f"Objekt in: {inputs.get('wohnort','')}", ln=True)
    pdf.ln(5)
    
    # 1. Objektdaten
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "1. Objektdaten", ln=True)
    pdf.set_font("Arial", "", 10)
    
    objektdaten = [
        ("Baujahr:", inputs.get('baujahr_kategorie', '')),
        ("Wohnflaeche (qm):", str(inputs.get('wohnflaeche_qm', ''))),
        ("Zimmeranzahl:", str(inputs.get('zimmeranzahl', ''))),
        ("Stockwerk:", str(inputs.get('stockwerk', ''))),
        ("Energieeffizienz:", str(inputs.get('energieeffizienz', ''))),
        ("OEPNV-Anbindung:", str(inputs.get('oepnv_anbindung', ''))),
        ("Besonderheiten:", str(inputs.get('besonderheiten', ''))),
        ("Kaufpreis:", format_eur_pdf(inputs.get('kaufpreis', 0))),
        ("Eigenkapital:", format_eur_pdf(inputs.get('eigenkapital', 0)))
    ]
    
    for label, wert in objektdaten:
        pdf.cell(60, 6, label, border=0)
        pdf.cell(60, 6, str(wert), border=0, ln=True)
    
    pdf.ln(5)
    
    # 2. Finanzierung
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2. Finanzierung", ln=True)
    pdf.set_font("Arial", "", 10)
    
    nebenkosten_summe = (inputs.get('kaufpreis',0) + inputs.get('garage_stellplatz_kosten',0)) * sum(inputs.get('nebenkosten_prozente',{}).values())/100
    gesamtinvest = inputs.get('kaufpreis',0) + inputs.get('garage_stellplatz_kosten',0) + inputs.get('invest_bedarf',0) + nebenkosten_summe
    darlehen = gesamtinvest - inputs.get('eigenkapital',0)
    
    finanzierung = [
        ("Gesamtinvestition:", format_eur_pdf(gesamtinvest)),
        ("Eigenkapital:", format_eur_pdf(inputs.get('eigenkapital',0))),
        ("Darlehen:", format_eur_pdf(darlehen)),
        ("Zinssatz:", format_percent_pdf(inputs.get('zins1_prozent', 0))),
        ("Tilgungssatz:", format_percent_pdf(inputs.get('tilgung1_prozent', 0) or 0))
    ]
    
    for label, wert in finanzierung:
        pdf.cell(60, 6, label, border=0)
        pdf.cell(60, 6, str(wert), border=0, ln=True)
    
    pdf.ln(5)
    
    # 3. Cashflow-Tabelle
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "3. Cashflow-Analyse", ln=True)
    
    # Tabellen-Header
    pdf.set_font("Arial", "B", 9)
    pdf.cell(80, 8, "Kennzahl", border=1)
    pdf.cell(35, 8, "Jahr 1", border=1)
    pdf.cell(35, 8, "Laufende Jahre", border=1, ln=True)
    
    pdf.set_font("Arial", "", 9)
    
    # Wichtigste Cashflow-Zeilen
    wichtige_zeilen = [
        "Einnahmen p.a. (Kaltmiete)" if inputs.get("nutzungsart") == "Vermietung" else "Laufende Kosten p.a.",
        "Nicht umlagef. Kosten p.a." if inputs.get("nutzungsart") == "Vermietung" else "Rückzahlung Darlehen p.a.",
        "Rückzahlung Darlehen p.a." if inputs.get("nutzungsart") == "Vermietung" else "- Zinsen p.a.",
        "= Cashflow vor Steuern p.a." if inputs.get("nutzungsart") == "Vermietung" else "Jährliche Gesamtkosten",
        "= Effektiver Cashflow n. St. p.a." if inputs.get("nutzungsart") == "Vermietung" else "Ihr monatl. Einkommen (vorher)",
        "Ihr monatl. Einkommen (vorher)",
        "+/- Mtl. Cashflow Immobilie" if inputs.get("nutzungsart") == "Vermietung" else "- Mtl. Kosten Immobilie",
        "= Neues verfügbares Einkommen"
    ]
    
    for zeile in wichtige_zeilen:
        row = next((r for r in results['display_table'] if zeile in r['kennzahl']), None)
        if row:
            kennzahl = str(row.get('kennzahl', ''))
            kennzahl = kennzahl.replace("ü", "ue").replace("ö", "oe").replace("ä", "ae")
            
            val1 = format_eur_pdf(row.get('val1', 0)) if is_number(row.get('val1', 0)) else str(row.get('val1', ''))
            val2 = format_eur_pdf(row.get('val2', 0)) if is_number(row.get('val2', 0)) else str(row.get('val2', ''))
            
            pdf.cell(80, 6, kennzahl, border=1)
            pdf.cell(35, 6, val1, border=1)
            pdf.cell(35, 6, val2, border=1, ln=True)
    
    pdf.ln(5)
    
    # 4. Finanzkennzahlen (nur bei Vermietung)
    if inputs.get("nutzungsart") == "Vermietung" and 'finanzkennzahlen' in results:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "4. Finanzkennzahlen", ln=True)
        pdf.set_font("Arial", "", 10)
        
        for k, v in results['finanzkennzahlen'].items():
            wert = format_percent_pdf(v) if "rendite" in k.lower() else str(v)
            pdf.cell(60, 6, k + ":", border=0)
            pdf.cell(60, 6, wert, border=0, ln=True)
        
        pdf.ln(5)
    
    # 5. Checkliste
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "5. Checkliste", ln=True)
    pdf.set_font("Arial", "", 10)
    
    checklist_status = inputs.get("checklist_status", {})
    for item in checklist_items[:8]:  # Nur erste 8 Items wegen Platz
        checked = checklist_status.get(item, False)
        box = "X" if checked else " "
        item_clean = item.replace("ü", "ue").replace("ö", "oe").replace("ä", "ae")
        pdf.cell(0, 5, f"[{box}] {item_clean}", ln=True)
    
    # FINAL KORRIGIERT: Nur dest='S' ohne encode()
    return pdf.output(dest='S')

st.title("🏠 Immobilien-Analyse-Tool")
st.markdown("---")

nutzungsart = st.selectbox("Nutzungsart wählen", ["Vermietung", "Eigennutzung"], index=0)

st.markdown("---")
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
kaufpreis = st.number_input("Kaufpreis (€)", min_value=0, max_value=10000000, value=250000, step=1000)
garage_stellplatz = st.number_input("Garage/Stellplatz (€)", min_value=0, max_value=50000, value=0, step=1000)
invest_bedarf = st.number_input("Zusätzl. Investitionsbedarf (€)", min_value=0, max_value=1000000, value=10000, step=1000)
eigenkapital = st.number_input("Eigenkapital (€)", min_value=0, max_value=10000000, value=80000, step=1000)

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
    tilg_eur1 = st.number_input("Tilgung (€ mtl.)", min_value=0, max_value=50000, value=350, step=50)
    tilgung1, laufzeit1 = None, None
else:
    laufzeit1 = st.number_input("Laufzeit (Jahre)", min_value=1, max_value=50, value=25, step=1)
    tilgung1, tilg_eur1 = None, None

modus_d1 = 'tilgungssatz' if tilgung1_modus.startswith("Tilgungssatz") else 'tilgung_euro' if tilgung1_modus.startswith("Tilgungsbetrag") else 'laufzeit'
d1 = berechne_darlehen_details(darlehen1_summe, zins1, tilgung_p=tilgung1, tilgung_euro_mtl=tilg_eur1, laufzeit_jahre=laufzeit1, modus=modus_d1)

st.markdown(f"""
**Darlehen Übersicht:**
- Darlehenssumme: **{darlehen1_summe:,.2f} €**
- Rate: **{d1['monatsrate']:,.2f} €**
- Laufzeit: **{d1['laufzeit_jahre']:.1f} Jahre**
- Tilgungssatz: **{d1['tilgung_p_ergebnis']:.2f} %**
""")

st.markdown("---")
st.header("3. Laufende Posten & Steuer")

if nutzungsart == "Vermietung":
    kaltmiete_monatlich = st.number_input("Kaltmiete mtl. (€)", min_value=0, max_value=10000, value=1000, step=50)
    umlagefaehige_monat = st.number_input("Umlagefähige Kosten (€ mtl.)", min_value=0, max_value=1000, value=150, step=10)
    nicht_umlagefaehige_pa = st.number_input("Nicht umlagef. Kosten p.a. (€)", min_value=0, max_value=10000, value=960, step=10)
else:
    kaltmiete_monatlich = 0
    umlagefaehige_monat = 0
    nicht_umlagefaehige_pa = st.number_input("Laufende Kosten p.a. (Hausgeld etc.)", min_value=0, max_value=10000, value=960, step=10)

steuersatz = st.number_input("Persönl. Steuersatz (%)", min_value=0.0, max_value=100.0, value=42.0, step=0.5)

st.subheader("Persönliche Finanzsituation")
verfuegbares_einkommen = st.number_input("Monatl. verfügbares Einkommen (€)", min_value=0, max_value=100000, value=2500, step=100)

st.markdown("---")
st.header("4. Checkliste: Wichtige Dokumente")
st.markdown("Haken Sie ab, welche Dokumente Sie bereits haben:")

if 'checklist_status' not in st.session_state:
    st.session_state['checklist_status'] = {}

for i, item in enumerate(checklist_items):
    st.session_state['checklist_status'][item] = st.checkbox(item, key=f"check_{item}_{i}", value=st.session_state['checklist_status'].get(item, False))

inputs = {
    'wohnort': wohnort, 'baujahr_kategorie': baujahr, 'wohnflaeche_qm': wohnflaeche_qm, 'stockwerk': stockwerk,
    'zimmeranzahl': zimmeranzahl, 'energieeffizienz': energieeffizienz, 'oepnv_anbindung': oepnv_anbindung,
    'besonderheiten': besonderheiten, 'kaufpreis': kaufpreis, 'garage_stellplatz_kosten': garage_stellplatz,
    'invest_bedarf': invest_bedarf, 'eigenkapital': eigenkapital,
    'nebenkosten_prozente': {'grunderwerbsteuer': grunderwerbsteuer, 'notar': notar, 'grundbuch': grundbuch, 'makler': makler},
    'nutzungsart': nutzungsart, 'zins1_prozent': zins1, 'modus_d1': modus_d1,
    'tilgung1_prozent': tilgung1 if tilgung1_modus.startswith("Tilgungssatz") else None,
    'tilgung1_euro_mtl': tilg_eur1 if tilgung1_modus.startswith("Tilgungsbetrag") else None,
    'laufzeit1_jahre': laufzeit1 if tilgung1_modus.startswith("Laufzeit") else None,
    'kaltmiete_monatlich': kaltmiete_monatlich, 'umlagefaehige_kosten_monatlich': umlagefaehige_monat,
    'nicht_umlagefaehige_kosten_pa': nicht_umlagefaehige_pa, 'steuersatz': steuersatz,
    'verfuegbares_einkommen_mtl': verfuegbares_einkommen, 'checklist_status': st.session_state['checklist_status']
}

if 'results' not in st.session_state:
    st.session_state['results'] = None

if st.button("Analyse berechnen"):
    results = calculate_analytics(inputs)
    st.session_state['results'] = results

results = st.session_state['results']

if results:
    st.subheader("Ergebnisse")
    
    if nutzungsart == "Vermietung":
        all_keys = [
            "Einnahmen p.a. (Kaltmiete)", "Umlagefähige Kosten p.a.", "Nicht umlagef. Kosten p.a.",
            "Rückzahlung Darlehen p.a.", "- Zinsen p.a.", "Jährliche Gesamtkosten",
            "= Cashflow vor Steuern p.a.", "- AfA p.a.", "- Absetzbare Kaufnebenkosten (Jahr 1)",
            "= Steuerlicher Gewinn/Verlust p.a.", "+ Steuerersparnis / -last p.a.",
            "= Effektiver Cashflow n. St. p.a.", "Ihr monatl. Einkommen (vorher)",
            "+/- Mtl. Cashflow Immobilie", "= Neues verfügbares Einkommen"
        ]
    else:
        all_keys = [
            "Laufende Kosten p.a.", "Rückzahlung Darlehen p.a.", "- Zinsen p.a.",
            "Jährliche Gesamtkosten", "Ihr monatl. Einkommen (vorher)",
            "- Mtl. Kosten Immobilie", "= Neues verfügbares Einkommen"
        ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Jahr der Anschaffung (€)")
        for key in all_keys:
            val = next((r['val1'] for r in results['display_table'] if key in r['kennzahl']), "")
            if val != "":
                style = "font-weight: bold;" if key.startswith("=") or "+ Steuerersparnis" in key else ""
                st.markdown(f"<div style='{style}'>{key}: {format_eur(val) if is_number(val) else val}</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### Laufende Jahre (€)")
        for key in all_keys:
            val = next((r['val2'] for r in results['display_table'] if key in r['kennzahl']), "")
            if val != "":
                style = "font-weight: bold;" if key.startswith("=") or "+ Steuerersparnis" in key else ""
                st.markdown(f"<div style='{style}'>{key}: {format_eur(val) if is_number(val) else val}</div>", unsafe_allow_html=True)
    
    if 'finanzkennzahlen' in results and results['finanzkennzahlen']:
        st.subheader("Finanzkennzahlen")
        for k, v in results['finanzkennzahlen'].items():
            if "rendite" in k.lower():
                st.markdown(f"**{k}:** {format_percent(v)}")
            else:
                st.markdown(f"**{k}:** {v}")
    
    if st.button("PDF-Bericht erstellen"):
        try:
            pdf_bytes = create_pdf_report(results, inputs, checklist_items)
            st.success("PDF erfolgreich erstellt!")
            st.download_button(
                label="📄 PDF-Bericht herunterladen",
                data=pdf_bytes,
                file_name=f"Immobilien_Analyse_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Fehler beim Erstellen des PDFs: {str(e)}")
