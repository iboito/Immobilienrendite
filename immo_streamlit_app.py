# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Streamlit-Konfiguration
st.set_page_config(
    page_title="Immobilien-Analyse Rechner",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session State initialisieren
if 'checkboxes' not in st.session_state:
    st.session_state.checkboxes = {}

if 'form_data' not in st.session_state:
    st.session_state.form_data = {}

# Haupttitel
st.title("🏠 Immobilien-Analyse Rechner")
st.markdown("---")

# Sidebar mit Navigationsmenü
st.sidebar.title("📋 Navigation")
selected_section = st.sidebar.selectbox(
    "Abschnitt auswählen:",
    ["Übersicht", "Objekt & Investition", "Finanzierung", "Rendite-Analyse", "Ergebnisse"]
)

# 1. OBJEKT & INVESTITION
if selected_section in ["Übersicht", "Objekt & Investition"]:
    st.header("1. Objekt & Investition")
    
    # Grunddaten in zwei Spalten
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Objektdaten")
        kaufpreis = st.number_input("Kaufpreis (€)", min_value=0, value=300000, step=5000)
        nebenkosten_prozent = st.slider("Nebenkosten (%)", min_value=5.0, max_value=15.0, value=10.0, step=0.5)
        nebenkosten = kaufpreis * (nebenkosten_prozent / 100)
        st.write(f"Nebenkosten: {nebenkosten:,.2f} €")
        
        gesamtinvestition = kaufpreis + nebenkosten
        st.write(f"**Gesamtinvestition: {gesamtinvestition:,.2f} €**")
        
        wohnflaeche = st.number_input("Wohnfläche (m²)", min_value=0, value=80, step=5)
        zimmer = st.number_input("Anzahl Zimmer", min_value=1, value=3, step=1)
        baujahr = st.number_input("Baujahr", min_value=1900, max_value=2024, value=1990, step=1)
        
    with col2:
        st.subheader("Standort & Zustand")
        bundesland = st.selectbox("Bundesland", [
            "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", 
            "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen", 
            "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen", 
            "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"
        ])
        
        stadt = st.text_input("Stadt/Ort", value="")
        plz = st.text_input("Postleitzahl", value="")
        
        zustand = st.selectbox("Zustand der Immobilie", [
            "Neuwertig", "Sehr gut", "Gut", "Befriedigend", 
            "Ausreichend", "Mangelhaft", "Renovierungsbedürftig"
        ])
        
        objektart = st.selectbox("Objektart", [
            "Eigentumswohnung", "Einfamilienhaus", "Doppelhaushälfte", 
            "Reihenhaus", "Mehrfamilienhaus", "Gewerbeimmobilie"
        ])
    
    # Besonderheiten
    st.subheader("Besonderheiten")
    besonderheiten = st.text_area(
        "Besondere Merkmale, Renovierungen, Ausstattung etc.",
        height=100,
        placeholder="z.B. Balkon, Garage, kürzlich renoviert, Denkmalschutz..."
    )
    
    # CHECKLISTE - Hier positioniert wie gewünscht
    st.markdown("---")
    st.subheader("✅ Checkliste: Wichtige Dokumente")
    st.write("Haken Sie die bereits vorhandenen Dokumente ab:")
    
    # Zwei-Spalten Layout für bessere Übersicht
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.checkboxes['grundbuch'] = st.checkbox(
            "📄 Grundbuchauszug",
            value=st.session_state.checkboxes.get('grundbuch', False)
        )
        st.session_state.checkboxes['flurkarte'] = st.checkbox(
            "🗺️ Flurkarte",
            value=st.session_state.checkboxes.get('flurkarte', False)
        )
        st.session_state.checkboxes['energieausweis'] = st.checkbox(
            "⚡ Energieausweis",
            value=st.session_state.checkboxes.get('energieausweis', False)
        )
        st.session_state.checkboxes['teilungserklaerung'] = st.checkbox(
            "📋 Teilungserklärung & Gemeinschaftsordnung",
            value=st.session_state.checkboxes.get('teilungserklaerung', False)
        )
        st.session_state.checkboxes['protokolle'] = st.checkbox(
            "📝 Protokolle der letzten 3-5 Eigentümerversammlungen",
            value=st.session_state.checkboxes.get('protokolle', False)
        )
        
    with col2:
        st.session_state.checkboxes['jahresabrechnung'] = st.checkbox(
            "💰 Jahresabrechnung & Wirtschaftsplan",
            value=st.session_state.checkboxes.get('jahresabrechnung', False)
        )
        st.session_state.checkboxes['ruecklage'] = st.checkbox(
            "🏦 Höhe der Instandhaltungsrücklage",
            value=st.session_state.checkboxes.get('ruecklage', False)
        )
        st.session_state.checkboxes['expose'] = st.checkbox(
            "📊 Exposé & Grundrisse",
            value=st.session_state.checkboxes.get('expose', False)
        )
        st.session_state.checkboxes['weg_protokolle'] = st.checkbox(
            "⚠️ WEG-Protokolle: Hinweise auf Streit, Sanierungen, Rückstände",
            value=st.session_state.checkboxes.get('weg_protokolle', False)
        )
        st.session_state.checkboxes['versicherung'] = st.checkbox(
            "🛡️ Versicherungsnachweis",
            value=st.session_state.checkboxes.get('versicherung', False)
        )
    
    # Fortschrittsanzeige
    completed_docs = sum(st.session_state.checkboxes.values())
    total_docs = len(st.session_state.checkboxes)
    progress = completed_docs / total_docs
    
    st.markdown("---")
    st.subheader("📈 Dokumenten-Fortschritt")
    st.progress(progress)
    st.write(f"**{completed_docs} von {total_docs} Dokumenten** vorhanden ({progress*100:.1f}%)")
    
    if progress == 1.0:
        st.success("🎉 Alle Dokumente vollständig! Sie sind optimal vorbereitet.")
    elif progress >= 0.8:
        st.info("👍 Sehr gut! Fast alle wichtigen Dokumente sind vorhanden.")
    elif progress >= 0.5:
        st.warning("⚠️ Noch einige wichtige Dokumente fehlen.")
    else:
        st.error("❌ Wichtige Dokumente fehlen noch. Bitte vervollständigen Sie die Unterlagen.")

# 2. FINANZIERUNG
if selected_section in ["Übersicht", "Finanzierung"]:
    st.header("2. Finanzierung")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Eigenkapital")
        eigenkapital = st.number_input("Verfügbares Eigenkapital (€)", min_value=0, value=50000, step=5000)
        eigenkapital_anteil = (eigenkapital / gesamtinvestition) * 100 if 'gesamtinvestition' in locals() else 0
        st.write(f"Eigenkapitalanteil: {eigenkapital_anteil:.1f}%")
        
        st.subheader("Darlehen")
        darlehenssumme = gesamtinvestition - eigenkapital if 'gesamtinvestition' in locals() else 0
        st.write(f"Benötigte Darlehenssumme: {darlehenssumme:,.2f} €")
        
        zinssatz = st.slider("Zinssatz (%)", min_value=0.5, max_value=8.0, value=3.5, step=0.1)
        laufzeit = st.number_input("Laufzeit (Jahre)", min_value=5, max_value=40, value=25, step=1)
        
    with col2:
        st.subheader("Monatliche Belastung")
        if darlehenssumme > 0:
            # Annuitätenrechnung
            monatszins = zinssatz / 100 / 12
            anzahl_raten = laufzeit * 12
            
            if monatszins > 0:
                monatliche_rate = darlehenssumme * (monatszins * (1 + monatszins)**anzahl_raten) / ((1 + monatszins)**anzahl_raten - 1)
            else:
                monatliche_rate = darlehenssumme / anzahl_raten
            
            st.write(f"**Monatliche Rate: {monatliche_rate:,.2f} €**")
            
            # Tilgungsplan erste Jahre
            restschuld = darlehenssumme
            st.write("**Tilgungsplan (erste 5 Jahre):**")
            for jahr in range(1, 6):
                zinsen_jahr = restschuld * (zinssatz / 100)
                tilgung_jahr = (monatliche_rate * 12) - zinsen_jahr
                restschuld -= tilgung_jahr
                st.write(f"Jahr {jahr}: Tilgung {tilgung_jahr:,.0f} €, Restschuld {restschuld:,.0f} €")

# 3. RENDITE-ANALYSE
if selected_section in ["Übersicht", "Rendite-Analyse"]:
    st.header("3. Rendite-Analyse")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Mieteinnahmen")
        kaltmiete_monat = st.number_input("Kaltmiete pro Monat (€)", min_value=0, value=1200, step=50)
        kaltmiete_jahr = kaltmiete_monat * 12
        st.write(f"Kaltmiete pro Jahr: {kaltmiete_jahr:,.2f} €")
        
        nebenkosten_mieter = st.number_input("Nebenkosten Mieter (€/Monat)", min_value=0, value=200, step=25)
        warmmiete = kaltmiete_monat + nebenkosten_mieter
        st.write(f"Warmmiete: {warmmiete:,.2f} €/Monat")
        
        leerstand_prozent = st.slider("Leerstand (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.5)
        effektive_mieteinnahmen = kaltmiete_jahr * (1 - leerstand_prozent / 100)
        st.write(f"Effektive Mieteinnahmen: {effektive_mieteinnahmen:,.2f} €/Jahr")
        
    with col2:
        st.subheader("Laufende Kosten")
        hausgeld = st.number_input("Hausgeld/Nebenkosten (€/Monat)", min_value=0, value=150, step=25)
        verwaltung = st.number_input("Verwaltungskosten (€/Monat)", min_value=0, value=30, step=5)
        versicherung = st.number_input("Versicherung (€/Jahr)", min_value=0, value=300, step=25)
        instandhaltung = st.number_input("Instandhaltungsrücklage (€/Jahr)", min_value=0, value=1000, step=100)
        sonstige_kosten = st.number_input("Sonstige Kosten (€/Jahr)", min_value=0, value=200, step=50)
        
        kosten_monat = hausgeld + verwaltung
        kosten_jahr = (kosten_monat * 12) + versicherung + instandhaltung + sonstige_kosten
        st.write(f"**Gesamtkosten pro Jahr: {kosten_jahr:,.2f} €**")

# 4. ERGEBNISSE & KENNZAHLEN
if selected_section in ["Übersicht", "Ergebnisse"]:
    st.header("4. Ergebnisse & Kennzahlen")
    
    # Berechnung der Kennzahlen
    if 'gesamtinvestition' in locals() and 'effektive_mieteinnahmen' in locals() and 'kosten_jahr' in locals():
        
        # Nettomietrendite
        nettomietrendite = ((effektive_mieteinnahmen - kosten_jahr) / gesamtinvestition) * 100
        
        # Bruttomietrendite
        bruttomietrendite = (kaltmiete_jahr / kaufpreis) * 100
        
        # Cashflow
        cashflow_monat = (effektive_mieteinnahmen - kosten_jahr) / 12
        if 'monatliche_rate' in locals():
            cashflow_monat -= monatliche_rate
        
        cashflow_jahr = cashflow_monat * 12
        
        # Eigenkapitalrendite
        if eigenkapital > 0:
            eigenkapitalrendite = (cashflow_jahr / eigenkapital) * 100
        else:
            eigenkapitalrendite = 0
            
        # Vervielfältiger
        vervielfaeltiger = kaufpreis / kaltmiete_jahr if kaltmiete_jahr > 0 else 0
        
        # Ergebnisse in Spalten anzeigen
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Bruttomietrendite",
                value=f"{bruttomietrendite:.2f}%",
                delta=f"{bruttomietrendite-6:.2f}%" if bruttomietrendite >= 6 else None
            )
            
        with col2:
            st.metric(
                label="Nettomietrendite", 
                value=f"{nettomietrendite:.2f}%",
                delta=f"{nettomietrendite-4:.2f}%" if nettomietrendite >= 4 else None
            )
            
        with col3:
            st.metric(
                label="Cashflow (monatlich)",
                value=f"{cashflow_monat:,.0f} €",
                delta="Positiv" if cashflow_monat > 0 else "Negativ"
            )
            
        with col4:
            st.metric(
                label="Eigenkapitalrendite",
                value=f"{eigenkapitalrendite:.2f}%",
                delta=f"{eigenkapitalrendite-8:.2f}%" if eigenkapitalrendite >= 8 else None
            )
        
        # Detailanalyse
        st.subheader("📊 Detailanalyse")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Kaufpreis-Kennzahlen:**")
            st.write(f"• Preis pro m²: {kaufpreis/wohnflaeche:.2f} €/m²")
            st.write(f"• Vervielfältiger: {vervielfaeltiger:.1f}")
            st.write(f"• Kaufnebenkosten: {nebenkosten_prozent:.1f}%")
            
            st.write("**Rendite-Kennzahlen:**")
            st.write(f"• Bruttomietrendite: {bruttomietrendite:.2f}%")
            st.write(f"• Nettomietrendite: {nettomietrendite:.2f}%")
            st.write(f"• Eigenkapitalrendite: {eigenkapitalrendite:.2f}%")
            
        with col2:
            st.write("**Cashflow-Analyse:**")
            st.write(f"• Mieteinnahmen: {effektive_mieteinnahmen:,.2f} €/Jahr")
            st.write(f"• Bewirtschaftungskosten: {kosten_jahr:,.2f} €/Jahr")
            if 'monatliche_rate' in locals():
                st.write(f"• Finanzierungskosten: {monatliche_rate*12:,.2f} €/Jahr")
            st.write(f"• **Netto-Cashflow: {cashflow_jahr:,.2f} €/Jahr**")
            
            st.write("**Bewertung:**")
            if bruttomietrendite >= 6:
                st.success("✅ Sehr gute Bruttomietrendite")
            elif bruttomietrendite >= 4:
                st.info("ℹ️ Solide Bruttomietrendite")
            else:
                st.warning("⚠️ Niedrige Bruttomietrendite")
        
        # Grafische Darstellung
        st.subheader("📈 Grafische Auswertung")
        
        # Cashflow-Diagramm
        cashflow_data = {
            'Kategorie': ['Mieteinnahmen', 'Bewirtschaftungskosten', 'Finanzierungskosten', 'Netto-Cashflow'],
            'Betrag': [effektive_mieteinnahmen, -kosten_jahr, 
                      -monatliche_rate*12 if 'monatliche_rate' in locals() else 0, 
                      cashflow_jahr],
            'Farbe': ['green', 'red', 'red', 'blue']
        }
        
        fig = px.bar(
            cashflow_data, 
            x='Kategorie', 
            y='Betrag',
            color='Farbe',
            title='Jährlicher Cashflow',
            color_discrete_map={'green': 'green', 'red': 'red', 'blue': 'blue'}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Rendite-Vergleich
        rendite_data = {
            'Rendite-Art': ['Bruttomietrendite', 'Nettomietrendite', 'Eigenkapitalrendite'],
            'Prozent': [bruttomietrendite, nettomietrendite, eigenkapitalrendite]
        }
        
        fig2 = px.bar(
            rendite_data, 
            x='Rendite-Art', 
            y='Prozent',
            title='Rendite-Vergleich',
            color='Prozent',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig2, use_container_width=True)

# ÜBERSICHT/DASHBOARD
if selected_section == "Übersicht":
    st.header("📊 Übersicht & Zusammenfassung")
    
    # Schnellübersicht in Metriken
    if 'gesamtinvestition' in locals():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Gesamtinvestition", f"{gesamtinvestition:,.0f} €")
        with col2:
            st.metric("Eigenkapital", f"{eigenkapital:,.0f} €")
        with col3:
            if 'kaltmiete_monat' in locals():
                st.metric("Kaltmiete/Monat", f"{kaltmiete_monat:,.0f} €")
        with col4:
            if 'bruttomietrendite' in locals():
                st.metric("Bruttomietrendite", f"{bruttomietrendite:.1f}%")
    
    # Wichtige Hinweise
    st.subheader("💡 Wichtige Hinweise")
    st.info("""
    **Vor dem Immobilienkauf beachten:**
    
    • Lassen Sie die Immobilie von einem Sachverständigen bewerten
    • Prüfen Sie die Finanzierungsmöglichkeiten bei mehreren Banken
    • Berücksichtigen Sie steuerliche Aspekte (Abschreibungen, Werbungskosten)
    • Kalkulieren Sie Rücklagen für Renovierungen und Instandhaltung
    • Informieren Sie sich über die Mietpreise in der Region
    • Beachten Sie die Entwicklung des Stadtteils/der Region
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🏠 Immobilien-Analyse Rechner | Entwickelt mit Streamlit</p>
    <p><small>Alle Angaben ohne Gewähr. Für wichtige Entscheidungen konsultieren Sie bitte einen Experten.</small></p>
</div>
""", unsafe_allow_html=True)

# Datenexport
if st.sidebar.button("📥 Daten exportieren"):
    # Sammle alle Daten für Export
    export_data = {
        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Kaufpreis': kaufpreis if 'kaufpreis' in locals() else 0,
        'Nebenkosten': nebenkosten if 'nebenkosten' in locals() else 0,
        'Gesamtinvestition': gesamtinvestition if 'gesamtinvestition' in locals() else 0,
        'Eigenkapital': eigenkapital if 'eigenkapital' in locals() else 0,
        'Kaltmiete_Monat': kaltmiete_monat if 'kaltmiete_monat' in locals() else 0,
        'Bruttomietrendite': bruttomietrendite if 'bruttomietrendite' in locals() else 0,
        'Nettomietrendite': nettomietrendite if 'nettomietrendite' in locals() else 0,
        'Cashflow_Jahr': cashflow_jahr if 'cashflow_jahr' in locals() else 0,
        'Checkliste_Vollständig': all(st.session_state.checkboxes.values())
    }
    
    df_export = pd.DataFrame([export_data])
    csv = df_export.to_csv(index=False)
    st.sidebar.download_button(
        label="💾 Als CSV herunterladen",
        data=csv,
        file_name=f'immobilien_analyse_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mime='text/csv',
    )
