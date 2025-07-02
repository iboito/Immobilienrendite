# immo_app.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import immo_core
import pdf_generator

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Immobilien-Analyse-Tool v39 - FINAL FIX")
        self.geometry("1200x950")

        self.config = immo_core.load_config()
        self.entries = {}
        self.comboboxes = {}
        self.nebenkosten_prozent_entries = {}
        self.nutzungsart_var = tk.StringVar(value="Vermietung")
        self.show_darlehen2_var = tk.BooleanVar(value=False)
        self.info_icon = tk.PhotoImage(width=18, height=18)
        self.last_results = None
        self.modus_d1_var = tk.StringVar(value="tilgungssatz")
        self.modus_d2_var = tk.StringVar(value="tilgungssatz")
        self.darlehen_ergebnis_labels = {}
        
        self.gesamtkosten_var = tk.StringVar()
        self.darlehensbedarf_var = tk.StringVar()
        self.afa_satz_var = tk.StringVar()

        main_frame = ttk.Frame(self, padding="10"); main_frame.pack(fill=tk.BOTH, expand=True)
        self._build_ui(main_frame)
        self._setup_styles()
        self._update_visibility()
        self._update_finanzbedarf()
        self._update_afa_satz()

    def _build_ui(self, parent):
        role_frame = ttk.LabelFrame(parent, text="1. Anwendungsfall wählen", padding=10)
        role_frame.pack(fill='x', pady=(0, 10))
        ttk.Radiobutton(role_frame, text="Kapitalanlage (Vermietung)", variable=self.nutzungsart_var, value="Vermietung", command=self._update_visibility).pack(side='left', padx=10)
        ttk.Radiobutton(role_frame, text="Eigennutzung", variable=self.nutzungsart_var, value="Eigennutzung", command=self._update_visibility).pack(side='left', padx=10)

        input_container = ttk.Frame(parent); input_container.pack(fill='x', expand=False, pady=5)
        output_container = ttk.Frame(parent); output_container.pack(fill='both', expand=True, pady=10)

        notebook = ttk.Notebook(input_container); notebook.pack(fill="x", expand=True)
        self.tab_general = ttk.Frame(notebook, padding="10"); notebook.add(self.tab_general, text='Objekt & Investition')
        self.tab_finance = ttk.Frame(notebook, padding="10"); notebook.add(self.tab_finance, text='Finanzierung')
        self.tab_rent_tax = ttk.Frame(notebook, padding="10"); notebook.add(self.tab_rent_tax, text='Laufende Posten & Steuer')

        self._create_general_tab(self.tab_general)
        self._create_finance_tab(self.tab_finance)
        self._create_rent_tax_tab(self.tab_rent_tax)

        action_frame = ttk.Frame(input_container); action_frame.pack(fill='x', pady=10)
        calc_button = ttk.Button(action_frame, text="Analyse berechnen", command=self._run_calculation, style="Accent.TButton"); calc_button.pack(side='left', padx=10)
        self.export_button = ttk.Button(action_frame, text="Bericht als PDF exportieren", command=self._export_pdf, state="disabled")
        self.export_button.pack(side='left', padx=10)
        
        self._create_output_widgets(output_container)
    
    def _create_entry(self, parent, text, key, default_value="", keyrelease_func=None):
        var = tk.StringVar(value=default_value)
        label = ttk.Label(parent, text=text)
        entry = ttk.Entry(parent, textvariable=var, width=15)
        self.entries[key] = {'var': var, 'widget': entry, 'label': label}
        if keyrelease_func:
            entry.bind("<KeyRelease>", keyrelease_func)
        return label, entry
    
    def _create_combobox(self, parent, text, key, options, default_value=None, selection_func=None):
        var = tk.StringVar(value=default_value if default_value else options[0])
        label = ttk.Label(parent, text=text)
        combobox = ttk.Combobox(parent, textvariable=var, values=options, state="readonly", width=13)
        self.comboboxes[key] = {'var': var, 'widget': combobox, 'label': label}
        if selection_func:
            combobox.bind("<<ComboboxSelected>>", selection_func)
        return label, combobox

    def _create_general_tab(self, parent):
        details_container = ttk.Frame(parent); details_container.pack(side='left', fill='y', padx=5, anchor='n')
        f_details = ttk.LabelFrame(details_container, text="Qualitative Objektdetails", padding=10)
        f_details.pack(fill='x', pady=(0, 10))
        row = 0
        l, e = self._create_entry(f_details, "Wohnort:", "wohnort", "Nürnberg"); l.grid(row=row, column=0, sticky='w'); e.grid(row=row, column=1, sticky='w', pady=2); row+=1
        baujahr_opts = ["1925 - 2022", "vor 1925", "ab 2023"]
        l, c = self._create_combobox(f_details, "Baujahr:", "baujahr_kategorie", baujahr_opts, selection_func=self._update_afa_satz); l.grid(row=row, column=0, sticky='w'); c.grid(row=row, column=1, sticky='w', pady=2); row+=1
        l, e = self._create_entry(f_details, "Wohnfläche (qm):", "wohnflaeche_qm", "80"); l.grid(row=row, column=0, sticky='w'); e.grid(row=row, column=1, sticky='w', pady=2); row+=1
        stockwerk_opts = ["EG", "1", "2", "3", "4", "5", "6", "DG"]
        l, c = self._create_combobox(f_details, "Stockwerk:", "stockwerk", stockwerk_opts); l.grid(row=row, column=0, sticky='w'); c.grid(row=row, column=1, sticky='w', pady=2); row+=1
        zimmer_opts = ["1", "1,5", "2", "2,5", "3", "3,5", "4", "4,5", "5"]
        l, c = self._create_combobox(f_details, "Zimmeranzahl:", "zimmeranzahl", zimmer_opts, "3"); l.grid(row=row, column=0, sticky='w'); c.grid(row=row, column=1, sticky='w', pady=2); row+=1
        energie_opts = ["A+", "A", "B", "C", "D", "E", "F", "G", "H"]
        l, c = self._create_combobox(f_details, "Energieeffizienz:", "energieeffizienz", energie_opts, "C"); l.grid(row=row, column=0, sticky='w'); c.grid(row=row, column=1, sticky='w', pady=2); row+=1
        oepnv_opts = ["Sehr gut", "Gut", "Okay"]
        l, c = self._create_combobox(f_details, "ÖPNV-Anbindung:", "oepnv_anbindung", oepnv_opts); l.grid(row=row, column=0, sticky='w'); c.grid(row=row, column=1, sticky='w', pady=2); row+=1
        l, e = self._create_entry(f_details, "Besonderheiten:", "besonderheiten", "Balkon, Einbauküche"); l.grid(row=row, column=0, sticky='w'); e.grid(row=row, column=1, sticky='w', pady=2); row+=1
        finance_container = ttk.Frame(parent); finance_container.pack(side='left', fill='y', padx=5, anchor='n')
        f_finance = ttk.LabelFrame(finance_container, text="Finanzielle Eckdaten", padding=10)
        f_finance.pack(fill='x', pady=(0, 10))
        l, e = self._create_entry(f_finance, "Kaufpreis (€)", "kaufpreis", "250000", self._update_finanzbedarf); l.grid(row=0, column=0, sticky='w'); e.grid(row=0, column=1, sticky='w', pady=2)
        l, e = self._create_entry(f_finance, "Garage/Stellplatz (€)", "garage_stellplatz_kosten", "0", self._update_finanzbedarf); l.grid(row=1, column=0, sticky='w'); e.grid(row=1, column=1, sticky='w', pady=2)
        l, e = self._create_entry(f_finance, "Zusätzl. Investitionsbedarf (€)", "invest_bedarf", "10000", self._update_finanzbedarf); l.grid(row=2, column=0, sticky='w'); e.grid(row=2, column=1, sticky='w', pady=2)
        f_nebenkosten = ttk.LabelFrame(finance_container, text="Kaufnebenkosten", padding=10)
        f_nebenkosten.pack(fill='x', pady=(10, 0))
        self.nebenkosten_prozent_entries = {}
        labels = {'grunderwerbsteuer': "Grunderwerbsteuer", 'notar': "Notar", 'grundbuch': "Grundbuch", 'makler': "Makler"}
        for i, (key, text) in enumerate(labels.items()):
            ttk.Label(f_nebenkosten, text=text).grid(row=i, column=0, sticky="w", pady=2)
            prozent_entry = ttk.Entry(f_nebenkosten, width=6); prozent_entry.insert(0, self.config.get(f"{key}_prozent", "0"))
            prozent_entry.grid(row=i, column=1, padx=5, pady=2); self.nebenkosten_prozent_entries[key] = prozent_entry

    def _create_finance_tab(self, parent):
        left_container = ttk.Frame(parent); left_container.pack(side='left', fill='y', padx=5, anchor='n')
        bedarfs_frame = ttk.LabelFrame(left_container, text="Finanzierungsbedarf", padding=10); bedarfs_frame.pack(fill='x', anchor='n')
        ttk.Label(bedarfs_frame, text="Gesamtkosten:").grid(row=0, column=0, sticky='w', pady=2)
        ttk.Label(bedarfs_frame, textvariable=self.gesamtkosten_var, font=("Helvetica", 13, "bold")).grid(row=0, column=1, sticky='w', pady=2, padx=5)
        l, e = self._create_entry(bedarfs_frame, "- Eigenkapital (€):", "eigenkapital", "80000", self._update_finanzbedarf); l.grid(row=1, column=0, sticky='w'); e.grid(row=1, column=1, sticky='w', pady=2)
        ttk.Separator(bedarfs_frame, orient='horizontal').grid(row=2, columnspan=2, sticky='ew', pady=5)
        ttk.Label(bedarfs_frame, text="= Darlehensbedarf:", font=("Helvetica", 13, "bold")).grid(row=3, column=0, sticky='w', pady=2)
        ttk.Label(bedarfs_frame, textvariable=self.darlehensbedarf_var, font=("Helvetica", 13, "bold")).grid(row=3, column=1, sticky='w', pady=2, padx=5)
        pers_finance_frame = ttk.LabelFrame(left_container, text="Persönliche Finanzsituation", padding=10); pers_finance_frame.pack(fill='x', pady=(10, 0), anchor='n')
        l, e = self._create_entry(pers_finance_frame, "Monatl. verfügbares Einkommen (€):", "verfuegbares_einkommen_mtl", "2500"); l.grid(row=0, column=0, sticky='w', pady=2); e.grid(row=0, column=1, sticky='w', pady=2)
        darlehen_container = ttk.Frame(parent); darlehen_container.pack(side='left', fill='y', padx=5, anchor='n')
        frame1 = self._create_darlehen_frame(darlehen_container, "Darlehensdetails", 1, self.modus_d1_var); frame1.pack(side='top', fill='y', anchor='n')
        checkbox = ttk.Checkbutton(darlehen_container, text="Weiteres Darlehen hinzufügen", variable=self.show_darlehen2_var, command=self._toggle_darlehen2_fields); checkbox.pack(anchor='w', pady=(10,0))
        self.darlehen2_frame = self._create_darlehen_frame(darlehen_container, "Darlehen II", 2, self.modus_d2_var)

    def _create_darlehen_frame(self, parent, title, num, modus_var):
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        update_func = lambda e, n=num: self._update_darlehen_berechnung(n)
        row = 0
        if num > 1: l, e = self._create_entry(frame, f"Darlehen {num} Summe (€)", f"darlehen{num}_summe", "0", update_func); l.grid(row=row,column=0,sticky='w'); e.grid(row=row,column=1,sticky='w',pady=2); row+=1
        l, e = self._create_entry(frame, "Zinssatz (%)", f"zins{num}_prozent", "3.5" if num==1 else "0", update_func); l.grid(row=row,column=0,sticky='w'); e.grid(row=row,column=1,sticky='w',pady=2); row+=1
        ttk.Separator(frame, orient='horizontal').grid(row=row, columnspan=2, sticky='ew', pady=5); row+=1
        ttk.Radiobutton(frame, text="Nach Tilgungssatz", variable=modus_var, value="tilgungssatz", command=lambda n=num: self._update_finance_mode(n)).grid(row=row, columnspan=2, sticky='w'); row+=1
        l, e = self._create_entry(frame, "Tilgung (%)", f"tilgung{num}_prozent", "2.0" if num==1 else "0", update_func); l.grid(row=row,column=0,sticky='w'); e.grid(row=row,column=1,sticky='w',pady=2); row+=1
        ttk.Radiobutton(frame, text="Nach Tilgungsbetrag", variable=modus_var, value="tilgung_euro", command=lambda n=num: self._update_finance_mode(n)).grid(row=row, columnspan=2, sticky='w'); row+=1
        l, e = self._create_entry(frame, "Tilgung (€ mtl.)", f"tilgung{num}_euro_mtl", "350", update_func); l.grid(row=row,column=0,sticky='w'); e.grid(row=row,column=1,sticky='w',pady=2); row+=1
        ttk.Radiobutton(frame, text="Nach Laufzeit", variable=modus_var, value="laufzeit", command=lambda n=num: self._update_finance_mode(n)).grid(row=row, columnspan=2, sticky='w'); row+=1
        l, e = self._create_entry(frame, "Laufzeit (Jahre)", f"laufzeit{num}_jahre", "25", update_func); l.grid(row=row,column=0,sticky='w'); e.grid(row=row,column=1,sticky='w',pady=2); row+=1
        ttk.Separator(frame, orient='horizontal').grid(row=row, columnspan=2, sticky='ew', pady=5); row+=1
        ergebnis_label = ttk.Label(frame, text="", font=("Helvetica", 11, "italic"), foreground="white", wraplength=250)
        ergebnis_label.grid(row=row, columnspan=2, sticky='w', padx=5)
        self.darlehen_ergebnis_labels[num] = ergebnis_label
        self._update_finance_mode(num)
        return frame

    def _update_finanzbedarf(self, event=None):
        try:
            kaufpreis = self._get_float("kaufpreis"); garage = self._get_float("garage_stellplatz_kosten"); invest_bedarf = self._get_float("invest_bedarf"); eigenkapital = self._get_float("eigenkapital")
            nebenkosten_prozente = {key: float(entry.get().replace(',', '.') or '0') for key, entry in self.nebenkosten_prozent_entries.items()}
            nebenkosten_summe = ((kaufpreis + garage) * (sum(nebenkosten_prozente.values()) / 100))
            gesamtkosten = kaufpreis + garage + invest_bedarf + nebenkosten_summe
            darlehensbedarf = gesamtkosten - eigenkapital
            self.gesamtkosten_var.set(f"{gesamtkosten:,.2f} €"); self.darlehensbedarf_var.set(f"{darlehensbedarf:,.2f}")
            self._update_darlehen_berechnung(1)
        except (ValueError, KeyError): self.gesamtkosten_var.set("..."); self.darlehensbedarf_var.set("Fehler")

    def _update_finance_mode(self, num):
        modus = (self.modus_d1_var if num == 1 else self.modus_d2_var).get()
        self.entries[f"tilgung{num}_prozent"]['widget'].config(state='normal' if modus == 'tilgungssatz' else 'disabled')
        self.entries[f"tilgung{num}_euro_mtl"]['widget'].config(state='normal' if modus == 'tilgung_euro' else 'disabled')
        self.entries[f"laufzeit{num}_jahre"]['widget'].config(state='normal' if modus == 'laufzeit' else 'disabled')
        self._update_darlehen_berechnung(num)

    def _update_darlehen_berechnung(self, num):
        try:
            summe = float(self.darlehensbedarf_var.get().replace(',','')) if num == 1 else self._get_float(f"darlehen{num}_summe")
            zins_p = self._get_float(f"zins{num}_prozent")
            modus = (self.modus_d1_var if num == 1 else self.modus_d2_var).get()
            tilgung_p = self._get_float(f"tilgung{num}_prozent") if modus == 'tilgungssatz' else None
            tilgung_euro_mtl = self._get_float(f"tilgung{num}_euro_mtl") if modus == 'tilgung_euro' else None
            laufzeit_j = self._get_float(f"laufzeit{num}_jahre") if modus == 'laufzeit' else None
            details = immo_core.berechne_darlehen_details(summe, zins_p, tilgung_p, tilgung_euro_mtl, laufzeit_j, modus)
            text = (f"=> Rate: {details['monatsrate']:.2f} €/Monat | Laufzeit: ca. {details['laufzeit_jahre']:.1f} J. | Tilgung: {details['tilgung_p_ergebnis']:.2f}%")
            self.darlehen_ergebnis_labels[num].config(text=text)
        except (ValueError, KeyError, AttributeError): self.darlehen_ergebnis_labels[num].config(text="")
    
    def _create_rent_tax_tab(self, parent):
        f1 = ttk.LabelFrame(parent, text="Laufende Einnahmen & Kosten", padding=10); f1.pack(side='left', fill='y', padx=5, anchor='n')
        l, e = self._create_entry(f1, "Kaltmiete mtl. (€)", "kaltmiete_monatlich", "1000", lambda ev: self._update_warmmiete()); l.grid(row=0, column=0, sticky='w'); e.grid(row=0, column=1, sticky='w', pady=2)
        uk_frame = ttk.Frame(f1); uk_frame.grid(row=1, column=0, columnspan=2, sticky='w')
        l, e = self._create_entry(uk_frame, "Umlagefähige Kosten mtl. (€)", "umlagefaehige_kosten_monatlich", "150", lambda ev: self._update_warmmiete()); l.pack(side='left', padx=(0,4)); e.pack(side='left')
        info_uk_button = ttk.Button(uk_frame, text="?", image=self.info_icon, compound="center", command=self._show_info_umlagefaehig); info_uk_button.pack(side='left', padx=5)
        self.entries["umlagefaehige_kosten_monatlich"]['info_button'] = info_uk_button
        ttk.Separator(f1, orient='horizontal').grid(row=2, columnspan=2, sticky='ew', pady=5)
        self.warmmiete_label_text = ttk.Label(f1, text="Warmmiete mtl. (für Mieter):"); self.warmmiete_label_text.grid(row=3, column=0, sticky="w", pady=2)
        self.warmmiete_label_value = ttk.Label(f1, text="1,150.00 €", font=("Helvetica", 12, "bold")); self.warmmiete_label_value.grid(row=3, column=1, padx=5, pady=2, sticky="w")
        nuk_frame = ttk.Frame(f1); nuk_frame.grid(row=4, column=0, columnspan=2, sticky='w', pady=(10,2))
        l, e = self._create_entry(nuk_frame, "Nicht umlagef. Kosten p.a. (€)", "nicht_umlagefaehige_kosten_pa", "960"); l.pack(side='left', padx=(0,4)); e.pack(side='left')
        info_nuk_button = ttk.Button(nuk_frame, text="?", image=self.info_icon, compound="center", command=self._show_info_nicht_umlagefaehig); info_nuk_button.pack(side='left', padx=5)
        self.entries["nicht_umlagefaehige_kosten_pa"]['info_button'] = info_nuk_button
        f3 = ttk.LabelFrame(parent, text="Steuerliche Annahmen", padding=10); f3.pack(side='left', fill='y', padx=5, anchor='n')
        self.afa_label_text = ttk.Label(f3, text="AfA-Satz (%):"); self.afa_label_text.grid(row=0, column=0, sticky='w', pady=2)
        self.afa_label_value = ttk.Label(f3, textvariable=self.afa_satz_var, font=("Helvetica", 13, "bold")); self.afa_label_value.grid(row=0, column=1, sticky='w', pady=2, padx=5)
        l, e = self._create_entry(f3, "Persönl. Steuersatz (%)", "steuersatz", "42.0"); l.grid(row=1, column=0, sticky='w'); e.grid(row=1, column=1, sticky='w', pady=2)
        self._update_warmmiete()
    
    def _update_afa_satz(self, event=None):
        baujahr_kategorie = self.comboboxes['baujahr_kategorie']['var'].get()
        self.afa_satz_var.set("2.5" if baujahr_kategorie == 'vor 1925' else "3.0" if baujahr_kategorie == 'ab 2023' else "2.0")

    def _show_info_umlagefaehig(self): messagebox.showinfo("Info: Umlagefähige Kosten", "Kosten, die direkt an den Mieter weitergegeben werden.\n\nBeispiele:\n• Heizung, Grundsteuer, Müllabfuhr")
    def _show_info_nicht_umlagefaehig(self): messagebox.showinfo("Info: Nicht umlagefähige Kosten", "Kosten, die Sie als Eigentümer tragen.\n\nBeispiele:\n• Instandhaltungsrücklage, Verwaltung")
    
    def _setup_styles(self):
        style = ttk.Style(self); style.configure("Accent.TButton", font=("Helvetica", 12, "bold"))
        style.configure("Treeview", font=('Helvetica', 11), rowheight=30)
        style.configure("Treeview.Heading", font=('Helvetica', 11, 'bold'))
        for tree in [self.output_tree, self.kpi_tree]:
            tree.tag_configure('bold', font=('Helvetica', 11, 'bold')); tree.tag_configure('separator', foreground='grey', font=('Helvetica', 11, 'italic'))
            tree.tag_configure('title', font=('Helvetica', 12, 'bold')); tree.tag_configure('green_text', foreground='#008000'); tree.tag_configure('red_text', foreground='red')

    def _create_output_widgets(self, parent):
        parent.columnconfigure(0, weight=3); parent.columnconfigure(1, weight=2); parent.rowconfigure(0, weight=1)
        left_frame = ttk.Frame(parent); left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.output_tree = ttk.Treeview(left_frame, columns=("kennzahl", "jahr1", "jahr2"), show="headings", height=18); self.output_tree.pack(fill='both', expand=True)
        self.kpi_tree = ttk.Treeview(left_frame, columns=("kennzahl", "wert"), show="headings", height=4); self.kpi_tree.pack(fill='both', expand=False, pady=(10,0))
        right_frame = ttk.Frame(parent); right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.rowconfigure(0, weight=1); right_frame.columnconfigure(0, weight=1)
        self.fig_pie = Figure(figsize=(5, 4), dpi=100); self.ax_pie = self.fig_pie.add_subplot(111); self.canvas_pie = FigureCanvasTkAgg(self.fig_pie, master=right_frame); self.canvas_pie.get_tk_widget().pack(fill='both', expand=True)
        self.fig_bar = Figure(figsize=(5, 4), dpi=100); self.ax_bar = self.fig_bar.add_subplot(111); self.canvas_bar = FigureCanvasTkAgg(self.fig_bar, master=right_frame); self.canvas_bar.get_tk_widget().pack(fill='both', expand=True)

    def _toggle_darlehen2_fields(self):
        if self.show_darlehen2_var.get(): self.darlehen2_frame.pack(side='top', fill='y', anchor='n', pady=(10,0))
        else: self.darlehen2_frame.pack_forget()

    def _update_warmmiete(self, event=None):
        try:
            kaltmiete_mtl = self._get_float("kaltmiete_monatlich"); umlage_kosten = self._get_float("umlagefaehige_kosten_monatlich")
            self.warmmiete_label_value.config(text=f"{kaltmiete_mtl + umlage_kosten:,.2f} €")
        except (ValueError, KeyError): self.warmmiete_label_value.config(text="...")
    
    def _update_visibility(self):
        is_vermietung = self.nutzungsart_var.get() == "Vermietung"; state = 'normal' if is_vermietung else 'disabled'
        laufende_keys = ["kaltmiete_monatlich", "umlagefaehige_kosten_monatlich", "steuersatz"]
        for k in laufende_keys:
            if k in self.entries:
                self.entries[k]['widget'].config(state=state); self.entries[k]['label'].config(state=state)
                if 'info_button' in self.entries.get(k,{}): self.entries[k]['info_button'].config(state=state)
        self.afa_label_text.config(state=state); self.afa_label_value.config(state=state)
        self.warmmiete_label_text.config(state=state); self.warmmiete_label_value.config(state=state)
        self.entries["nicht_umlagefaehige_kosten_pa"]['info_button'].config(state=state)
        self.entries["nicht_umlagefaehige_kosten_pa"]['label'].config(text="Nicht umlagef. Kosten p.a. (€)" if is_vermietung else "Laufende Kosten p.a. (Hausgeld etc.)")

    def _get_float(self, key):
        var = self.entries.get(key, {}).get('var') or self.comboboxes.get(key, {}).get('var')
        val_str = var.get() if var else "0"
        return float(val_str.replace(',', '.') if val_str else "0")
    
    def _run_calculation(self):
        try:
            darlehensbedarf_str = self.darlehensbedarf_var.get().replace(',','')
            darlehen1_summe = float(darlehensbedarf_str) if darlehensbedarf_str and "Fehler" not in darlehensbedarf_str else 0
            inputs = self._collect_inputs(darlehen1_summe)
            results = immo_core.calculate_analytics(inputs)
            if 'error' in results: 
                messagebox.showerror("Fehler bei der Berechnung", results['error']); self.export_button.config(state="disabled"); return
            self.last_results = {**results, 'inputs': inputs, 'figures': {'pie': self.fig_pie, 'bar': self.fig_bar}}
            self._update_ui(results)
            self.export_button.config(state="normal")
        except Exception as e: 
            messagebox.showerror("Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {e}"); self.export_button.config(state="disabled")

    def _collect_inputs(self, darlehen1_summe):
        inputs = {key: var['var'].get() for key, var in self.entries.items()}
        inputs.update({key: var['var'].get() for key, var in self.comboboxes.items()})
        float_keys = ['kaufpreis', 'garage_stellplatz_kosten', 'invest_bedarf', 'eigenkapital', 'zins1_prozent', 'tilgung1_prozent', 'tilgung1_euro_mtl', 'laufzeit1_jahre', 'zins2_prozent', 'tilgung2_prozent', 'tilgung2_euro_mtl', 'laufzeit2_jahre', 'kaltmiete_monatlich', 'umlagefaehige_kosten_monatlich', 'nicht_umlagefaehige_kosten_pa', 'steuersatz', 'verfuegbares_einkommen_mtl']
        for key in float_keys: inputs[key] = self._get_float(key)
        inputs.update({'nutzungsart': self.nutzungsart_var.get(), 'darlehen1_summe': darlehen1_summe, 'modus_d1': self.modus_d1_var.get(),
                       'darlehen2_summe': self._get_float("darlehen2_summe") if self.show_darlehen2_var.get() else 0,
                       'modus_d2': self.modus_d2_var.get() if self.show_darlehen2_var.get() else 'tilgungssatz',
                       'nebenkosten_prozente': {key: float(entry.get().replace(',', '.') or '0') for key, entry in self.nebenkosten_prozent_entries.items()}})
        return inputs

    def _export_pdf(self):
        if not self.last_results: messagebox.showwarning("Export nicht möglich", "Bitte führen Sie zuerst eine Berechnung durch."); return
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF-Dokumente", "*.pdf")], title="Analyse als PDF speichern", initialfile=f"Immobilienanalyse_{self.last_results['inputs'].get('wohnort', 'Objekt')}.pdf")
        if filepath:
            try:
                pdf_generator.create_bank_report(self.last_results, filepath)
                messagebox.showinfo("Export erfolgreich", f"Bericht wurde gespeichert unter:\n{filepath}")
            except Exception as e: messagebox.showerror("Export fehlgeschlagen", f"Ein Fehler ist aufgetreten:\n{e}")

    def _update_ui(self, data):
        # *** HIER IST DIE VEREINFACHTE UND KORREKTE LOGIK ***
        for tree in [self.output_tree, self.kpi_tree]: tree.delete(*tree.get_children())
        
        # Haupttabelle befüllen
        self.output_tree.heading("jahr1", text="Jahr der Anschaffung (€)"); self.output_tree.heading("jahr2", text="Laufende Jahre (€)")
        for row in data.get('display_table', []):
            val1_str = f"{row['val1']:,.2f}" if isinstance(row['val1'], (int, float)) else (row['val1'] or "")
            val2_str = f"{row['val2']:,.2f}" if isinstance(row['val2'], (int, float)) else (row['val2'] or "")
            self.output_tree.insert("", "end", values=(row['kennzahl'], val1_str, val2_str), tags=tuple(row['tags']))
            
        # KPI-Tabelle befüllen
        self.kpi_tree.heading("kennzahl", text="Kennzahl"); self.kpi_tree.heading("wert", text="Wert")
        for row in data.get('kpi_table', []): self.kpi_tree.insert("", "end", values=(row['Kennzahl'], row['Wert']))
        
        self._update_pie_chart(data.get('pie_data', {}))
        self._update_bar_chart(data.get('bar_data', {}))

    def _update_pie_chart(self, data):
        self.ax_pie.clear(); labels = [k for k, v in data.items() if v > 0]; sizes = [v for k, v in data.items() if v > 0]
        self.ax_pie.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#4F81BD', '#C0504D', '#9BBB59'])
        self.ax_pie.set_title("Finanzierungsstruktur"); self.canvas_pie.draw()

    def _update_bar_chart(self, data):
        self.ax_bar.clear(); einnahmen = data.get('Nettokaltmiete', 0)
        self.ax_bar.bar("Einnahmen", einnahmen, color='green', label='Nettokaltmiete')
        ausgaben_labels = ['Bewirt.-Kosten', 'Zinsen', 'Tilgung']
        ausgaben_werte = [data.get(k.replace('-','_').replace('.','_'), 0) for k in ['Bewirt.-Kosten', 'Zinsen', 'Tilgung']]
        bottom = 0; colors = ['#C0504D', '#F79646', '#8064A2']
        for i, (label, wert) in enumerate(zip(ausgaben_labels, ausgaben_werte)): 
            self.ax_bar.bar("Ausgaben", -wert, bottom=bottom, label=label, color=colors[i]); bottom -= wert
        self.ax_bar.set_title("Monatlicher Cashflow"); self.ax_bar.set_ylabel("Betrag (€)"); self.ax_bar.legend(); self.canvas_bar.draw()

if __name__ == "__main__":
    app = App()
    app.mainloop()
