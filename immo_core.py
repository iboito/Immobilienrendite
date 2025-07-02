# immo_core.py

import configparser
import math
import matplotlib.pyplot as plt

def load_config():
    """
    Lädt Standardwerte aus config.txt (Section DefaultValues).
    Falls nicht vorhanden, werden Fallback-Werte zurückgegeben.
    """
    config = configparser.ConfigParser()
    try:
        config.read('config.txt')
        return config['DefaultValues']
    except (configparser.NoSectionError, FileNotFoundError):
        return {
            'grunderwerbsteuer_prozent': '3.5',
            'notar_prozent': '1.5',
            'grundbuch_prozent': '0.5',
            'makler_prozent': '3.57'
        }

def berechne_darlehen_details(summe, zins_p,
                              tilgung_p=None,
                              tilgung_euro_mtl=None,
                              laufzeit_jahre=None,
                              modus='tilgungssatz'):
    """
    Berechnet für ein Darlehen:
    - Zinsen p.a.
    - Tilgung p.a.
    - Monatsrate
    - Laufzeit in Jahren (falls nach Laufzeit berechnet)
    - Effektiver Tilgungssatz p.a.
    - Effektive Tilgung in Euro p.a.
    """
    if summe <= 0:
        return {
            'zins_pa': 0, 'tilgung_pa': 0,
            'monatsrate': 0, 'laufzeit_jahre': 0,
            'tilgung_p_ergebnis': 0, 'tilgung_euro_ergebnis_pa': 0
        }

    zins_pa = summe * (zins_p / 100)
    mon_zins = zins_p / 100 / 12
    tilgung_pa = 0
    laufzeit_ergebnis = float('inf')

    if modus == 'tilgungssatz' and tilgung_p is not None:
        tilgung_pa = summe * (tilgung_p / 100)
    elif modus == 'tilgung_euro' and tilgung_euro_mtl is not None:
        tilgung_pa = tilgung_euro_mtl * 12
    elif modus == 'laufzeit' and laufzeit_jahre and laufzeit_jahre > 0:
        if zins_p > 0 and mon_zins > 0:
            n_monate = laufzeit_jahre * 12
            try:
                faktor = (mon_zins * (1 + mon_zins)**n_monate) / ((1 + mon_zins)**n_monate - 1)
                monatsrate_calc = summe * faktor
                tilgung_pa = (monatsrate_calc * 12) - zins_pa
            except OverflowError:
                tilgung_pa = 0
        else:
            tilgung_pa = summe / laufzeit_jahre

    monatsrate = (zins_pa + tilgung_pa) / 12

    if mon_zins > 0 and monatsrate > (summe * mon_zins):
        try:
            laufzeit_ergebnis = -math.log(1 - (summe * mon_zins) / monatsrate) / math.log(1 + mon_zins) / 12
        except (ValueError, ZeroDivisionError):
            laufzeit_ergebnis = float('inf')
    elif mon_zins == 0 and monatsrate > 0:
        laufzeit_ergebnis = summe / (monatsrate * 12)

    tilgung_p_ergebnis = (tilgung_pa / summe) * 100 if summe > 0 else 0

    return {
        'zins_pa': zins_pa,
        'tilgung_pa': tilgung_pa,
        'monatsrate': monatsrate,
        'laufzeit_jahre': laufzeit_ergebnis,
        'tilgung_p_ergebnis': tilgung_p_ergebnis,
        'tilgung_euro_ergebnis_pa': tilgung_pa
    }

def calculate_analytics(inputs):
    """
    Führt die vollständige Analyse durch und liefert:
    - display_table: Liste von Dicts für GUI/PDF mit Kennzahl, val1, val2, tags
    - kpi_table: Liste von Dicts für KPI-Anzeige
    - pie_data: Dict für Tortendiagramm
    - bar_data: Dict für Balkendiagramm
    - gesamtinvestition: Gesamtinvestitionsbetrag
    """
    # Basisdaten
    kaufpreis = inputs.get('kaufpreis', 0)
    if kaufpreis == 0:
        return {'error': 'Kaufpreis darf nicht 0 sein.'}

    garage = inputs.get('garage_stellplatz_kosten', 0)
    invest_bedarf = inputs.get('invest_bedarf', 0)
    nebenkosten_prozente = inputs.get('nebenkosten_prozente', {})
    kauf_basis = kaufpreis + garage
    gesamte_nebenkosten = kauf_basis * sum(nebenkosten_prozente.values()) / 100
    gesamtinvestition = kauf_basis + gesamte_nebenkosten + invest_bedarf
    eigenkapital = inputs.get('eigenkapital', 0)
    darlehensbedarf = gesamtinvestition - eigenkapital

    # Darlehen I und II
    inputs['darlehen1_summe'] = darlehensbedarf
    d1 = berechne_darlehen_details(
        inputs['darlehen1_summe'], inputs.get('zins1_prozent', 0),
        inputs.get('tilgung1_prozent'), inputs.get('tilgung1_euro_mtl'),
        inputs.get('laufzeit1_jahre'), inputs.get('modus_d1')
    )
    d2 = berechne_darlehen_details(
        inputs.get('darlehen2_summe', 0), inputs.get('zins2_prozent', 0),
        inputs.get('tilgung2_prozent'), inputs.get('tilgung2_euro_mtl'),
        inputs.get('laufzeit2_jahre'), inputs.get('modus_d2')
    )

    zinsen_pa = d1['zins_pa'] + d2['zins_pa']
    tilgung_pa = d1['tilgung_pa'] + d2['tilgung_pa']
    bankrate_pa = zinsen_pa + tilgung_pa

    nutzungsart = inputs.get('nutzungsart', 'Vermietung')
    nicht_umlagefaehige = inputs.get('nicht_umlagefaehige_kosten_pa', 0)
    verfuegbares_einkommen = inputs.get('verfuegbares_einkommen_mtl', 0)

    display_table = []
    kpi_table = []
    pie_data = {
        'Darlehen I': inputs['darlehen1_summe'],
        'Darlehen II': inputs.get('darlehen2_summe', 0),
        'Eigenkapital': eigenkapital
    }
    bar_data = {}

    if nutzungsart == 'Vermietung':
        # AfA-Satz ermitteln
        baujahr = inputs.get('baujahr_kategorie', '1925 - 2022')
        afa_satz = 2.5 if baujahr == 'vor 1925' else 3.0 if baujahr == 'ab 2023' else 2.0

        kaltmiete_pa = inputs.get('kaltmiete_monatlich', 0) * 12
        cashflow_vor_steuern = kaltmiete_pa - nicht_umlagefaehige - bankrate_pa
        afa_pa = kaufpreis * (afa_satz / 100)
        laufende_werbung = zinsen_pa + nicht_umlagefaehige + afa_pa
        gewinn_jahr1 = kaltmiete_pa - (laufende_werbung + gesamte_nebenkosten)
        gewinn_laufend = kaltmiete_pa - laufende_werbung
        steuer_jahr1 = -gewinn_jahr1 * (inputs.get('steuersatz', 42.0) / 100)
        steuer_laufend = -gewinn_laufend * (inputs.get('steuersatz', 42.0) / 100)
        cashflow_n_st_jahr1 = cashflow_vor_steuern + steuer_jahr1
        cashflow_n_st_laufend = cashflow_vor_steuern + steuer_laufend
        neues_einkommen = verfuegbares_einkommen + (cashflow_n_st_laufend / 12)

        # Anzeige-Tabelle aufbauen
        display_table.extend([
            {'kennzahl': 'Cashflow-Rechnung (Ihr Konto)', 'val1': None, 'val2': None, 'tags': ['title']},
            {'kennzahl': ' Einnahmen p.a. (Kaltmiete)', 'val1': kaltmiete_pa, 'val2': kaltmiete_pa, 'tags': []},
            {'kennzahl': ' - Nicht umlagef. Kosten p.a.', 'val1': -nicht_umlagefaehige, 'val2': -nicht_umlagefaehige, 'tags': []},
            {'kennzahl': ' - Rückzahlung Darlehen p.a.', 'val1': -bankrate_pa, 'val2': -bankrate_pa, 'tags': []},
            {'kennzahl': ' = Cashflow vor Steuern p.a.', 'val1': cashflow_vor_steuern, 'val2': cashflow_vor_steuern, 'tags': ['bold']},
            {'kennzahl': '---', 'val1': None, 'val2': None, 'tags': ['separator']},
            {'kennzahl': 'Steuer-Rechnung (Finanzamt)', 'val1': None, 'val2': None, 'tags': ['title']},
            {'kennzahl': ' - Zinsen p.a.', 'val1': -zinsen_pa, 'val2': -zinsen_pa, 'tags': []},
            {'kennzahl': ' - AfA p.a.', 'val1': -afa_pa, 'val2': -afa_pa, 'tags': []},
            {'kennzahl': ' - Absetzbare Kaufnebenkosten (Jahr 1)', 'val1': -gesamte_nebenkosten, 'val2': 0, 'tags': []},
            {'kennzahl': ' = Steuerlicher Gewinn/Verlust p.a.', 'val1': gewinn_jahr1, 'val2': gewinn_laufend, 'tags': ['bold']},
            {'kennzahl': '---', 'val1': None, 'val2': None, 'tags': ['separator']},
            {'kennzahl': 'Finale Ergebnisse', 'val1': None, 'val2': None, 'tags': ['title']},
            {'kennzahl': ' + Steuerersparnis / -last p.a.', 'val1': steuer_jahr1, 'val2': steuer_laufend, 'tags': ['bold', 'green_text' if steuer_laufend >= 0 else 'red_text']},
            {'kennzahl': ' = Effektiver Cashflow n. St. p.a.', 'val1': cashflow_n_st_jahr1, 'val2': cashflow_n_st_laufend, 'tags': ['bold']},
            {'kennzahl': '---', 'val1': None, 'val2': None, 'tags': ['separator']},
            {'kennzahl': 'Gesamt-Cashflow (Ihre persönliche Situation)', 'val1': None, 'val2': None, 'tags': ['title']},
            {'kennzahl': ' Ihr monatl. Einkommen (vorher)', 'val1': None, 'val2': verfuegbares_einkommen, 'tags': []},
            {'kennzahl': ' +/- Mtl. Cashflow Immobilie', 'val1': None, 'val2': cashflow_n_st_laufend / 12, 'tags': []},
            {'kennzahl': ' = Neues verfügbares Einkommen', 'val1': None, 'val2': neues_einkommen, 'tags': ['bold', 'green_text' if neues_einkommen >= verfuegbares_einkommen else 'red_text']}
        ])

        # KPIs
        bruttomietrendite = (kaltmiete_pa / kaufpreis) * 100
        nettomietrendite = ((kaltmiete_pa - nicht_umlagefaehige) / gesamtinvestition) * 100
        ek_rendite = (cashflow_n_st_laufend / eigenkapital) * 100 if eigenkapital > 0 else 0
        kpi_table = [
            {'Kennzahl': 'Bruttomietrendite', 'Wert': f"{bruttomietrendite:.2f} %"},
            {'Kennzahl': 'Nettomietrendite', 'Wert': f"{nettomietrendite:.2f} %"},
            {'Kennzahl': 'EK-Rendite n.St. (laufend)', 'Wert': f"{ek_rendite:.2f} %"}
        ]

        # Balkendiagramm-Daten
        bar_data = {
            'Nettokaltmiete': kaltmiete_pa / 12,
            'Zinsen': zinsen_pa / 12,
            'Tilgung': tilgung_pa / 12,
            'Bewirt.-Kosten': nicht_umlagefaehige / 12
        }

    else:  # Eigennutzung
        jaehrliche_kosten = bankrate_pa + nicht_umlagefaehige
        neues_einkommen = verfuegbares_einkommen - (jaehrliche_kosten / 12)

        display_table.extend([
            {'kennzahl': 'Rückzahlung Darlehen p.a.', 'val1': -bankrate_pa, 'val2': -bankrate_pa, 'tags': []},
            {'kennzahl': 'Laufende Kosten p.a.', 'val1': -nicht_umlagefaehige, 'val2': -nicht_umlagefaehige, 'tags': []},
            {'kennzahl': '---', 'val1': None, 'val2': None, 'tags': ['separator']},
            {'kennzahl': 'Jährliche Gesamtkosten', 'val1': -jaehrliche_kosten, 'val2': -jaehrliche_kosten, 'tags': ['bold']},
            {'kennzahl': '---', 'val1': None, 'val2': None, 'tags': ['separator']},
            {'kennzahl': 'Gesamt-Cashflow (Ihre persönliche Situation)', 'val1': None, 'val2': None, 'tags': ['title']},
            {'kennzahl': ' Ihr monatl. Einkommen (vorher)', 'val1': None, 'val2': verfuegbares_einkommen, 'tags': []},
            {'kennzahl': ' - Mtl. Kosten Immobilie', 'val1': None, 'val2': -jaehrliche_kosten / 12, 'tags': []},
            {'kennzahl': ' = Neues verfügbares Einkommen', 'val1': None, 'val2': neues_einkommen, 'tags': ['bold', 'green_text' if neues_einkommen >= verfuegbares_einkommen else 'red_text']}
        ])

        # KPIs
        kpi_table = [
            {'Kennzahl': 'Gesamtinvestition', 'Wert': f"{gesamtinvestition:,.2f} €"},
            {'Kennzahl': 'Benötigtes EK', 'Wert': f"{gesamtinvestition - (inputs['darlehen1_summe'] + inputs.get('darlehen2_summe', 0)):,.2f} €"}
        ]

        bar_data = {
            'Nettokaltmiete': 0,
            'Zinsen': zinsen_pa / 12,
            'Tilgung': tilgung_pa / 12,
            'Bewirt.-Kosten': nicht_umlagefaehige / 12
        }

    # Ergebnis zusammenstellen
    return {
        'display_table': display_table,
        'kpi_table': kpi_table,
        'pie_data': pie_data,
        'bar_data': bar_data,
        'gesamtinvestition': gesamtinvestition
    }

# Helper-Funktionen für Streamlit/Charts

def plt_pie(labels, sizes, ret_fig=False):
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.set_title("Finanzierungsstruktur")
    if ret_fig:
        return fig
    else:
        return plt

def plt_bar(data, ret_fig=False):
    fig, ax = plt.subplots()
    ax.bar("Einnahmen", data.get('Nettokaltmiete', 0), color='green', label='Nettokaltmiete')
    bottom = 0
    colors = ['#C0504D', '#F79646', '#8064A2']
    labels = ['Bewirt.-Kosten', 'Zinsen', 'Tilgung']
    for color, label in zip(colors, labels):
        val = -data.get(label.replace('-', '_').replace('.', '_'), 0)
        ax.bar("Ausgaben", val, bottom=bottom, color=color, label=label)
        bottom += val
    ax.set_title("Monatlicher Cashflow")
    ax.legend()
    if ret_fig:
        return fig
    else:
        return plt
