import streamlit as st
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

st.set_page_config(page_title="Immobilien-Analyse", page_icon="🏠", layout="wide")

# Checkliste Items definieren
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

# Ersatz für immo_core Funktionen
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
    # Grundberechnungen
    kaufpreis = inputs.get('kaufpreis', 0)
    garage_stellplatz = inputs.get('garage_stellplatz_kosten', 0)
    invest_bedarf = inputs.get('invest_bedarf', 0)
    nebenkosten_prozente = inputs.get('nebenkosten_prozente', {})
    nebenkosten_summe = (kaufpreis + garage_stellplatz) * sum(nebenkosten_prozente.values()) / 100
    gesamtinvestition = kaufpreis + garage_stellplatz + invest_bedarf + nebenkosten_summe
    eigenkapital = inputs.get('eigenkapital', 0)
    darlehen_summe = gesamtinvestition - eigenkapital
    
    # Darlehen Details
    d1 = berechne_darlehen_details(
        darlehen_summe,
        inputs.get('zins1_prozent', 0),
        tilgung_p=inputs.get('tilgung1_prozent'),
        tilgung_euro_mtl=inputs.get('tilgung1_euro_mtl'),
        laufzeit_jahre=inputs.get('laufzeit1_jahre'),
        modus=inputs.get('modus_d1', 'tilgungssatz')
    )
    
    # Einnahmen und Ausgaben
    kaltmiete_jahr = inputs.get('kaltmiete_monatlich', 0) * 12
    umlagefaehige_jahr = inputs.get('umlagefaehige_kosten_monatlich', 0) * 12
    nicht_umlagefaehige_jahr = inputs.get('nicht_umlagefaehige_kosten_pa', 0)
    
    # Darlehen Kosten
    zinsen_jahr = darlehen_summe * inputs.get('zins1_prozent', 0) / 100
    tilgung_jahr = d1['monatsrate'] * 12 - zinsen_jahr
    darlehen_rueckzahlung_jahr = d1['monatsrate'] * 12
    
    # AfA Berechnung (2% vom Gebäudewert, angenommen 80% des Kaufpreises)
    afa_jahr = kaufpreis * 0.8 * 0.02
    
    # Steuerberechnung
    if inputs.get('nutzungsart') == 'Vermietung':
        steuerlicher_gewinn = kaltmiete_jahr - nicht_umlagefaehige_jahr - zinsen_jahr - afa_jahr
        # Jahr 1: zusätzlich absetzbare Kaufnebenkosten
        steuerlicher_gewinn_jahr1 = steuerlicher_gewinn - nebenkosten_summe
        steuerersparnis_jahr1 = steuerlicher_gewinn_jahr1 * inputs.get('steuersatz', 0) / 100
        steuerersparnis_laufend = steuerlicher_gewinn * inputs.get('steuersatz', 0) / 100
        
        cashflow_vor_steuer = kaltmiete_jahr + umlagefaehige_jahr - nicht_umlagefaehige_jahr - darlehen_rueckzahlung_jahr
        cashflow_nach_steuer_jahr1 = cashflow_vor_steuer + steuerersparnis_jahr1
        cashflow_nach_steuer_laufend = cashflow_vor_steuer + steuerersparnis_laufend
    else:
        steuerersparnis_jahr1 = 0
        steuerersparnis_laufend = 0
        cashflow_nach_steuer_jahr1 = -(nicht_umlagefaehige_jahr + darlehen_rueckzahlung_jahr)
        cashflow_nach_steuer_laufend = cashflow_nach_steuer_jahr1
    
    # Persönliche Finanzsituation
    verfuegbares_einkommen_mtl = inputs.get('verfuegbares_einkommen_mtl', 0)
    mtl_kosten_immobilie = d1['monatsrate'] + nicht_umlagefaehige_jahr / 12
    neues_verfuegbares_einkommen = verfuegbares_einkommen_mtl - mtl_kosten_immobilie
    
    # Display Table erstellen
    if inputs.get('nutzungsart') == 'Vermietung':
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
            {'kennzahl': 'Gesamt-Cashflow (Ihre persönliche Si)', 'val1': cashflow_nach_steuer_jahr1, 'val2': cashflow_nach_steuer_laufend},
            {'kennzahl': 'Ihr monatl. Einkommen (vorher)', 'val1': verfuegbares_einkommen_mtl, 'val2': verfuegbares_einkommen_mtl},
            {'kennzahl': '- Mtl. Kosten Immobilie', 'val1': -mtl_kosten_immobilie, 'val2': -mtl_kosten_immobilie},
            {'kennzahl': '= Neues verfügbares Einkommen', 'val1': neues_verfuegbares_einkommen, 'val2': neues_verfuegbares_einkommen}
        ]
    else:
        display_table = [
            {'kennzahl': 'Laufende Kosten p.a.', 'val1': -nicht_umlagefaehige_jahr, 'val2': -nicht_umlagefaehige_jahr},
            {'kennzahl': 'Rückzahlung Darlehen p.a.', 'val1': -darlehen_rueckzahlung_jahr, 'val2': -darlehen_rueckzahlung_jahr},
            {'kennzahl': '- Zinsen p.a.', 'val1': zinsen_jahr, 'val2': zinsen_jahr},
            {'kennzahl': 'Jährliche Gesamtkosten', 'val1': -(nicht_umlagefaehige_jahr + darlehen_rueckzahlung_jahr), 'val2': -(nicht_umlagefaehige_jahr + darlehen_rueckzahlung_jahr)},
            {'kennzahl': 'Gesamt-Cashflow (Ihre persönliche Si)', 'val1': cashflow_nach_steuer_jahr1, 'val2': cashflow_nach_steuer_laufend},
            {'kennzahl': 'Ihr monatl. Einkommen (vorher)', 'val1': verfuegbares_einkommen_mtl, 'val2': verfuegbares_einkommen_mtl},
            {'kennzahl': '- Mtl. Kosten Immobilie', 'val1': -mtl_kosten_immobilie, 'val2': -mtl_kosten_immobilie},
            {'kennzahl': '= Neues verfügbares Einkommen', 'val1': neues_verfuegbares_einkommen, 'val2': neues_verfuegbares_einkommen}
        ]
    
    # Finanzkennzahlen
    if inputs.get('nutzungsart') == 'Vermietung':
        bruttomietrendite = (kaltmiete_jahr / gesamtinvestition * 100) if gesamtinvestition > 0 else 0
        eigenkapitalrendite = (cashflow_nach_steuer_laufend / eigenkapital * 100) if eigenkapital > 0 else 0
        finanzkennzahlen = {
            'Bruttomietrendite': bruttomietrendite,
            'Eigenkapitalrendite': eigenkapitalrendite
        }
    else:
        finanzkennzahlen = {}
    
    return {
        'display_table': display_table,
        'finanzkennzahlen': finanzkennzahlen
    }

def create_pdf_report(results, inputs, checklist_items):
    pdf = FPDF()
    pdf.add_page()
    
    # Verwende Standard-Fonts
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, "Finanzanalyse Immobilieninvestment", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Bericht erstellt am: {datetime.now().strftime('%d.%m.%Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Analyse für Objekt in: {inputs.get('wohnort','')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    
    # 1. Objekt- & Investmentübersicht
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "1. Objekt- & Investmentübersicht", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Arial", "", 10)
    
    immotable = [
        ("Baujahr:", inputs.get('baujahr_kategorie', '')),
        ("Wohnfläche (qm):", str(inputs.get('wohnflaeche_qm', ''))),
        ("Zimmeranzahl:", str(inputs.get('zimmeranzahl', ''))),
        ("Stockwerk:", str(inputs.get('stockwerk', ''))),
        ("Energieeffizienz:", str(inputs.get('energieeffizienz', ''))),
        ("ÖPNV-Anbindung:", str(inputs.get('oepnv_anbindung', ''))),
        ("Besonderheiten:", str(inputs.get('besonderheiten', ''))),
        ("Kaufpreis:", format_eur(inputs.get('kaufpreis', 0))),
        ("Garage/Stellplatz:", format_eur(inputs.get('garage_stellplatz_kosten', 0))),
        ("Investitionsbedarf:", format_eur(inputs.get('invest_bedarf', 0))),
    ]
    
    nebenkosten_summe = (inputs.get('kaufpreis',0) + inputs.get('garage_stellplatz_kosten',0)) * sum(inputs.get('nebenkosten_prozente',{}).values())/100
    immotable.append(("Kaufnebenkosten:", format_eur(nebenkosten_summe)))
    
    gesamtinvest = inputs.get('kaufpreis',0)+inputs.get('garage_stellplatz_kosten',0)+inputs.get('invest_bedarf',0)+nebenkosten_summe
    immotable.append(("Gesamtinvestition:", format_eur(gesamtinvest)))
    
    for k, v in immotable:
        pdf.cell(65, 7, k, border=0)
        pdf.cell(40, 7, v, border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(2)
    
    # 2. Finanzierungsstruktur & Darlehensdetails
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2. Finanzierungsstruktur & Darlehensdetails", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Arial", "", 10)
    
    ek = inputs.get('eigenkapital',0)
    fk = gesamtinvest - ek
    pdf.cell(65, 7, "Eigenkapital:", border=0)
    pdf.cell(40, 7, format_eur(ek), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(65, 7, "Fremdkapital (Darlehen):", border=0)
    pdf.cell(40, 7, format_eur(fk), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Darlehen I Details
    d1 = berechne_darlehen_details(
        fk,
        inputs.get('zins1_prozent',0),
        tilgung_p=inputs.get('tilgung1_prozent',None),
        tilgung_euro_mtl=inputs.get('tilgung1_euro_mtl',None),
        laufzeit_jahre=inputs.get('laufzeit1_jahre',None),
        modus=inputs.get('modus_d1','tilgungssatz')
    )
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, "Darlehen I:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Arial", "", 10)
    pdf.cell(65, 7, "Zinssatz (%):", border=0)
    pdf.cell(40, 7, format_percent(inputs.get('zins1_prozent', '')), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(65, 7, "Tilgungssatz (%):", border=0)
    
    tilgung1 = inputs.get('tilgung1_prozent', '') or ""
    if tilgung1 == "" and inputs.get('tilgung1_euro_mtl'):
        tilgung1 = f"{inputs.get('tilgung1_euro_mtl')} € mtl."
    pdf.cell(40, 7, str(tilgung1), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    laufzeit_anzeige = inputs.get('laufzeit1_jahre')
    if not laufzeit_anzeige or laufzeit_anzeige in [None, '', 0]:
        laufzeit_anzeige = f"{d1.get('laufzeit_jahre',''):.1f}" if d1.get('laufzeit_jahre') else ""
    pdf.cell(65, 7, "Laufzeit (Jahre):", border=0)
    pdf.cell(40, 7, str(laufzeit_anzeige), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(65, 7, "Monatsrate (€):", border=0)
    pdf.cell(40, 7, format_eur(d1.get('monatsrate', '')), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(2)
    
    # 3. Detailrechnung & Persönlicher Cashflow
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "3. Detailrechnung & Persönlicher Cashflow", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(80, 7, "Kennzahl", border=1)
    pdf.cell(35, 7, "Jahr 1 (€)", border=1)
    pdf.cell(35, 7, "Laufende Jahre (€)", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Arial", "", 10)
    
    if inputs.get("nutzungsart") == "Vermietung":
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
    else:
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
    
    for key in all_keys:
        row = next((r for r in results['display_table'] if key in r['kennzahl']), None)
        if row:
            kennzahl = str(row.get('kennzahl', ''))
            val1_raw = row.get('val1', '')
            val2_raw = row.get('val2', '')
            
            try:
                val1 = format_eur(val1_raw) if is_number(val1_raw) else str(val1_raw) if val1_raw not in [None, "None"] else ""
            except Exception:
                val1 = ""
            
            try:
                val2 = format_eur(val2_raw) if is_number(val2_raw) else str(val2_raw) if val2_raw not in [None, "None"] else ""
            except Exception:
                val2 = ""
            
            pdf.cell(80, 7, kennzahl, border=1)
            pdf.cell(35, 7, val1, border=1)
            pdf.cell(35, 7, val2, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # 4. Finanzkennzahlen
    if 'finanzkennzahlen' in results and results['finanzkennzahlen']:
        pdf.ln(3)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "4. Finanzkennzahlen", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(80, 7, "Kennzahl", border=1)
        pdf.cell(35, 7, "Wert", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Arial", "", 10)
        
        for k, v in results['finanzkennzahlen'].items():
            if "rendite" in k.lower():
                v = format_percent(v)
            pdf.cell(80, 7, k, border=1)
            pdf.cell(35, 7, str(v), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # 5. Checkliste
    pdf.ln(3)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "5. Checkliste: Wichtige Dokumente", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Arial", "", 10)
    
    checklist_status = inputs.get("checklist_status", {})
    for item in checklist_items:
        checked = checklist_status.get(item, False)
        box = "☑" if checked else "☐"
        pdf.cell(0, 7, f"{box} {item}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    result = pdf.output()
    if isinstance(result, bytearray):
        return bytes(result)
    return result

# Titel und Icon
try:
    icon_path = Path(__file__).with_name("10751558.png")
    st.image(Image.open(icon_path).resize((64, 64)))
except Exception:
    pass

st.title("🏠 Immobilien-Analyse-Tool (Streamlit Edition)")
st.markdown("---")

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

modus_d1 = 'tilgungssatz' if tilgung1_modus.startswith("Tilgungssatz") else 'tilgung_euro' if tilgung1_modus.startswith("Tilgungsbetrag") else 'laufzeit'
d1 = berechne_darlehen_details(
    darlehen1_summe,
    zins1,
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

if show_darlehen2:
    d2 = berechne_darlehen_details(
        0,
        zins2,
        tilgung_p=tilgung2,
        tilgung_euro_mtl=tilg_eur2,
        laufzeit_jahre=laufzeit2,
        modus=('tilgungssatz' if tilgung2_modus and tilgung2_modus.startswith("Tilgungssatz") else 'tilgung_euro' if tilgung2_modus and tilgung2_modus.startswith("Tilgungsbetrag") else 'laufzeit')
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

# 4. Checkliste: Wichtige Dokumente
st.header("4. Checkliste: Wichtige Dokumente")
st.markdown("Haken Sie ab, welche Dokumente Sie bereits haben:")

# Interaktive Checkliste-Status speichern
if 'checklist_status' not in st.session_state:
    st.session_state['checklist_status'] = {}

for item in checklist_items:
    st.session_state['checklist_status'][item] = st.checkbox(
        item, 
        key=f"check_{item}", 
        value=st.session_state['checklist_status'].get(item, False)
    )

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
    'modus_d2': ('tilgungssatz' if tilgung2_modus and tilgung2_modus.startswith("Tilgungssatz") else 'tilgung_euro' if tilgung2_modus and tilgung2_modus.startswith("Tilgungsbetrag") else 'laufzeit'),
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
    results = calculate_analytics(inputs)
    if 'error' in results:
        st.session_state['results'] = None
        st.error(results['error'])
    else:
        st.session_state['results'] = results

results = st.session_state['results']

if results:
    st.subheader("Ergebnisse")
    
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
    else:
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
    
    col1, col2, col3 = st.columns([2.5, 2.5, 1])
    
    with col1:
        st.markdown("#### Jahr der Anschaffung (€)")
        for key in all_keys:
            val = next((r['val1'] for r in results['display_table'] if key in r['kennzahl']), "")
            if val != "":
                style = "font-weight: bold;" if key.startswith("=") or "+ Steuerersparnis" in key else ""
                st.markdown(
                    f"<div style='{style}'>{key}: {format_eur(val) if is_number(val) else val}</div>",
                    unsafe_allow_html=True
                )
    
    with col2:
        st.markdown("#### Laufende Jahre (€)")
        for key in all_keys:
            val = next((r['val2'] for r in results['display_table'] if key in r['kennzahl']), "")
            if val != "":
                style = "font-weight: bold;" if key.startswith("=") or "+ Steuerersparnis" in key else ""
                st.markdown(
                    f"<div style='{style}'>{key}: {format_eur(val) if is_number(val) else val}</div>",
                    unsafe_allow_html=True
                )
    
    # Finanzkennzahlen anzeigen
    if 'finanzkennzahlen' in results and results['finanzkennzahlen']:
        st.subheader("Finanzkennzahlen")
        for k, v in results['finanzkennzahlen'].items():
            if "rendite" in k.lower():
                st.markdown(f"**{k}:** {format_percent(v)}")
            else:
                st.markdown(f"**{k}:** {v}")
    
    # PDF-Erstellung
    if st.button("PDF-Bericht erstellen"):
        try:
            pdf_bytes = create_pdf_report(results, inputs, checklist_items)
            st.session_state['pdf_bytes'] = pdf_bytes
            st.success("PDF erfolgreich erstellt!")
        except Exception as e:
            st.error(f"Fehler beim Erstellen des PDFs: {str(e)}")
    
    if st.session_state.get('pdf_bytes'):
        st.download_button(
            label="📄 PDF-Bericht herunterladen",
            data=st.session_state['pdf_bytes'],
            file_name=f"Immobilien_Analyse_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )
