import streamlit as st
import math
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Immobilien-Analyse", page_icon="🏠", layout="wide")

# ═════════════════════════════════════════════════════════════════════════════
# KONSTANTEN
# ═════════════════════════════════════════════════════════════════════════════
CO2_KOST_AUFG_PREIS = 60  # €/Tonne, gesetzlich fixiert 2026

HEIZUNG_CO2_FAKTOR = {
    "Gas":                0.18139,
    "Heizöl":             0.26640,
    "Fernwärme (fossil)": 0.18000,
    "Wärmepumpe":         0.0,
    "Pellets/Holz":       0.0,
}

ENERGIEKLASSE_VERBRAUCH = {  # Endenergie kWh/m²/a (Schätzwert)
    "A+": 15, "A": 30, "B": 55, "C": 80,
    "D": 110, "E": 145, "F": 185, "G": 230, "H": 300
}

CO2_STUFEN_VERMIETER = [  # CO2KostAufG Anlage §§ 5–7
    (0,  12, 0.00), (12, 17, 0.10), (17, 22, 0.20),
    (22, 27, 0.30), (27, 32, 0.40), (32, 37, 0.50),
    (37, 42, 0.60), (42, 47, 0.70), (47, 52, 0.80),
    (52, float('inf'), 0.95),
]

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

# ═════════════════════════════════════════════════════════════════════════════
# HILFSFUNKTIONEN
# ═════════════════════════════════════════════════════════════════════════════
def format_eur(val):
    """Zahl mit €-Zeichen, deutsches Format: 1.234,56 €"""
    try:
        f = float(str(val).replace(",", "."))
        return f"{f:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(val)

def de(val, d=2):
    """Deutsche Zahlenformatierung ohne €: 1.234,56 — für f-Strings"""
    try:
        f = float(str(val).replace(",", "."))
        s = f"{f:,.{d}f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(val)

def format_percent(val):
    try:
        return f"{float(val):.2f} %"
    except Exception:
        return str(val)

def is_number(val):
    try:
        float(str(val).replace(",", "."))
        return True
    except:
        return False

def berechne_co2_vermieter(heizungstyp, effizienzklasse, wohnflaeche, jahresverbrauch_kwh=None):
    faktor = HEIZUNG_CO2_FAKTOR.get(heizungstyp, 0)
    if faktor == 0 or wohnflaeche <= 0:
        return {'co2_qm': 0.0, 'vermieter_anteil': 0.0, 'vermieter_kosten': 0.0}
    verbrauch = jahresverbrauch_kwh if (jahresverbrauch_kwh and jahresverbrauch_kwh > 0) \
                else ENERGIEKLASSE_VERBRAUCH.get(effizienzklasse, 100) * wohnflaeche
    co2_kg   = verbrauch * faktor
    co2_qm   = co2_kg / wohnflaeche
    anteil   = next((a for lo, hi, a in CO2_STUFEN_VERMIETER if lo <= co2_qm < hi), 0.95)
    kosten   = (co2_kg / 1000 * CO2_KOST_AUFG_PREIS) * anteil
    return {'co2_qm': round(co2_qm, 1), 'vermieter_anteil': anteil, 'vermieter_kosten': round(kosten, 2)}

# ═════════════════════════════════════════════════════════════════════════════
# DARLEHENSBERECHNUNG (Annuitätsformel)
# ═════════════════════════════════════════════════════════════════════════════
def berechne_darlehen_details(summe, zins, tilgung_p=None, tilgung_euro_mtl=None,
                               laufzeit_jahre=None, modus='tilgungssatz'):
    r = zins / 100 / 12

    if modus == 'tilgungssatz' and tilgung_p:
        monatsrate = summe * (zins + tilgung_p) / 100 / 12
        if r > 0 and monatsrate > r * summe:
            laufzeit = math.log(monatsrate / (monatsrate - r * summe)) / math.log(1 + r) / 12
        else:
            laufzeit = summe / (summe * tilgung_p / 100) if tilgung_p > 0 else 0
        return {'monatsrate': monatsrate, 'laufzeit_jahre': laufzeit, 'tilgung_p_ergebnis': tilgung_p}

    elif modus == 'tilgung_euro' and tilgung_euro_mtl:
        monatsrate    = tilgung_euro_mtl
        tilgung_p_erg = ((monatsrate - summe * r) * 12 / summe * 100) if summe > 0 else 0
        if r > 0 and monatsrate > r * summe:
            laufzeit = math.log(monatsrate / (monatsrate - r * summe)) / math.log(1 + r) / 12
        else:
            laufzeit = 0
        return {'monatsrate': monatsrate, 'laufzeit_jahre': laufzeit, 'tilgung_p_ergebnis': tilgung_p_erg}

    elif modus == 'laufzeit' and laufzeit_jahre:
        n          = laufzeit_jahre * 12
        monatsrate = summe * r * (1 + r)**n / ((1 + r)**n - 1) if r > 0 else summe / n
        tilgung_p_erg = ((monatsrate - summe * r) * 12 / summe * 100) if summe > 0 else 0
        return {'monatsrate': monatsrate, 'laufzeit_jahre': laufzeit_jahre, 'tilgung_p_ergebnis': tilgung_p_erg}

    else:
        return {'monatsrate': 0, 'laufzeit_jahre': 0, 'tilgung_p_ergebnis': 0}

# ═════════════════════════════════════════════════════════════════════════════
# HAUPTBERECHNUNG
# ═════════════════════════════════════════════════════════════════════════════
def calculate_analytics(inputs):
    kaufpreis         = inputs.get('kaufpreis', 0)
    garage            = inputs.get('garage_stellplatz_kosten', 0)
    invest_bedarf     = inputs.get('invest_bedarf', 0)
    nk_prozente       = inputs.get('nebenkosten_prozente', {})
    nebenkosten_summe = (kaufpreis + garage) * sum(nk_prozente.values()) / 100
    gesamtinvestition = kaufpreis + garage + invest_bedarf + nebenkosten_summe
    eigenkapital      = inputs.get('eigenkapital', 0)
    darlehen_summe    = gesamtinvestition - eigenkapital

    d1 = berechne_darlehen_details(
        darlehen_summe, inputs.get('zins1_prozent', 0),
        tilgung_p=inputs.get('tilgung1_prozent'),
        tilgung_euro_mtl=inputs.get('tilgung1_euro_mtl'),
        laufzeit_jahre=inputs.get('laufzeit1_jahre'),
        modus=inputs.get('modus_d1', 'tilgungssatz')
    )

    kaltmiete_jahr        = inputs.get('kaltmiete_monatlich', 0) * 12
    umlagefaehige_jahr    = inputs.get('umlagefaehige_kosten_monatlich', 0) * 12
    nicht_umlagefaehige_j = inputs.get('nicht_umlagefaehige_kosten_pa', 0)
    zinsen_jahr           = darlehen_summe * inputs.get('zins1_prozent', 0) / 100
    darlehen_rueck_jahr   = d1['monatsrate'] * 12

    # AfA (§ 7 Abs. 4 EStG)
    baujahr      = inputs.get('baujahr_kategorie', '1925 - 2022')
    afa_satz     = 2.5 if baujahr == 'vor 1925' else 3.0 if baujahr == 'ab 2023' else 2.0
    gebaeude_ant = inputs.get('gebaeude_anteil_prozent', 80)
    afa_jahr     = kaufpreis * (gebaeude_ant / 100) * (afa_satz / 100)

    # Risikopositionen
    mietausfall_pa    = kaltmiete_jahr * inputs.get('mietausfallwagnis_prozent', 0) / 100
    instandhaltung_pa = inputs.get('wohnflaeche_qm', 0) * inputs.get('instandhaltung_euro_qm', 0) * 12

    # CO2-Steuer Vermieteranteil
    co2_data = berechne_co2_vermieter(
        inputs.get('heizungstyp', 'Gas'),
        inputs.get('energieeffizienz', 'B'),
        inputs.get('wohnflaeche_qm', 0),
        inputs.get('jahresverbrauch_kwh')
    )
    co2_pa = co2_data['vermieter_kosten']

    verfuegbar_mtl = inputs.get('verfuegbares_einkommen_mtl', 0)

    if inputs.get('nutzungsart') == 'Vermietung':
        stg_lfd = kaltmiete_jahr - nicht_umlagefaehige_j - zinsen_jahr - afa_jahr - mietausfall_pa - co2_pa
        stg_j1  = stg_lfd - nebenkosten_summe

        # KORREKT: Verlust → positive Steuerersparnis | Gewinn → negative Steuerlast
        steuer_j1  = -(stg_j1  * inputs.get('steuersatz', 0) / 100)
        steuer_lfd = -(stg_lfd * inputs.get('steuersatz', 0) / 100)

        cf_vor      = (kaltmiete_jahr + umlagefaehige_jahr
                       - nicht_umlagefaehige_j - darlehen_rueck_jahr
                       - mietausfall_pa - instandhaltung_pa - co2_pa)
        cf_nach_j1  = cf_vor + steuer_j1
        cf_nach_lfd = cf_vor + steuer_lfd
        nve_j1      = verfuegbar_mtl + cf_nach_j1  / 12
        nve_lfd     = verfuegbar_mtl + cf_nach_lfd / 12
        gesamt_kost = -(nicht_umlagefaehige_j + darlehen_rueck_jahr + mietausfall_pa + instandhaltung_pa + co2_pa)

        display_table = [
            {'kennzahl': 'Einnahmen p.a. (Kaltmiete)',             'val1': kaltmiete_jahr,         'val2': kaltmiete_jahr},
            {'kennzahl': 'Umlagefähige Kosten p.a.',               'val1': umlagefaehige_jahr,     'val2': umlagefaehige_jahr},
            {'kennzahl': 'Nicht umlagef. Kosten p.a.',             'val1': -nicht_umlagefaehige_j, 'val2': -nicht_umlagefaehige_j},
            {'kennzahl': '- Mietausfallwagnis p.a.',               'val1': -mietausfall_pa,        'val2': -mietausfall_pa},
            {'kennzahl': '- Priv. Instandhaltungsrücklage p.a.',   'val1': -instandhaltung_pa,     'val2': -instandhaltung_pa},
            {'kennzahl': '- CO2-Steuer Vermieteranteil p.a.',      'val1': -co2_pa,                'val2': -co2_pa},
            {'kennzahl': 'Rückzahlung Darlehen p.a.',              'val1': -darlehen_rueck_jahr,   'val2': -darlehen_rueck_jahr},
            {'kennzahl': '- Zinsen p.a.',                          'val1': zinsen_jahr,            'val2': zinsen_jahr},
            {'kennzahl': 'Jährliche Gesamtkosten',                 'val1': gesamt_kost,            'val2': gesamt_kost},
            {'kennzahl': '= Cashflow vor Steuern p.a.',            'val1': cf_vor,                 'val2': cf_vor},
            {'kennzahl': '- AfA p.a.',                             'val1': -afa_jahr,              'val2': -afa_jahr},
            {'kennzahl': '- Absetzbare Kaufnebenkosten (Jahr 1)',   'val1': -nebenkosten_summe,     'val2': 0},
            {'kennzahl': '= Steuerlicher Gewinn/Verlust p.a.',     'val1': stg_j1,                 'val2': stg_lfd},
            {'kennzahl': '+ Steuerersparnis / -last p.a.',         'val1': steuer_j1,              'val2': steuer_lfd},
            {'kennzahl': '= Effektiver Cashflow n. St. p.a.',      'val1': cf_nach_j1,             'val2': cf_nach_lfd},
            {'kennzahl': 'Ihr monatl. Einkommen (vorher)',         'val1': verfuegbar_mtl,         'val2': verfuegbar_mtl},
            {'kennzahl': '+/- Mtl. Cashflow Immobilie',            'val1': cf_nach_j1 / 12,        'val2': cf_nach_lfd / 12},
            {'kennzahl': '= Neues verfügbares Einkommen',          'val1': nve_j1,                 'val2': nve_lfd},
        ]
        bruttomietrendite   = (kaltmiete_jahr / gesamtinvestition * 100) if gesamtinvestition > 0 else 0
        eigenkapitalrendite = (cf_nach_lfd / eigenkapital * 100) if eigenkapital > 0 else 0
        finanzkennzahlen    = {'Bruttomietrendite': bruttomietrendite, 'Eigenkapitalrendite': eigenkapitalrendite}

    else:
        instand_eigen_pa  = inputs.get('instand_eigen_pa', 0)
        co2_eigen_pa      = inputs.get('co2_eigen_pa', 0)
        jaehrliche_kosten = darlehen_rueck_jahr + nicht_umlagefaehige_j + instand_eigen_pa + co2_eigen_pa
        nve = verfuegbar_mtl - jaehrliche_kosten / 12
        display_table = [
            {'kennzahl': 'Hausgeld / Betriebskosten p.a.',         'val1': -nicht_umlagefaehige_j,  'val2': -nicht_umlagefaehige_j},
            {'kennzahl': '- Private Instandhaltungsrücklage p.a.', 'val1': -instand_eigen_pa,        'val2': -instand_eigen_pa},
            {'kennzahl': '- CO2-Kosten (Eigennutzer) p.a.',        'val1': -co2_eigen_pa,            'val2': -co2_eigen_pa},
            {'kennzahl': 'Rückzahlung Darlehen p.a.',              'val1': -darlehen_rueck_jahr,     'val2': -darlehen_rueck_jahr},
            {'kennzahl': '- Zinsen p.a.',                          'val1': zinsen_jahr,              'val2': zinsen_jahr},
            {'kennzahl': '- Tilgung p.a. (Vermögensaufbau)',       'val1': darlehen_rueck_jahr - zinsen_jahr, 'val2': darlehen_rueck_jahr - zinsen_jahr},
            {'kennzahl': 'Jährliche Gesamtkosten (inkl. Tilgung)', 'val1': -jaehrliche_kosten,       'val2': -jaehrliche_kosten},
            {'kennzahl': 'Ihr monatl. Einkommen (vorher)',         'val1': verfuegbar_mtl,           'val2': verfuegbar_mtl},
            {'kennzahl': '- Mtl. Kosten Immobilie',                'val1': -jaehrliche_kosten / 12,  'val2': -jaehrliche_kosten / 12},
            {'kennzahl': '= Neues verfügbares Einkommen',          'val1': nve,                      'val2': nve},
        ]
        # Eigenkapitalaufbau durch Tilgung
        tilgung_pa = darlehen_rueck_jahr - zinsen_jahr
        finanzkennzahlen = {
            'tilgung_pa': tilgung_pa,
            'zinsen_pa': zinsen_jahr,
            'reine_wohnkosten_pa': nicht_umlagefaehige_j + instand_eigen_pa + co2_eigen_pa + zinsen_jahr,
        }

    return {'display_table': display_table, 'finanzkennzahlen': finanzkennzahlen}

# ═════════════════════════════════════════════════════════════════════════════
# PDF-BERICHT
# ═════════════════════════════════════════════════════════════════════════════
def create_pdf_report(results, inputs, checklist_items):
    pdf = FPDF()
    pdf.add_page()

    def fmt_eur(val):
        try:
            f = float(str(val).replace(",", "."))
            return f"{f:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return str(val) if val else '0,00 EUR'

    def fmt_pct(val):
        try:
            return f"{float(val):.2f} %"
        except:
            return str(val)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, "Finanzanalyse Immobilieninvestment", ln=True, align='C')
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Erstellt am: {datetime.now().strftime('%d.%m.%Y')}", ln=True)
    pdf.cell(0, 8, f"Objekt in: {inputs.get('wohnort', '')}", ln=True)
    pdf.cell(0, 8, f"Nutzungsart: {inputs.get('nutzungsart', '')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "1. Objektdaten", ln=True)
    pdf.set_font("Arial", "", 10)
    for label, wert in [
        ("Baujahr:",                        inputs.get('baujahr_kategorie', '')),
        ("Wohnflaeche (qm):",               str(inputs.get('wohnflaeche_qm', ''))),
        ("Zimmeranzahl:",                    str(inputs.get('zimmeranzahl', ''))),
        ("Stockwerk:",                       str(inputs.get('stockwerk', ''))),
        ("Energieeffizienz:",                str(inputs.get('energieeffizienz', ''))),
        ("Heizungstyp:",                     str(inputs.get('heizungstyp', ''))),
        ("OEPNV-Anbindung:",                 str(inputs.get('oepnv_anbindung', ''))),
        ("Besonderheiten:",                  str(inputs.get('besonderheiten', ''))),
        ("Kaufpreis:",                       fmt_eur(inputs.get('kaufpreis', 0))),
        ("Eigenkapital:",                    fmt_eur(inputs.get('eigenkapital', 0))),
        ("Gebaeudeanteil (AfA-Basis):",      fmt_pct(inputs.get('gebaeude_anteil_prozent', 80))),
    ]:
        pdf.cell(65, 6, label, border=0)
        pdf.cell(65, 6, str(wert), border=0, ln=True)
    pdf.ln(5)

    nk_sum       = (inputs.get('kaufpreis', 0) + inputs.get('garage_stellplatz_kosten', 0)) * sum(inputs.get('nebenkosten_prozente', {}).values()) / 100
    gesamtinvest = inputs.get('kaufpreis', 0) + inputs.get('garage_stellplatz_kosten', 0) + inputs.get('invest_bedarf', 0) + nk_sum
    darlehen     = gesamtinvest - inputs.get('eigenkapital', 0)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2. Finanzierung", ln=True)
    pdf.set_font("Arial", "", 10)
    for label, wert in [
        ("Gesamtinvestition:", fmt_eur(gesamtinvest)),
        ("Eigenkapital:",      fmt_eur(inputs.get('eigenkapital', 0))),
        ("Darlehen:",          fmt_eur(darlehen)),
        ("Zinssatz:",          fmt_pct(inputs.get('zins1_prozent', 0))),
        ("Tilgungssatz:",      fmt_pct(inputs.get('tilgung1_prozent', 0) or 0)),
    ]:
        pdf.cell(65, 6, label, border=0)
        pdf.cell(65, 6, str(wert), border=0, ln=True)
    pdf.ln(5)

    titel = "3. Cashflow-Analyse (Vermietung)" if inputs.get("nutzungsart") == "Vermietung" else "3. Kostenanalyse (Eigennutzung)"
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, titel, ln=True)
    pdf.set_font("Arial", "B", 8)
    pdf.cell(80, 6, "Kennzahl", border=1)
    pdf.cell(35, 6, "Jahr 1", border=1)
    pdf.cell(35, 6, "Laufende Jahre", border=1, ln=True)
    pdf.set_font("Arial", "", 8)
    for row in results['display_table']:
        k = str(row.get('kennzahl', '')).replace("ü","ue").replace("ö","oe").replace("ä","ae").replace("–","-")
        pdf.cell(80, 5, k, border=1)
        pdf.cell(35, 5, fmt_eur(row.get('val1', 0)), border=1)
        pdf.cell(35, 5, fmt_eur(row.get('val2', 0)), border=1, ln=True)
    pdf.ln(5)

    if inputs.get("nutzungsart") == "Vermietung" and results.get('finanzkennzahlen'):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "4. Finanzkennzahlen", ln=True)
        pdf.set_font("Arial", "", 10)
        for k, v in results['finanzkennzahlen'].items():
            pdf.cell(65, 6, k + ":", border=0)
            pdf.cell(65, 6, fmt_pct(v) if "rendite" in k.lower() else str(v), border=0, ln=True)
        pdf.ln(5)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "5. Checkliste", ln=True)
    pdf.set_font("Arial", "", 10)
    checklist_status = inputs.get("checklist_status", {})
    for item in checklist_items:
        box   = "X" if checklist_status.get(item, False) else " "
        clean = item.replace("ü","ue").replace("ö","oe").replace("ä","ae").replace("–","-")
        pdf.cell(0, 5, f"[{box}] {clean}", ln=True)

    return bytes(pdf.output())

# ═════════════════════════════════════════════════════════════════════════════
# STREAMLIT UI
# ═════════════════════════════════════════════════════════════════════════════
st.title("🏠 Immobilien-Analyse-Tool")
st.markdown("---")

with st.expander("ℹ️ Wie funktioniert dieses Tool? (Erklärung für Einsteiger)", expanded=False):
    st.markdown("""
    Dieses Tool hilft Ihnen, eine Immobilie **als Investment zu bewerten** — bevor Sie zum Notar gehen.

    **So gehen Sie vor:**
    1. **Nutzungsart wählen**: Vermieten oder selbst einziehen?
    2. **Objektdaten eingeben**: Baujahr, Heizung, Lage — beeinflusst Steuer & CO2-Kosten.
    3. **Finanzierung ausfüllen**: Kaufpreis, Eigenkapital, Zins und Tilgung.
    4. **Laufende Kosten angeben**: Was kostet die Wohnung im Betrieb?
    5. **Analyse berechnen**: Das Tool zeigt, wie die Immobilie Ihren Cashflow beeinflusst.

    **Die wichtigsten Ergebnisse:**
    - 📊 **Cashflow vor Steuern**: Was bleibt monatlich übrig, *bevor* das Finanzamt beteiligt ist?
    - 💰 **Cashflow nach Steuern**: Der realistische Wert inkl. AfA-Steuervorteilen.
    - 📈 **Bruttomietrendite**: Faustregel — unter 4% ist in den meisten Lagen unattraktiv.
    - 🏦 **Eigenkapitalrendite**: Richtwert >10% = gut, >20% = sehr gut.
    """)

nutzungsart = st.selectbox(
    "Nutzungsart wählen", ["Vermietung", "Eigennutzung"], index=0,
    help="Vermietung = steuerliche AfA-Berechnung und Cashflow-Analyse. Eigennutzung = reine Kostenübersicht."
)

# ─────────────────────────────────────────────────────────────────────────────
# SEKTION 1: Objekt & Investition
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.header("1. Objekt & Investition")

with st.expander("ℹ️ Warum sind diese Daten wichtig?", expanded=False):
    st.markdown("""
    - **Baujahr** bestimmt den **AfA-Satz**: Vor 1925 → 2,5% | 1925–2022 → 2% | ab 2023 → 3% p.a.
    - **Energieeffizienz + Heizungstyp** bestimmen den **CO2-Steueranteil** (CO2KostAufG): Wärmepumpe/Pellets = 0 €. Gas/Öl + schlechte Effizienz = bis zu 95% Vermieteranteil.
    - **Wohnfläche** fließt in die CO2-Berechnung und die private Instandhaltungsrücklage ein.
    """)

wohnort        = st.text_input("Wohnort / Stadtteil", "Nürnberg",
                    help="Erscheint im PDF-Bericht. Beeinflusst keine Berechnung.")
baujahr        = st.selectbox("Baujahr", ["1925 - 2022", "vor 1925", "ab 2023"],
                    help="Bestimmt den AfA-Satz (§ 7 Abs. 4 EStG). Gilt nur für den Gebäudeanteil.")
wohnflaeche_qm = st.number_input("Wohnfläche (m²)", min_value=10, max_value=500, value=80,
                    help="Wird für CO2-Berechnung und private Instandhaltungsrücklage (€/m²/Monat) verwendet.")
stockwerk      = st.selectbox("Stockwerk", ["EG","1","2","3","4","5","6","DG"],
                    help="Dokumentation für PDF. EG = höheres Einbruchsrisiko, DG = ggf. Dachschäden.")
zimmeranzahl   = st.selectbox("Zimmeranzahl", ["1","1,5","2","2,5","3","3,5","4","4,5","5"], index=4,
                    help="2–3 Zimmer = hohe Mietnachfrage, geringes Leerstandsrisiko.")
energieeffizienz = st.selectbox("Energieeffizienz", ["A+","A","B","C","D","E","F","G","H"], index=2,
                    help="Bestimmt den CO2-Ausstoß und damit den Vermieteranteil an der CO2-Steuer.")
heizungstyp    = st.selectbox("Heizungstyp",
                    ["Gas", "Heizöl", "Fernwärme (fossil)", "Wärmepumpe", "Pellets/Holz"], index=0,
                    help="Wärmepumpe & Pellets: 0 € CO2-Steuer. Gas/Öl: CO2-Kosten je nach Effizienzklasse.")

with st.expander("🔧 Jahresheizverbrauch (optional — für genauere CO2-Berechnung)", expanded=False):
    st.caption("Leer lassen (= 0) → Schätzwert aus Energieklasse. Genauen Wert finden Sie im Energieausweis.")
    jahresverbrauch_kwh = st.number_input("Jährl. Heizenergieverbrauch (kWh/Jahr)",
                              min_value=0, max_value=100000, value=0, step=500,
                              help="0 = Schätzwert aus Energieklasse × Wohnfläche.")

co2_vorschau = berechne_co2_vermieter(heizungstyp, energieeffizienz, wohnflaeche_qm,
                                       jahresverbrauch_kwh if jahresverbrauch_kwh > 0 else None)
if nutzungsart == "Eigennutzung":
    co2_gesamt = berechne_co2_vermieter(heizungstyp, energieeffizienz, wohnflaeche_qm,
                                         jahresverbrauch_kwh if jahresverbrauch_kwh > 0 else None)
    co2_kosten_eigen = (ENERGIEKLASSE_VERBRAUCH.get(energieeffizienz, 100) * wohnflaeche_qm *
                        HEIZUNG_CO2_FAKTOR.get(heizungstyp, 0) / 1000 * CO2_KOST_AUFG_PREIS) if not (jahresverbrauch_kwh and jahresverbrauch_kwh > 0) else (jahresverbrauch_kwh * HEIZUNG_CO2_FAKTOR.get(heizungstyp, 0) / 1000 * CO2_KOST_AUFG_PREIS)
    if HEIZUNG_CO2_FAKTOR.get(heizungstyp, 0) == 0:
        st.success(f"✅ **{heizungstyp}** — keine CO2-Kosten (~{de(co2_vorschau['co2_qm'], 1)} kg CO2/m²/a).")
    else:
        st.warning(
            f"⚠️ **CO2-Kosten (Eigennutzer trägt 100%):** "
            f"~{de(co2_vorschau['co2_qm'], 1)} kg CO2/m²/a | "
            f"Geschätzte Kosten: **~{de(co2_kosten_eigen, 0)} €/Jahr** — fließt in die Kostenrechnung ein."
        )
elif co2_vorschau['vermieter_anteil'] == 0:
    st.success(
        f"✅ **{heizungstyp}** — kein CO2-Steueranteil für den Vermieter "
        f"(~{de(co2_vorschau['co2_qm'], 1)} kg CO2/m²/a → 0%)."
    )
else:
    st.warning(
        f"⚠️ **CO2-Steuer Vermieteranteil: {co2_vorschau['vermieter_anteil']*100:.0f}%** "
        f"(~{de(co2_vorschau['co2_qm'], 1)} kg CO2/m²/a) | "
        f"Geschätzte Kosten: **~{de(co2_vorschau['vermieter_kosten'], 0)} €/Jahr** "
        f"— nicht umlagefähig, fließt in die Cashflow-Berechnung ein."
    )

if energieeffizienz in ["D","E","F","G","H"]:
    st.info("💡 Tipp: Eine energetische Sanierung (Dämmung, Heizungstausch) kann den CO2-Steueranteil "
            "erheblich senken oder eliminieren — und den Wiederverkaufswert steigern.")

oepnv_anbindung = st.selectbox("ÖPNV-Anbindung", ["Sehr gut","Gut","Okay"],
                    help="Gute Anbindung senkt Leerstandsrisiko und stützt den Wiederverkaufspreis.")
besonderheiten  = st.text_input("Besonderheiten", "Balkon, Einbauküche",
                    help="Freitext für den PDF-Bericht.")

# ─────────────────────────────────────────────────────────────────────────────
# SEKTION 2: Finanzierung
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.header("2. Finanzierung")

with st.expander("ℹ️ Was ist der Unterschied zwischen Kaufpreis und Gesamtinvestition?", expanded=False):
    st.markdown("""
    Der **Kaufpreis** ist nur der Anfang. Zur **Gesamtinvestition** kommen hinzu:
    - **Kaufnebenkosten**: Grunderwerbsteuer, Notar, Grundbuch, Makler — in Bayern typisch ~9–10%.
    - **Investitionsbedarf**: Geplante Renovierungen direkt nach dem Kauf.

    💡 Die Kaufnebenkosten sind im Jahr 1 bei Vermietung steuerlich absetzbar → großer Steuereffekt in Jahr 1.
    """)

kaufpreis     = st.number_input("Kaufpreis (€)", min_value=0, max_value=10000000, value=250000, step=1000,
                    help="Reiner Kaufpreis laut Kaufvertrag. Basis für AfA und Renditeberechnung.")
garage        = st.number_input("Garage/Stellplatz (€)", min_value=0, max_value=50000, value=0, step=1000,
                    help="Wird zur Nebenkosten-Basis addiert. Stellplätze selbst sind nicht AfA-fähig.")
invest_bedarf = st.number_input("Zusätzl. Investitionsbedarf (€)", min_value=0, max_value=1000000, value=10000, step=1000,
                    help="Geplante Renovierungen. Erhöht Darlehenssumme, kann als Werbungskosten absetzbar sein.")
eigenkapital  = st.number_input("Eigenkapital (€)", min_value=0, max_value=10000000, value=80000, step=1000,
                    help="Faustregel: Mind. die Kaufnebenkosten (~10%) sollten aus Eigenkapital stammen.")
if nutzungsart == "Eigennutzung" and eigenkapital == 0:
    st.error("⚠️ **Kein Eigenkapital:** Bei einer 100%-Finanzierung werden auch die Kaufnebenkosten kreditfinanziert. Das ist ungewöhnlich risikoreich — Banken verlangen i.d.R. mind. 10–20% EK.")
elif nutzungsart == "Eigennutzung":
    nk_check = (kaufpreis + garage) * (3.5 + 1.5 + 0.5 + 3.57) / 100
    if eigenkapital < nk_check:
        st.warning(f"⚠️ Eigenkapital ({de(eigenkapital, 0)} €) deckt kaum die geschätzten Kaufnebenkosten (~{de(nk_check, 0)} €). Mindestens die Nebenkosten sollten aus eigenen Mitteln stammen.")

if nutzungsart == "Vermietung":
    st.info("💡 **AfA-Basis:** Nur das Gebäude ist abschreibbar — nicht Grund & Boden (§ 7 Abs. 4 EStG). "
            "In Nürnberg (gute Lagen) beträgt der Bodenanteil oft 30–50%. "
            "Bodenrichtwert: [boris.bayern.de](https://www.boris.bayern.de)")
    gebaeude_anteil = st.slider(
        "Gebäudeanteil am Kaufpreis (%) — AfA-Basis",
        min_value=40, max_value=95, value=80, step=5,
        help="100% minus dieser Wert = Bodenanteil (nicht abschreibbar). Je niedriger, desto geringer die jährliche AfA."
    )
    st.caption(
        f"→ AfA-Basis: **{de(kaufpreis * gebaeude_anteil / 100, 0)} €** "
        f"| Bodenanteil (nicht absetzbar): **{de(kaufpreis * (100 - gebaeude_anteil) / 100, 0)} €**"
    )
else:
    gebaeude_anteil = 80  # Standardwert, für Eigennutzung nicht relevant

st.subheader("Kaufnebenkosten (%)")
with st.expander("ℹ️ Was sind Kaufnebenkosten?", expanded=False):
    st.markdown("""
    | Kostenart | Bayern | Andere Bundesländer |
    |---|---|---|
    | Grunderwerbsteuer | **3,5%** | 5,0–6,5% (NRW, Hessen) |
    | Notar | ~1,5% | ~1,5% |
    | Grundbuch | ~0,5% | ~0,5% |
    | Makler | ~3,57% | 0–3,57% |

    Bei Vermietung sind alle Kaufnebenkosten als Werbungskosten absetzbar (Jahr 1).
    """)

grunderwerbsteuer = st.number_input("Grunderwerbsteuer %", min_value=0.0, max_value=15.0, value=3.5, step=0.1,
                        help="Bayern: 3,5% (2026). Bitte an Ihr Bundesland anpassen.")
notar     = st.number_input("Notar %", min_value=0.0, max_value=10.0, value=1.5, step=0.1,
                        help="Beurkundung + notarielle Leistungen. Ca. 1,0–2,0% des Kaufpreises.")
grundbuch = st.number_input("Grundbuch %", min_value=0.0, max_value=10.0, value=0.5, step=0.1,
                        help="Eintragung ins Grundbuch (Eigentum + Grundschuld). Ca. 0,5%.")
makler    = st.number_input("Makler %", min_value=0.0, max_value=10.0, value=3.57, step=0.01,
                        help="Seit 2020 max. 3,57% je Seite. Bei Direktkauf: 0%.")

nebenkosten_summe  = (kaufpreis + garage) * (grunderwerbsteuer + notar + grundbuch + makler) / 100
gesamtfinanzierung = kaufpreis + garage + invest_bedarf + nebenkosten_summe
darlehen1_summe    = gesamtfinanzierung - eigenkapital

st.caption(
    f"Kaufnebenkosten gesamt: **{de(nebenkosten_summe, 0)} €** "
    f"({grunderwerbsteuer+notar+grundbuch+makler:.2f}%) "
    f"| Gesamtinvestition: **{de(gesamtfinanzierung, 0)} €**"
)

st.subheader("Darlehen")
st.info(f"**Darlehenssumme (automatisch):** {de(darlehen1_summe)} € *(Gesamtinvestition − Eigenkapital)*")

zins1 = st.number_input("Zins (%)", min_value=0.0, max_value=10.0, value=3.5, step=0.05,
            help="Aktueller Bauzins für Ihre Zinsbindungsperiode. Nach Ablauf muss neu verhandelt werden.")

with st.expander("ℹ️ Welchen Tilgungsmodus soll ich wählen?", expanded=False):
    st.markdown("""
    - **Tilgungssatz (%)**: Klassisch. Üblich: 2–3%. Je höher, desto schneller schuldenfrei.
    - **Tilgungsbetrag (€ mtl.)**: Sie kennen Ihre maximale Monatsrate.
    - **Laufzeit (Jahre)**: Sie wissen, bis wann das Darlehen abbezahlt sein soll.

    ⚠️ Die Laufzeit ist eine **Annuitätsberechnung** (mathematisch korrekt).
    Bei 3,5% Zins + 2% Tilgung: ca. **29 Jahre** (nicht 50!).
    """)

tilgung1_modus = st.selectbox("Tilgungsmodus",
    ["Tilgungssatz (%)","Tilgungsbetrag (€ mtl.)","Laufzeit (Jahre)"], index=0)

if tilgung1_modus.startswith("Tilgungssatz"):
    tilgung1 = st.number_input("Tilgung (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.1,
                    help="Anfangstilgungssatz p.a. Empfehlung: mind. 2%.")
    tilg_eur1, laufzeit1 = None, None
elif tilgung1_modus.startswith("Tilgungsbetrag"):
    tilg_eur1 = st.number_input("Tilgung (€ mtl.)", min_value=0, max_value=50000, value=350, step=50,
                    help="Muss höher sein als der monatliche Zinsanteil, sonst tilgen Sie nichts.")
    tilgung1, laufzeit1 = None, None
else:
    laufzeit1 = st.number_input("Laufzeit (Jahre)", min_value=1, max_value=50, value=25, step=1,
                    help="Die monatliche Rate wird automatisch per Annuitätsformel berechnet.")
    tilgung1, tilg_eur1 = None, None

modus_d1 = ('tilgungssatz'  if tilgung1_modus.startswith("Tilgungssatz") else
            'tilgung_euro'  if tilgung1_modus.startswith("Tilgungsbetrag") else 'laufzeit')
d1 = berechne_darlehen_details(darlehen1_summe, zins1,
        tilgung_p=tilgung1, tilgung_euro_mtl=tilg_eur1, laufzeit_jahre=laufzeit1, modus=modus_d1)

st.markdown(f"""
**Darlehen Übersicht:**
- Darlehenssumme: **{de(darlehen1_summe)} €**
- Monatliche Rate: **{de(d1['monatsrate'])} €**
- Laufzeit (Annuität): **{d1['laufzeit_jahre']:.1f} Jahre**
- Tilgungssatz: **{d1['tilgung_p_ergebnis']:.2f} %**
""")
zinsbindung = st.number_input("Zinsbindung (Jahre)", min_value=5, max_value=30, value=10, step=5,
                help="Nach Ablauf der Zinsbindung muss das Darlehen zu dann geltenden Zinsen weitergeführt oder umgeschuldet werden. Üblich: 10–15 Jahre.")
sondertilgung_p = st.number_input("Sondertilgungsrecht (% p.a.)", min_value=0.0, max_value=20.0, value=5.0, step=1.0,
                help="Die meisten Kreditverträge erlauben 5–10% der Darlehenssumme p.a. als Sondertilgung. Erhöht Ihre Flexibilität erheblich.")
if nutzungsart == "Vermietung":
    st.caption(
        f"💡 Sondertilgungspotenzial: bis zu **{de(darlehen1_summe * sondertilgung_p / 100, 0)} €/Jahr**. "
        f"Hinweis: Da Zinsen bei Vermietung steuerlich absetzbar sind, reduziert jede Sondertilgung auch den Steuerabzug — "
        f"der Nettoeffekt ist geringer als bei Eigennutzung, aber Risiko und Zinsbelastung sinken trotzdem."
    )
else:
    st.caption(
        f"💡 Sondertilgungspotenzial: bis zu **{de(darlehen1_summe * sondertilgung_p / 100, 0)} €/Jahr** tilgbar ohne Vorfälligkeitsentschädigung. "
        f"Zinsbindung endet nach **{zinsbindung} Jahren** — dann Anschlussfinanzierung nötig."
    )
st.caption("ℹ️ Laufzeit ≠ Zinsbindung. Nach Ablauf der Zinsbindung muss zu dann geltenden Konditionen neu finanziert werden.")

# ─────────────────────────────────────────────────────────────────────────────
# SEKTION 3: Laufende Posten & Steuer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.header("3. Laufende Posten & Steuer")

with st.expander("ℹ️ Was ist umlagefähig und was nicht?", expanded=False):
    st.markdown("""
    **Umlagefähig** (Mieter zahlt): Heizung, Wasser, Hausmeister, Gebäudeversicherung, Müll.

    **Nicht umlagefähig** (Vermieter trägt): WEG-Verwaltungsgebühr, Instandhaltungsrücklage (WEG-Anteil), Kontoführung, CO2-Steueranteil.

    **Steuerlich absetzbar** bei Vermietung: Zinsen, AfA, Instandhaltung, Verwaltungskosten, Kaufnebenkosten (Jahr 1).
    **Nicht absetzbar**: Tilgung (= Vermögensaufbau).
    """)

if nutzungsart == "Vermietung":
    kaltmiete_monatlich = st.number_input("Kaltmiete mtl. (€)", min_value=0, max_value=10000, value=1000, step=50,
                              help="Nur Kaltmiete — ohne Nebenkosten. Die Nebenkosten werden separat als 'umlagefähig' erfasst.")
    umlagefaehige_monat = st.number_input("Umlagefähige Kosten (€ mtl.)", min_value=0, max_value=1000, value=150, step=10,
                              help="Betriebskosten, die Sie als Vorauszahlung vom Mieter einziehen und weiterleiten. Durchlaufposten.")
    nicht_umlagefaehige_pa = st.number_input("Nicht umlagef. Kosten p.a. (€)", min_value=0, max_value=10000, value=960, step=10,
                              help="WEG-Hausgeldanteil (Verwaltung, Rücklage), Kontoführung etc. Typisch: 80–150 €/Monat.")

    st.subheader("Risikoabschläge (konservative Planung)")
    st.caption("Diese Positionen fehlen in vielen vereinfachten Rechnern — sie sind entscheidend für eine realistische Einschätzung.")

    mietausfallwagnis_p = st.slider("Mietausfallwagnis (% der Jahreskaltmiete)",
                              min_value=0.0, max_value=10.0, value=3.0, step=0.5,
                              help="Puffer für Leerstand bei Mieterwechsel. Standard: 2–4% = ca. 1–2 Monatsleerstand p.a.")
    instandhaltung_qm   = st.slider("Private Instandhaltungsrücklage (€/m²/Monat)",
                              min_value=0.0, max_value=2.0, value=0.75, step=0.25,
                              help="Für wohnungsinternes Sondereigentum (Böden, Bad, Heizung in der Wohnung). Empfehlung: 0,50–1,00 €/m².")
    if kaltmiete_monatlich > 0:
        ausfall_pa      = kaltmiete_monatlich * 12 * mietausfallwagnis_p / 100
        instand_pa      = wohnflaeche_qm * instandhaltung_qm * 12
        st.caption(
            f"→ Mietausfallwagnis p.a.: **{de(ausfall_pa, 0)} €** "
            f"({ausfall_pa / kaltmiete_monatlich:.1f} Monatsmiet.) "
            f"| Priv. Instandhaltung p.a.: **{de(instand_pa, 0)} €**"
        )
else:
    kaltmiete_monatlich, umlagefaehige_monat, mietausfallwagnis_p = 0, 0, 0.0
    nicht_umlagefaehige_pa = st.number_input("Hausgeld p.a. (€)",
                                min_value=0, max_value=50000, value=2400, step=120,
                                help="Hausgeld × 12. Enthält WEG-Verwaltung, Betriebskosten, ggf. Grundsteuer. Typisch: 2,50–4,00 €/m²/Monat.")
    hausgeld_qm = nicht_umlagefaehige_pa / wohnflaeche_qm / 12 if wohnflaeche_qm > 0 else 0
    if hausgeld_qm < 2.0 and nicht_umlagefaehige_pa > 0:
        st.warning(f"⚠️ Das eingegebene Hausgeld entspricht nur {de(hausgeld_qm, 2)} €/m²/Monat — sehr niedrig. Realistisch sind 2,50–4,00 €/m²/Monat (bei {wohnflaeche_qm} m² ca. {de(wohnflaeche_qm * 2.5 * 12, 0)}–{de(wohnflaeche_qm * 4.0 * 12, 0)} €/Jahr).")
    elif hausgeld_qm > 5.0:
        st.info(f"ℹ️ Hausgeld von {de(hausgeld_qm, 2)} €/m²/Monat ist überdurchschnittlich hoch — prüfen Sie, ob eine Sonderumlage enthalten ist.")

    st.subheader("Private Instandhaltungsrücklage (Sondereigentum)")
    st.caption("Für wohnungsinterne Instandhaltung (Bad, Böden, Türen etc.) — zusätzlich zur WEG-Rücklage im Hausgeld.")
    instandhaltung_qm = st.slider("Private Instandhaltungsrücklage (€/m²/Monat)",
                        min_value=0.0, max_value=2.0, value=0.75, step=0.25,
                        help="Empfehlung: 0,50–1,00 €/m² bei älteren Objekten eher 1,00–1,50 €/m².")
    instand_eigen_pa = wohnflaeche_qm * instandhaltung_qm * 12
    st.caption(f"→ Private Instandhaltungsrücklage p.a.: **{de(instand_eigen_pa, 0)} €** ({de(instand_eigen_pa/12, 0)} €/Monat)")

    co2_eigen_pa_calc = (ENERGIEKLASSE_VERBRAUCH.get(energieeffizienz, 100) * wohnflaeche_qm *
                         HEIZUNG_CO2_FAKTOR.get(heizungstyp, 0) / 1000 * CO2_KOST_AUFG_PREIS)
    if jahresverbrauch_kwh and jahresverbrauch_kwh > 0:
        co2_eigen_pa_calc = jahresverbrauch_kwh * HEIZUNG_CO2_FAKTOR.get(heizungstyp, 0) / 1000 * CO2_KOST_AUFG_PREIS

if nutzungsart == "Vermietung":
    steuersatz = st.number_input("Persönl. Grenzsteuersatz (%)", min_value=0.0, max_value=100.0, value=42.0, step=0.5,
                      help="Verwenden Sie Ihren Grenzsteuersatz (nicht Durchschnitt). Bei ~60.000 € Einkommen: ca. 42%.")
else:
    steuersatz = 0.0
    st.info("ℹ️ **Steuerlicher Hinweis (Eigennutzung):** Bei selbstgenutztem Wohneigentum gibt es keine AfA oder steuerliche Absetzbarkeit von Zinskosten. Eine Ausnahme wäre ein häusliches Arbeitszimmer (anteilig, strenge Voraussetzungen) oder eine spätere Teilsanierung zur Vermietung.")
with st.expander("ℹ️ Welchen Steuersatz soll ich eintragen?", expanded=False):
    st.markdown("""
    | Zu verst. Jahreseinkommen | Grenzsteuersatz (ca.) |
    |---|---|
    | bis 11.784 € | 0% |
    | bis ~30.000 € | ~25–30% |
    | bis ~60.000 € | ~35–42% |
    | über 66.761 € | **42%** (Spitzensteuersatz) |
    | über 277.826 € | 45% |

    Mieteinnahmen werden zu Ihrem sonstigen Einkommen addiert. AfA, Zinsen und Kosten mindern den Gewinn — oft entsteht ein steuerlicher **Verlust**, der Ihre Gesamtsteuerlast senkt.
    """)

st.subheader("Persönliche Finanzsituation")
verfuegbares_einkommen = st.number_input("Monatl. verfügbares Einkommen (€)",
                            min_value=0, max_value=100000, value=2500, step=100,
                            help="Ihr aktuelles frei verfügbares Nettoeinkommen. Das Tool zeigt, wie die Immobilie diesen Betrag verändert.")

# ─────────────────────────────────────────────────────────────────────────────
# SEKTION 4: Checkliste
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.header("4. Checkliste: Wichtige Dokumente")

with st.expander("ℹ️ Warum sind diese Dokumente wichtig?", expanded=False):
    st.markdown("""
    | Dokument | Warum wichtig? |
    |---|---|
    | Grundbuchauszug | Lasten, Grundschulden, Wegerechte, Vorkaufsrechte |
    | Teilungserklärung | Definiert Ihr Sondereigentum (Keller, Stellplatz etc.) |
    | WEG-Protokolle (3–5 J.) | Geplante Sanierungen, Streitigkeiten, Sonderumlagen |
    | Jahresabrechnung & Wirtschaftsplan | Tatsächliche vs. geplante Kosten der WEG |
    | Instandhaltungsrücklage | Niedrige Rücklage < 5.000 €/Einheit = Sonderumlagerisiko |
    | Energieausweis | Pflicht beim Verkauf, relevant für CO2-Kosten |
    """)

st.markdown("Haken Sie ab, welche Dokumente Sie bereits haben:")
if 'checklist_status' not in st.session_state:
    st.session_state['checklist_status'] = {}
for i, item in enumerate(checklist_items):
    st.session_state['checklist_status'][item] = st.checkbox(
        item, key=f"check_{item}_{i}",
        value=st.session_state['checklist_status'].get(item, False)
    )
checked_count = sum(st.session_state['checklist_status'].values())
total_count   = len(checklist_items)
if checked_count == total_count:
    st.success(f"✅ Alle {total_count} Dokumente vorhanden — gut vorbereitet!")
elif checked_count >= total_count * 0.6:
    st.warning(f"⚠️ {checked_count}/{total_count} Dokumente vorhanden — noch nicht vollständig.")
else:
    st.error(f"❌ Nur {checked_count}/{total_count} Dokumente vorhanden — bitte anfordern vor der Entscheidung.")

# ─────────────────────────────────────────────────────────────────────────────
# INPUTS-DICT
# ─────────────────────────────────────────────────────────────────────────────
inputs = {
    'wohnort': wohnort, 'baujahr_kategorie': baujahr, 'wohnflaeche_qm': wohnflaeche_qm,
    'stockwerk': stockwerk, 'zimmeranzahl': zimmeranzahl, 'energieeffizienz': energieeffizienz,
    'heizungstyp': heizungstyp,
    'jahresverbrauch_kwh': jahresverbrauch_kwh if jahresverbrauch_kwh > 0 else None,
    'oepnv_anbindung': oepnv_anbindung, 'besonderheiten': besonderheiten,
    'kaufpreis': kaufpreis, 'garage_stellplatz_kosten': garage, 'invest_bedarf': invest_bedarf,
    'eigenkapital': eigenkapital, 'gebaeude_anteil_prozent': gebaeude_anteil,
    'nebenkosten_prozente': {'grunderwerbsteuer': grunderwerbsteuer, 'notar': notar,
                             'grundbuch': grundbuch, 'makler': makler},
    'nutzungsart': nutzungsart, 'zins1_prozent': zins1, 'modus_d1': modus_d1,
    'tilgung1_prozent':  tilgung1  if tilgung1_modus.startswith("Tilgungssatz")    else None,
    'tilgung1_euro_mtl': tilg_eur1 if tilgung1_modus.startswith("Tilgungsbetrag") else None,
    'laufzeit1_jahre':   laufzeit1 if tilgung1_modus.startswith("Laufzeit")        else None,
    'kaltmiete_monatlich': kaltmiete_monatlich, 'umlagefaehige_kosten_monatlich': umlagefaehige_monat,
    'nicht_umlagefaehige_kosten_pa': nicht_umlagefaehige_pa,
    'instand_eigen_pa': instand_eigen_pa if nutzungsart == "Eigennutzung" else 0,
    'co2_eigen_pa': co2_eigen_pa_calc if nutzungsart == "Eigennutzung" else 0,
    'zinsbindung': zinsbindung,
    'sondertilgung_p': sondertilgung_p,
    'mietausfallwagnis_prozent': mietausfallwagnis_p, 'instandhaltung_euro_qm': instandhaltung_qm if nutzungsart == 'Vermietung' else 0,
    'steuersatz': steuersatz, 'verfuegbares_einkommen_mtl': verfuegbares_einkommen,
    'checklist_status': st.session_state['checklist_status']
}

if 'results' not in st.session_state:
    st.session_state['results'] = None

st.markdown("---")
if st.button("🔍 Analyse berechnen", type="primary"):
    st.session_state['results'] = calculate_analytics(inputs)

results = st.session_state['results']

# ─────────────────────────────────────────────────────────────────────────────
# ERGEBNISSE
# ─────────────────────────────────────────────────────────────────────────────
if results:
    st.markdown("---")
    st.header("5. Ergebnisse")

    if nutzungsart == "Vermietung":
        cf_vor  = next((r['val2'] for r in results['display_table'] if '= Cashflow vor Steuern'  in r['kennzahl']), 0)
        cf_nach = next((r['val2'] for r in results['display_table'] if '= Effektiver Cashflow'   in r['kennzahl']), 0)
        nve     = next((r['val2'] for r in results['display_table'] if '= Neues verfügbares'      in r['kennzahl']), 0)
        diff    = nve - verfuegbares_einkommen

        st.subheader("📊 Schnellübersicht")
        m1, m2, m3 = st.columns(3)
        m1.metric("Cashflow vor Steuern (lfd.)",  f"{de(cf_vor/12, 0)} €/Monat",
                  delta=f"{de(cf_vor, 0)} €/Jahr")
        m2.metric("Cashflow nach Steuern (lfd.)", f"{de(cf_nach/12, 0)} €/Monat",
                  delta=f"{de(cf_nach, 0)} €/Jahr")
        m3.metric("Neues monatl. Verfügbares",    f"{de(nve, 0)} €/Monat",
                  delta=f"{'+' if diff >= 0 else ''}{de(diff, 0)} € vs. heute")

        if cf_nach >= 0:
            st.success(f"✅ **Cashflow-positiv nach Steuern** (lfd. Jahre: +{de(cf_nach/12, 0)} €/Monat).")
        elif cf_vor < 0:
            st.error(
                f"❌ **Cashflow negativ — auch vor Steuern.** "
                f"Zuzahlung: {de(abs(cf_vor/12), 0)} €/Monat. "
                "Kaufpreis, Mietansatz oder Finanzierung prüfen."
            )
        else:
            st.warning(
                f"⚠️ **Vor Steuern negativ, nach Steuern: {de(cf_nach/12, 0)} €/Monat.** "
                "Typisches Steuersparer-Modell — hängt von Ihrer Einkommenssituation ab."
            )

    # --- Detailtabelle ---
    st.subheader("Detaillierte Cashflow-Rechnung")

    if nutzungsart == "Vermietung":
        all_keys = [
            "Einnahmen p.a. (Kaltmiete)", "Umlagefähige Kosten p.a.", "Nicht umlagef. Kosten p.a.",
            "- Mietausfallwagnis p.a.", "- Priv. Instandhaltungsrücklage p.a.",
            "- CO2-Steuer Vermieteranteil p.a.", "Rückzahlung Darlehen p.a.", "- Zinsen p.a.",
            "Jährliche Gesamtkosten", "= Cashflow vor Steuern p.a.",
            "- AfA p.a.", "- Absetzbare Kaufnebenkosten (Jahr 1)",
            "= Steuerlicher Gewinn/Verlust p.a.", "+ Steuerersparnis / -last p.a.",
            "= Effektiver Cashflow n. St. p.a.", "Ihr monatl. Einkommen (vorher)",
            "+/- Mtl. Cashflow Immobilie", "= Neues verfügbares Einkommen"
        ]
    else:
        all_keys = [
            "Hausgeld / Betriebskosten p.a.", "- Private Instandhaltungsrücklage p.a.",
            "- CO2-Kosten (Eigennutzer) p.a.", "Rückzahlung Darlehen p.a.", "- Zinsen p.a.",
            "- Tilgung p.a. (Vermögensaufbau)", "Jährliche Gesamtkosten (inkl. Tilgung)",
            "Ihr monatl. Einkommen (vorher)", "- Mtl. Kosten Immobilie", "= Neues verfügbares Einkommen"
        ]

    col1, col2 = st.columns(2)
    for col, val_key, titel in [(col1, 'val1', "#### Jahr der Anschaffung (€)"),
                                 (col2, 'val2', "#### Laufende Jahre (€)")]:
        with col:
            st.markdown(titel)
            for key in all_keys:
                val = next((r[val_key] for r in results['display_table'] if key in r['kennzahl']), "")
                if val != "":
                    is_bold = key.startswith("=") or "+ Steuerersparnis" in key
                    style   = "font-weight:bold; font-size:1.05em;" if is_bold else ""
                    color   = ("color:green;" if is_number(val) and float(val) > 0 and key.startswith("=") else
                               "color:red;"   if is_number(val) and float(val) < 0 and key.startswith("=") else "")
                    st.markdown(
                        f"<div style='{style}{color}'>{key}: {format_eur(val) if is_number(val) else val}</div>",
                        unsafe_allow_html=True
                    )

    # --- Eigennutzung: Zusatzinfos ---
    if nutzungsart == "Eigennutzung" and results.get('finanzkennzahlen'):
        fk = results['finanzkennzahlen']
        tilgung_pa = fk.get('tilgung_pa', 0)
        zinsen_pa  = fk.get('zinsen_pa', 0)
        reine_wk   = fk.get('reine_wohnkosten_pa', 0)

        st.subheader("🏦 Vermögensaufbau durch Tilgung")
        _info_msg = (
            f"💡 Von Ihrer monatlichen Rate von **{de(d1['monatsrate'], 0)} €** sind im 1. Jahr:\n"
            f"- **{de(zinsen_pa/12, 0)} €/Monat** Zinsen (= Kosten, nicht rückgewinnbar)\n"
            f"- **{de(tilgung_pa/12, 0)} €/Monat** Tilgung (= Vermögensaufbau / Eigenkapitalzuwachs)\n\n"
            f"Reine 'Wohnkosten' ohne Tilgung (Zins + Betrieb + Instandh. + CO2): **{de(reine_wk/12, 0)} €/Monat**"
        )
        st.info(_info_msg)

        laufzeit_j = d1['laufzeit_jahre']
        ek_nach_10j = eigenkapital + tilgung_pa * 10
        st.caption(f"📈 Geschätztes Eigenkapital nach 10 Jahren (nur Tilgung, ohne Wertsteigerung): **{de(ek_nach_10j, 0)} €**")

        st.subheader("⚖️ Kaufen vs. Mieten+Investieren (Opportunity Cost)")
        with st.expander("ℹ️ Was ist der Opportunity-Cost-Vergleich?", expanded=True):
            st.markdown("""
            Der wichtigste Vergleich bei Eigennutzung: Was wäre, wenn Sie **weiter mieten** und die
            Differenz (Eigenkapital + monatliche Mehrkosten) am Kapitalmarkt anlegen würden?

            **Annahmen für den Vergleich:**
            - Kapitalmarktrendite (ETF): 6% p.a. (historischer Ø MSCI World nach Inflation ~5–7%)
            - Immobilienwertentwicklung: 2% p.a. (konservativ für Nürnberg)
            """)

        vergleichsmiete = st.number_input("Vergleichsmiete (€/mtl. Kaltmiete für gleichwertige Wohnung)",
                            min_value=0, max_value=5000, value=int(wohnflaeche_qm * 12),
                            step=50, key="vergleichsmiete",
                            help="Was würden Sie für eine gleichwertige Mietwohnung zahlen? Basis für den Opportunitätskostenvergleich.")

        etf_rendite = 0.06
        immo_wertzuwachs = 0.02
        jahre = 20

        monatliche_immo_kosten = jaehrliche_kosten_display = (
            results['finanzkennzahlen'].get('reine_wohnkosten_pa', 0) + (d1['monatsrate'] * 12)
        ) / 12
        monatliche_immo_kosten = next(
            (r['val2'] for r in results['display_table'] if '- Mtl. Kosten Immobilie' in r['kennzahl']), 0
        )
        monatliche_immo_kosten = abs(float(monatliche_immo_kosten)) if monatliche_immo_kosten else d1['monatsrate']

        mtl_differenz = monatliche_immo_kosten - vergleichsmiete

        # Szenario Kaufen: Immobilienwert nach X Jahren
        immo_wert_20j = kaufpreis * (1 + immo_wertzuwachs) ** jahre
        restschuld_20j = darlehen1_summe * ((1 + zins1/100/12)**(jahre*12) - 1) / ((1 + zins1/100/12)**(d1['laufzeit_jahre']*12) - 1) if d1['laufzeit_jahre'] > 0 else 0
        nettoverm_kaufen = immo_wert_20j - max(restschuld_20j, 0)

        # Szenario Mieten: EK + mtl. Differenz in ETF
        etf_monatlich = max(mtl_differenz, 0)
        etf_wert_20j  = eigenkapital * (1 + etf_rendite)**jahre + etf_monatlich * 12 * (((1+etf_rendite)**jahre - 1) / etf_rendite) if etf_rendite > 0 else eigenkapital + etf_monatlich * 12 * jahre

        col_k, col_m = st.columns(2)
        col_k.metric("🏠 Kaufen — Nettovermögen nach 20 J.", f"{de(nettoverm_kaufen, 0)} €",
                     delta=f"Immo-Wert: {de(immo_wert_20j, 0)} € − Restschuld: {de(max(restschuld_20j,0), 0)} €")
        col_m.metric("📈 Mieten+ETF — Depotwert nach 20 J.", f"{de(etf_wert_20j, 0)} €",
                     delta=f"EK ({de(eigenkapital, 0)} €) + {de(etf_monatlich, 0)} €/Monat @ 6% p.a." if mtl_differenz >= 0 else "Kauf ist günstiger als Miete — Mieter hat weniger übrig")
        st.caption("⚠️ Vereinfachte Modellrechnung ohne Steuern, Inflationsanpassung, Mietsteigerungen oder Sonderumlagen. Dient nur zur Orientierung.")

    # --- Renditekennzahlen ---
    if nutzungsart == "Vermietung" and results.get('finanzkennzahlen'):
        st.subheader("📈 Finanzkennzahlen & Einordnung")
        with st.expander("ℹ️ Was bedeuten diese Kennzahlen?", expanded=False):
            st.markdown("""
            | Kennzahl | Formel | Gut | Okay | Schwach |
            |---|---|---|---|---|
            | **Bruttomietrendite** | Jahreskaltmiete / Gesamtinvestition | > 5% | 4–5% | < 4% |
            | **Eigenkapitalrendite** | Cashflow n.St. / Eigenkapital | > 10% | 5–10% | < 5% |

            **Ø Bruttomietrendite Deutschland (Feb. 2026): ~4,1%**
            ⚠️ Die Eigenkapitalrendite berücksichtigt nur den Cashflow, nicht den Vermögensaufbau durch Tilgung.
            """)

        for k, v in results['finanzkennzahlen'].items():
            val_f = float(v)
            if "bruttomietrendite" in k.lower():
                if val_f >= 5:
                    st.success(f"✅ **{k}:** {format_percent(v)} — gut (Ø DE: ~4,1%)")
                elif val_f >= 4:
                    st.warning(f"⚠️ **{k}:** {format_percent(v)} — im Durchschnitt (Ø DE: ~4,1%)")
                else:
                    st.error(f"❌ **{k}:** {format_percent(v)} — unter Durchschnitt (Ø DE: ~4,1%)")
            elif "eigenkapitalrendite" in k.lower():
                if val_f >= 10:
                    st.success(f"✅ **{k}:** {format_percent(v)} — gut (Richtwert: >10%)")
                elif val_f >= 5:
                    st.warning(f"⚠️ **{k}:** {format_percent(v)} — akzeptabel (Richtwert: >10%)")
                else:
                    st.error(f"❌ **{k}:** {format_percent(v)} — schwach (Richtwert: >10%)")

    # --- PDF Export ---
    st.markdown("---")
    if st.button("📄 PDF-Bericht erstellen"):
        try:
            pdf_bytes = create_pdf_report(results, inputs, checklist_items)
            st.success("PDF erfolgreich erstellt!")
            st.download_button(
                label="⬇️ PDF-Bericht herunterladen",
                data=pdf_bytes,
                file_name=f"Immobilien_Analyse_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Fehler beim Erstellen des PDFs: {str(e)}")
