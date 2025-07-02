# pdf_generator.py

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors

def fig_to_image(fig):
    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=300, bbox_inches='tight'); buf.seek(0)
    return Image(buf, width=450, height=280)

def create_bank_report(data, filepath):
    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet(); styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT)); styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    story = []
    
    story.append(Paragraph("Finanzanalyse Immobilieninvestment", styles['h1'])); story.append(Spacer(1, 24))
    story.append(Paragraph(f"Bericht erstellt am: {datetime.now().strftime('%d.%m.%Y')}", styles['Right']))
    story.append(Paragraph(f"Analyse für Objekt in: {data['inputs'].get('wohnort', 'N/A')}", styles['Normal'])); story.append(Spacer(1, 24))

    story.append(Paragraph("1. Objekt- & Investmentübersicht", styles['h2'])); story.append(Spacer(1, 12))
    invest_data = [
        ["Kaufpreis:", f"{data['inputs']['kaufpreis']:,.2f} €"],
        ["Garage/Stellplatz:", f"{data['inputs']['garage_stellplatz_kosten']:,.2f} €"],
        ["Investitionsbedarf:", f"{data['inputs']['invest_bedarf']:,.2f} €"],
        ["Kaufnebenkosten:", f"{data['gesamtinvestition'] - data['inputs']['kaufpreis'] - data['inputs']['garage_stellplatz_kosten'] - data['inputs']['invest_bedarf']:,.2f} €"],
        [Paragraph("<b>Gesamtinvestition:</b>", styles['Normal']), Paragraph(f"<b>{data['gesamtinvestition']:,.2f} €</b>", styles['Right'])],
    ]
    invest_table = Table(invest_data, colWidths=[200, 250]); invest_table.setStyle(TableStyle([('ALIGN', (1,0), (1,-1), 'RIGHT'), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0, 4), (-1, 4), colors.lightgrey)])); story.append(invest_table); story.append(Spacer(1, 24))

    story.append(Paragraph("2. Finanzierungsstruktur", styles['h2'])); story.append(Spacer(1, 12)); story.append(fig_to_image(data['figures']['pie'])); story.append(PageBreak())

    story.append(Paragraph("3. Detailrechnung & Persönlicher Cashflow", styles['h2'])); story.append(Spacer(1, 12))
    
    # *** HIER IST DIE VEREINFACHTE PDF-LOGIK ***
    table_data = [["Kennzahl", "Jahr 1 (€)", "Laufende Jahre (€)"]]
    style_commands = [('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('ALIGN', (1,1), (-1,-1), 'RIGHT'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0,0), (-1,0), 12), ('GRID', (0,0), (-1,-1), 1, colors.black)]
    
    for i, row in enumerate(data.get('display_table', [])):
        row_idx = i + 1
        val1 = f"{row['val1']:,.2f}" if isinstance(row['val1'], (int, float)) else ""
        val2 = f"{row['val2']:,.2f}" if isinstance(row['val2'], (int, float)) else ""
        
        if 'title' in row['tags']: table_data.append([Paragraph(row['kennzahl'], styles['h3']), "", ""])
        elif 'separator' in row['tags']: continue # Separatoren im PDF weglassen für kompakteres Layout
        else: table_data.append([row['kennzahl'], val1, val2])
            
        if 'bold' in row['tags']: style_commands.append(('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'))
        if 'green_text' in row['tags']: style_commands.append(('TEXTCOLOR', (0, row_idx), (-1, row_idx), colors.green))
        if 'red_text' in row['tags']: style_commands.append(('TEXTCOLOR', (0, row_idx), (-1, row_idx), colors.red))

    detail_table = Table(table_data, colWidths=[250, 100, 100]); detail_table.setStyle(TableStyle(style_commands)); story.append(detail_table); story.append(PageBreak())
    
    story.append(Paragraph("4. Finanzkennzahlen", styles['h2'])); story.append(Spacer(1, 12))
    kpi_data = [["Kennzahl", "Wert"]]; kpi_data.extend([[row['Kennzahl'], row['Wert']] for row in data.get('kpi_table', [])])
    kpi_table = Table(kpi_data, colWidths=[250, 200]); kpi_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('ALIGN', (1,1), (1,-1), 'RIGHT'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('GRID', (0,0), (-1,-1), 1, colors.black)])); story.append(kpi_table); story.append(Spacer(1, 24))

    story.append(Paragraph("5. Grafische Cashflow-Analyse (Monatlich)", styles['h2'])); story.append(Spacer(1, 12)); story.append(fig_to_image(data['figures']['bar']))
    doc.build(story)
