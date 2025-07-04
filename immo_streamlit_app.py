def create_pdf_report(results, inputs, checklist_items):
    pdf = FPDF()
    pdf.add_page()
    
    # Verwende nur ASCII-kompatible Zeichen
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, "Finanzanalyse Immobilieninvestment", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Bericht erstellt am: {datetime.now().strftime('%d.%m.%Y')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"Analyse fuer Objekt in: {inputs.get('wohnort','')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    
    # Korrigierte format_eur Funktion für PDF
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
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "1. Objekt- & Investmentuebersicht", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Arial", "", 10)
    
    immotable = [
        ("Baujahr:", inputs.get('baujahr_kategorie', '')),
        ("Wohnflaeche (qm):", str(inputs.get('wohnflaeche_qm', ''))),
        ("Zimmeranzahl:", str(inputs.get('zimmeranzahl', ''))),
        ("Stockwerk:", str(inputs.get('stockwerk', ''))),
        ("Energieeffizienz:", str(inputs.get('energieeffizienz', ''))),
        ("OEPNV-Anbindung:", str(inputs.get('oepnv_anbindung', ''))),
        ("Besonderheiten:", str(inputs.get('besonderheiten', ''))),
        ("Kaufpreis:", format_eur_pdf(inputs.get('kaufpreis', 0))),
        ("Garage/Stellplatz:", format_eur_pdf(inputs.get('garage_stellplatz_kosten', 0))),
        ("Investitionsbedarf:", format_eur_pdf(inputs.get('invest_bedarf', 0))),
    ]
    
    nebenkosten_summe = (inputs.get('kaufpreis',0) + inputs.get('garage_stellplatz_kosten',0)) * sum(inputs.get('nebenkosten_prozente',{}).values())/100
    immotable.append(("Kaufnebenkosten:", format_eur_pdf(nebenkosten_summe)))
    
    gesamtinvest = inputs.get('kaufpreis',0)+inputs.get('garage_stellplatz_kosten',0)+inputs.get('invest_bedarf',0)+nebenkosten_summe
    immotable.append(("Gesamtinvestition:", format_eur_pdf(gesamtinvest)))
    
    for k, v in immotable:
        pdf.cell(65, 7, k, border=0)
        pdf.cell(40, 7, str(v), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(2)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2. Finanzierungsstruktur & Darlehensdetails", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Arial", "", 10)
    
    ek = inputs.get('eigenkapital',0)
    fk = gesamtinvest - ek
    pdf.cell(65, 7, "Eigenkapital:", border=0)
    pdf.cell(40, 7, format_eur_pdf(ek), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(65, 7, "Fremdkapital (Darlehen):", border=0)
    pdf.cell(40, 7, format_eur_pdf(fk), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    d1 = berechne_darlehen_details(
        fk,
        inputs.get('zins1_prozent',0),
        tilgung_p=inputs.get('tilgung1_prozent',None),
        tilgung_euro_mtl=inputs.get('tilgung1_euro_mtl',None),
        laufzeit_jahre=inputs.get('laufzeit1_jahre',None),
        modus=inputs.get('modus_d1','tilgungssatz')
    )
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, "Darlehen:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Arial", "", 10)
    pdf.cell(65, 7, "Zinssatz (%):", border=0)
    pdf.cell(40, 7, format_percent_pdf(inputs.get('zins1_prozent', '')), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(65, 7, "Tilgungssatz (%):", border=0)
    
    tilgung1 = inputs.get('tilgung1_prozent', '') or ""
    if tilgung1 == "" and inputs.get('tilgung1_euro_mtl'):
        tilgung1 = f"{inputs.get('tilgung1_euro_mtl')} EUR mtl."
    pdf.cell(40, 7, str(tilgung1), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    laufzeit_anzeige = inputs.get('laufzeit1_jahre')
    if not laufzeit_anzeige or laufzeit_anzeige in [None, '', 0]:
        laufzeit_anzeige = f"{d1.get('laufzeit_jahre',''):.1f}" if d1.get('laufzeit_jahre') else ""
    pdf.cell(65, 7, "Laufzeit (Jahre):", border=0)
    pdf.cell(40, 7, str(laufzeit_anzeige), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(65, 7, "Monatsrate (EUR):", border=0)
    pdf.cell(40, 7, format_eur_pdf(d1.get('monatsrate', '')), border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(2)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "3. Detailrechnung & Persoenlicher Cashflow", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(80, 7, "Kennzahl", border=1)
    pdf.cell(35, 7, "Jahr 1 (EUR)", border=1)
    pdf.cell(35, 7, "Laufende Jahre (EUR)", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Arial", "", 10)
    
    if inputs.get("nutzungsart") == "Vermietung":
        all_keys = [
            "Einnahmen p.a. (Kaltmiete)",
            "Umlagefaehige Kosten p.a.",
            "Nicht umlagef. Kosten p.a.",
            "Rueckzahlung Darlehen p.a.",
            "- Zinsen p.a.",
            "Jaehrliche Gesamtkosten",
            "= Cashflow vor Steuern p.a.",
            "- AfA p.a.",
            "- Absetzbare Kaufnebenkosten (Jahr 1)",
            "= Steuerlicher Gewinn/Verlust p.a.",
            "+ Steuerersparnis / -last p.a.",
            "= Effektiver Cashflow n. St. p.a.",
            "Gesamt-Cashflow (Ihre persoenliche Si)",
            "Ihr monatl. Einkommen (vorher)",
            "- Mtl. Kosten Immobilie",
            "= Neues verfuegbares Einkommen"
        ]
    else:
        all_keys = [
            "Laufende Kosten p.a.",
            "Rueckzahlung Darlehen p.a.",
            "- Zinsen p.a.",
            "Jaehrliche Gesamtkosten",
            "Gesamt-Cashflow (Ihre persoenliche Si)",
            "Ihr monatl. Einkommen (vorher)",
            "- Mtl. Kosten Immobilie",
            "= Neues verfuegbares Einkommen"
        ]
    
    for key in all_keys:
        row = next((r for r in results['display_table'] if key.replace("ue", "ü").replace("oe", "ö").replace("ae", "ä") in r['kennzahl']), None)
        if row:
            kennzahl = str(row.get('kennzahl', ''))
            # Ersetze Umlaute für PDF
            kennzahl = kennzahl.replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ß", "ss")
            val1_raw = row.get('val1', '')
            val2_raw = row.get('val2', '')
            
            try:
                val1 = format_eur_pdf(val1_raw) if is_number(val1_raw) else str(val1_raw) if val1_raw not in [None, "None"] else ""
            except Exception:
                val1 = ""
            
            try:
                val2 = format_eur_pdf(val2_raw) if is_number(val2_raw) else str(val2_raw) if val2_raw not in [None, "None"] else ""
            except Exception:
                val2 = ""
            
            pdf.cell(80, 7, kennzahl, border=1)
            pdf.cell(35, 7, val1, border=1)
            pdf.cell(35, 7, val2, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
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
                v = format_percent_pdf(v)
            pdf.cell(80, 7, k, border=1)
            pdf.cell(35, 7, str(v), border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(3)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "5. Checkliste: Wichtige Dokumente", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Arial", "", 10)
    
    checklist_status = inputs.get("checklist_status", {})
    for item in checklist_items:
        checked = checklist_status.get(item, False)
        box = "X" if checked else " "
        # Ersetze Umlaute für PDF
        item_clean = item.replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ß", "ss")
        pdf.cell(0, 7, f"[{box}] {item_clean}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    result = pdf.output()
    if isinstance(result, bytearray):
        return bytes(result)
    return result
