import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
import threading
import pandas as pd
import os
import sys
import logging
import time
from company_scraper import (
    find_website_via_google, 
    scrape_company_website, 
    clean_url
)
from gemini_api import GeminiEmailGenerator

# Tab içinde data grid görüntüleme sınıfı
class ExcelTableViewer(ttk.Frame):
    def __init__(self, parent, dataframe=None, title="Excel Görüntüleyici"):
        super().__init__(parent)
        self.title = title
        self.dataframe = None
        self.email_generator = GeminiEmailGenerator()
        self.buttons = []
        
        # Ana layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Treeview için frame
        self.table_frame = ttk.Frame(self)
        self.table_frame.grid(row=0, column=0, sticky="nsew")
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)
        
        # Kontrol paneli
        self.control_frame = ttk.Frame(self)
        self.control_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Create Treeview for data display
        self.tree = ttk.Treeview(self.table_frame)
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Add scrollbars
        vsb = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Configure Treeview
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Export button
        export_button = ttk.Button(self.control_frame, text="Dışa Aktar", command=self.export_data)
        export_button.pack(side=tk.RIGHT, padx=5)
        
        # Search functionality
        search_frame = ttk.Frame(self.control_frame)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(search_frame, text="Ara:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<KeyRelease>", self.search_data)
        
        # Column selector
        ttk.Label(search_frame, text="Kolon:").pack(side=tk.LEFT, padx=5)
        self.search_column_var = tk.StringVar()
        self.search_column_combo = ttk.Combobox(search_frame, textvariable=self.search_column_var, width=15)
        self.search_column_combo.pack(side=tk.LEFT, padx=5)
        
        # Style for alternating rows
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        style.map('Treeview', background=[('selected', '#0078D7')])
        
        if dataframe is not None:
            self.load_dataframe(dataframe)
    
    def load_dataframe(self, dataframe):
        self.dataframe = dataframe
        
        # Clear existing data and buttons
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.buttons = []
            
        # Configure columns
        self.tree["columns"] = list(dataframe.columns) + ["EmailTemplate"]
        self.tree["show"] = "headings"
        
        # Set column values for search
        self.search_column_combo['values'] = ['Tümü'] + list(dataframe.columns)
        self.search_column_combo.current(0)
        
        # Set column headings
        for column in dataframe.columns:
            self.tree.heading(column, text=column)
            # Set column width based on content
            max_width = max(
                len(str(column)),
                dataframe[column].astype(str).str.len().max() if len(dataframe) > 0 else 10
            )
            # Limit width to reasonable size
            column_width = min(max_width * 10, 300)
            self.tree.column(column, width=column_width, minwidth=50)
            
        # Configure special styling for WebSitesi column - fix underline issue
        self.tree.tag_configure('url_link', foreground='blue')
        
        # Add Email Template button column
        self.tree.heading("EmailTemplate", text="E-posta Şablonu")
        self.tree.column("EmailTemplate", width=120, minwidth=120, stretch=False)
        
        # Insert data and create buttons
        for i, (index, row) in enumerate(dataframe.iterrows()):
            values = [row[col] if pd.notna(row[col]) else "" for col in dataframe.columns] + ["Mail Şablonu"]
            
            # Add tags to make the row clickable
            tags = [f'row{i%2}', f'btn{i}']
            
            # Add special tag for website URLs
            for j, col in enumerate(dataframe.columns):
                if col == 'WebSitesi' and pd.notna(row[col]) and row[col]:
                    tags.append('url_link')
            
            item_id = self.tree.insert("", tk.END, values=values, tags=tags)
            
            # Apply alternating row colors
            if i % 2 == 0:
                self.tree.tag_configure(f'row{i%2}', background='#F0F0F0')
            else:
                self.tree.tag_configure(f'row{i%2}', background='white')
        
        # Configure the cursor to change when hovering over URL
        def on_motion(event):
            region = self.tree.identify_region(event.x, event.y)
            column = self.tree.identify_column(event.x)
            
            # Check if we're over a website URL cell
            if region == "cell":
                col_idx = int(column[1:]) - 1
                website_col_index = -1
                for i, col in enumerate(dataframe.columns):
                    if col == 'WebSitesi':
                        website_col_index = i
                        break
                
                if col_idx == website_col_index:
                    self.tree.config(cursor="hand2")  # Hand cursor
                    return
            
            # Default cursor
            self.tree.config(cursor="")
            
        # Bind motion for cursor change
        self.tree.bind('<Motion>', on_motion)
        
        # Add click binding to the tree for button column and website URLs
        self.tree.bind('<ButtonRelease-1>', self.handle_button_click)
    
    def handle_button_click(self, event):
        """Handle clicks on the buttons in the treeview"""
        # Get the item that was clicked
        region = self.tree.identify_region(event.x, event.y)
        column = self.tree.identify_column(event.x)
        
        # Check if we clicked on a cell in the button column
        if region == "cell" and column == f"#{len(self.dataframe.columns) + 1}":
            item_id = self.tree.identify_row(event.y)
            if item_id:
                # Get the index of the clicked row
                row_index = self.tree.index(item_id)
                # Generate email template for this row
                self.generate_email_template(row_index)
        
        # Check if we clicked on a website URL
        elif region == "cell":
            item_id = self.tree.identify_row(event.y)
            if item_id:
                # Get column index (remove the # prefix and convert to int)
                col_idx = int(column[1:]) - 1
                
                # Check if clicked column is the 'WebSitesi' column 
                website_col_index = -1
                for i, col in enumerate(self.dataframe.columns):
                    if col == 'WebSitesi':
                        website_col_index = i
                        break
                
                if col_idx == website_col_index:
                    row_index = self.tree.index(item_id)
                    url = self.dataframe.iloc[row_index]['WebSitesi']
                    if url and isinstance(url, str):
                        # Clean up URL to ensure it has protocol
                        if not url.startswith(('http://', 'https://')):
                            url = 'http://' + url
                        
                        try:
                            import webbrowser
                            webbrowser.open(url)
                        except Exception as e:
                            messagebox.showerror("Hata", f"Web sitesi açılırken hata oluştu: {str(e)}")
    
    def add_buttons(self):
        """This method is no longer needed, buttons are handled through tags and binding"""
        pass
    
    def generate_email_template(self, row_index):
        """Generate an email template for the selected company using Gemini API"""
        if row_index >= len(self.dataframe):
            messagebox.showerror("Hata", "Geçersiz firma seçimi.")
            return
        
        # Check if Gemini API is configured
        if not self.email_generator.is_configured:
            # Ask for API key
            self.request_api_key()
            if not self.email_generator.is_configured:
                return
        
        # Get company data from the selected row
        company_data = self.dataframe.iloc[row_index].to_dict()
        
        # Show loading dialog
        loading_dialog = tk.Toplevel()
        loading_dialog.title("E-posta Şablonu Oluşturuluyor")
        loading_dialog.geometry("300x100")
        loading_dialog.transient(self.master)
        loading_dialog.grab_set()
        loading_dialog.resizable(False, False)
        
        # Center loading dialog on screen
        loading_dialog.update_idletasks()
        width = loading_dialog.winfo_width()
        height = loading_dialog.winfo_height()
        x = (loading_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (loading_dialog.winfo_screenheight() // 2) - (height // 2)
        loading_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        ttk.Label(loading_dialog, text=f"{company_data.get('FirmaAdı', 'Firma')} için e-posta şablonu hazırlanıyor...").pack(pady=10)
        progress = ttk.Progressbar(loading_dialog, mode="indeterminate")
        progress.pack(fill="x", padx=20)
        progress.start()
        
        # Run email generation in a separate thread
        def generate_email():
            try:
                self.show_email_template(company_data)
                loading_dialog.destroy()
            except Exception as e:
                loading_dialog.destroy()
                messagebox.showerror("Hata", f"E-posta şablonu oluşturulurken hata oluştu: {str(e)}")
        
        threading.Thread(target=generate_email, daemon=True).start()
    
    def show_email_template(self, company_info):
        """Show email template dialog for the selected company"""
        if not hasattr(self, 'email_generator') or not self.email_generator.is_configured:
            self.initialize_email_generator()
            
        if not hasattr(self, 'email_generator') or not self.email_generator.is_configured:
            messagebox.showerror("Hata", "E-posta şablonu oluşturulamadı. API ayarlarını kontrol edin.")
            return
            
        # First, analyze the company information
        company_analysis = self.email_generator.analyze_company_info(company_info)
        
        # Then, get the email template based on this analysis
        email_template = self.email_generator.generate_email_from_analysis(company_info, company_analysis)
        
        # Create a top-level window
        dialog = tk.Toplevel(self.master)
        dialog.title(f"E-posta Şablonu - {company_info.get('FirmaAdı', '')}")
        dialog.geometry("800x650")
        dialog.minsize(600, 400)
        
        # Create a frame for the content
        content_frame = tk.Frame(dialog)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add email template text with scrollbars
        email_label = tk.Label(content_frame, text="E-posta Şablonu:", anchor="w")
        email_label.pack(fill=tk.X, pady=(0, 5))
        
        email_frame = tk.Frame(content_frame)
        email_frame.pack(fill=tk.BOTH, expand=True)
        
        email_scrollbar = tk.Scrollbar(email_frame)
        email_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        email_text = tk.Text(email_frame, wrap=tk.WORD, yscrollcommand=email_scrollbar.set)
        email_text.pack(fill=tk.BOTH, expand=True)
        email_text.insert(tk.END, email_template)
        email_text.config(state=tk.NORMAL)
        
        email_scrollbar.config(command=email_text.yview)
        
        # Add analysis text below the email template
        analysis_frame = tk.LabelFrame(content_frame, text="Firma Analizi:", padx=5, pady=5)
        analysis_frame.pack(fill=tk.X, pady=10)
        
        analysis_text = tk.Text(analysis_frame, wrap=tk.WORD, height=4)
        analysis_text.pack(fill=tk.X, expand=True)
        analysis_text.insert(tk.END, company_analysis)
        analysis_text.config(state=tk.NORMAL)
        
        # Show prompt used for analysis
        prompt_frame = tk.LabelFrame(content_frame, text="Kullanılan Prompt:", padx=5, pady=5)
        prompt_frame.pack(fill=tk.X, pady=10)
        
        # Build the actual prompt that was used (simplified version)
        company_name = company_info.get('FirmaAdı', '')
        analysis_prompt = f"""
Aşağıdaki firma bilgilerini analiz et ve bu firmanın ne iş yaptığını, 
güçlü yönlerini, ve dijital medya/yazılım ihtiyaçları olabilecek noktaları belirt.

Firma Adı: {company_name}
...
"""
        
        prompt_text = tk.Text(prompt_frame, wrap=tk.WORD, height=4)
        prompt_text.pack(fill=tk.X, expand=True)
        prompt_text.insert(tk.END, analysis_prompt)
        prompt_text.config(state=tk.NORMAL)
        
        # Add buttons frame
        button_frame = tk.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Copy button
        copy_button = tk.Button(
            button_frame, 
            text="Kopyala", 
            command=lambda: self.copy_to_clipboard(email_template)
        )
        copy_button.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_button = tk.Button(
            button_frame, 
            text="Kapat", 
            command=dialog.destroy
        )
        close_button.pack(side=tk.RIGHT, padx=5)
        
        # Center the dialog on the screen
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.update_idletasks()
        
        # Position the window in the center of the parent window
        x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        dialog.focus_set()
    
    def request_api_key(self):
        """Request Gemini API key from the user"""
        api_key_dialog = tk.Toplevel()
        api_key_dialog.title("Google Gemini API Anahtarı Gerekli")
        api_key_dialog.geometry("500x200")
        api_key_dialog.transient(self.master)
        api_key_dialog.grab_set()
        api_key_dialog.resizable(False, False)
        
        # Center dialog on screen
        api_key_dialog.update_idletasks()
        width = api_key_dialog.winfo_width()
        height = api_key_dialog.winfo_height()
        x = (api_key_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (api_key_dialog.winfo_screenheight() // 2) - (height // 2)
        api_key_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        ttk.Label(
            api_key_dialog, 
            text="E-posta şablonu oluşturmak için Google Gemini API anahtarı gereklidir.", 
            wraplength=450
        ).pack(pady=10, padx=20)
        
        ttk.Label(
            api_key_dialog,
            text="API anahtarınızı https://makersuite.google.com/app/apikey adresinden edinebilirsiniz.",
            wraplength=450
        ).pack(pady=5, padx=20)
        
        key_frame = ttk.Frame(api_key_dialog)
        key_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Label(key_frame, text="API Anahtarı:").pack(side="left")
        
        api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(key_frame, textvariable=api_key_var, width=50, show="*")
        self.api_key_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        button_frame = ttk.Frame(api_key_dialog)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        save_button = ttk.Button(button_frame, text="Kaydet", command=self.save_api_key)
        save_button.pack(side="right", padx=5)
        
        cancel_button = ttk.Button(button_frame, text="İptal", command=api_key_dialog.destroy)
        cancel_button.pack(side="right", padx=5)
    
    def save_api_key(self):
        """API anahtarını kaydet ve email generator'a ayarla"""
        key = self.api_key_entry.get().strip()
        if key:
            try:
                # API anahtarını dosyaya kaydet
                api_key_file = os.path.join(os.path.dirname(__file__), "api_key.txt")
                with open(api_key_file, "w") as f:
                    f.write(key)
                
                # Email generator'a API anahtarını ayarla
                self.email_generator.set_api_key(key)
                messagebox.showinfo("Başarılı", "API anahtarı kaydedildi")
            except Exception as e:
                messagebox.showerror("Hata", f"API anahtarı kaydedilirken hata oluştu: {str(e)}")
        else:
            messagebox.showwarning("Uyarı", "Lütfen API anahtarı girin")
    
    def search_data(self, event=None):
        search_term = self.search_var.get().lower()
        search_column = self.search_column_var.get()
        
        # Clear previous search highlight
        self.tree.selection_remove(self.tree.selection())
        
        if not search_term:
            return
            
        # Search in the dataframe
        if search_column == 'Tümü':
            # Search in all columns
            for i, (index, row) in enumerate(self.dataframe.iterrows()):
                found = False
                for col in self.dataframe.columns:
                    cell_value = str(row[col]).lower() if pd.notna(row[col]) else ""
                    if search_term in cell_value:
                        found = True
                        break
                
                if found:
                    item_id = self.tree.get_children()[i]
                    self.tree.selection_add(item_id)
                    self.tree.see(item_id)  # Scroll to the item
        else:
            # Search in specific column
            for i, (index, row) in enumerate(self.dataframe.iterrows()):
                cell_value = str(row[search_column]).lower() if pd.notna(row[search_column]) else ""
                if search_term in cell_value:
                    item_id = self.tree.get_children()[i]
                    self.tree.selection_add(item_id)
                    self.tree.see(item_id)  # Scroll to the item
    
    def export_data(self):
        if self.dataframe is None:
            messagebox.showinfo("Bilgi", "Dışa aktarılacak veri yok.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Verileri Dışa Aktar"
        )
        
        if file_path:
            try:
                self.dataframe.to_excel(file_path, index=False)
                messagebox.showinfo("Başarılı", f"Veriler başarıyla dışa aktarıldı:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Hata", f"Dışa aktarma sırasında hata oluştu:\n{str(e)}")


class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Firma Web Scraper")
        
        # Tam ekrana ayarla
        self.set_fullscreen()
        
        # Create styles
        self.style = ttk.Style()
        self.current_theme = "light"
        
        # Ana çerçeve oluştur (grid layout kullanarak)
        self.root.grid_columnconfigure(0, weight=1)  # Tüm boş alan ana çerçeveye
        self.root.grid_rowconfigure(0, weight=1)
        
        self.main_frame = ttk.Frame(root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.main_frame.grid_columnconfigure(1, weight=1)  # Sağ panel genişleyecek
        self.main_frame.grid_rowconfigure(0, weight=1)  # Satır yükseklikleri ayarlanabilir
        
        # Sol panel - Ayarlar
        self.left_panel = ttk.Frame(self.main_frame, padding=10)
        self.left_panel.grid(row=0, column=0, sticky="ns")
        
        # Sağ panel - Tabs
        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=5)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(0, weight=1)
        
        # Tab oluştur
        self.tabs = ttk.Notebook(self.right_panel)
        self.tabs.grid(row=0, column=0, sticky="nsew")
        
        # Tema ve kontrol butonları için üst çerçeve
        self.control_buttons_frame = ttk.Frame(self.left_panel)
        self.control_buttons_frame.pack(fill='x', pady=5)
        
        self.theme_button = ttk.Button(self.control_buttons_frame, text="🌙 Koyu Tema", command=self.toggle_theme)
        self.theme_button.pack(side=tk.LEFT, padx=5)
        
        # Başlat ve Durdur butonlarını tema butonunun yanına taşı
        self.start_button = ttk.Button(self.control_buttons_frame, text="▶️ Başlat", command=self.start_scraping)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(self.control_buttons_frame, text="⏹️ Durdur", command=self.stop_scraping, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Dosya seçme bölümü
        self.file_frame = ttk.LabelFrame(self.left_panel, text="Dosya Seçimi")
        self.file_frame.pack(fill='x', pady=10, padx=5)
        
        self.file_label = ttk.Label(self.file_frame, text="Excel dosyası seçin:")
        self.file_label.pack(fill='x', padx=5, pady=5)
        
        self.file_path = tk.StringVar()
        self.file_entry = ttk.Entry(self.file_frame, textvariable=self.file_path)
        self.file_entry.pack(fill='x', padx=5, pady=5)
        
        self.browse_button = ttk.Button(self.file_frame, text="Gözat", command=self.browse_file)
        self.browse_button.pack(fill='x', padx=5, pady=5)
        
        # Ayarlar bölümü
        self.settings_frame = ttk.LabelFrame(self.left_panel, text="Temel Ayarlar")
        self.settings_frame.pack(fill='x', pady=10, padx=5)
        
        self.delay_label = ttk.Label(self.settings_frame, text="İstekler arası gecikme (saniye):")
        self.delay_label.pack(fill='x', padx=5, pady=5)
        
        self.delay_var = tk.DoubleVar(value=2.0)
        self.delay_spinbox = ttk.Spinbox(self.settings_frame, from_=0.5, to=10.0, increment=0.5, textvariable=self.delay_var)
        self.delay_spinbox.pack(fill='x', padx=5, pady=5)
        
        self.google_search_var = tk.BooleanVar(value=True)
        self.google_search_check = ttk.Checkbutton(
            self.settings_frame, 
            text="Web sitesi olmayan firmalar için arama yap", 
            variable=self.google_search_var
        )
        self.google_search_check.pack(fill='x', padx=5, pady=5)

        # Google sonuç sırası seçimi
        self.google_result_label = ttk.Label(self.settings_frame, text="Arama sonuç sırası:")
        self.google_result_label.pack(fill='x', padx=5, pady=(10,5))

        self.google_result_options = ["1. sonuç", "2. sonuç", "3. sonuç", "4. sonuç", "5. sonuç"]
        self.google_result_menu = ttk.Combobox(
            self.settings_frame, 
            values=self.google_result_options,
            state="readonly"
        )
        self.google_result_menu.current(0)
        self.google_result_menu.pack(fill='x', padx=5, pady=5)
        
        # Sütun seçme bölümü
        self.columns_frame = ttk.LabelFrame(self.left_panel, text="Excel Sütun Ayarları")
        self.columns_frame.pack(fill='x', pady=10, padx=5)
        
        # Sütun eşleştirme
        self.column_setup = [
            {"name": "FirmaAdı", "label": "Firma Adı Sütunu:", "required": True},
            {"name": "WebSitesi", "label": "Web Sitesi Sütunu:", "required": True},
            {"name": "Mail", "label": "Mail Sütunu:", "required": False},
            {"name": "Instagram", "label": "Instagram Sütunu:", "required": False},
            {"name": "Linkedin", "label": "Linkedin Sütunu:", "required": False},
            {"name": "Telefon", "label": "Telefon Sütunu:", "required": False},
            {"name": "Adres", "label": "Adres Sütunu:", "required": False},
            {"name": "Hakkımızda", "label": "Hakkımızda Sütunu:", "required": False}
        ]
        
        # Sütun eşleştirme UI öğelerini oluştur
        self.column_vars = {}
        self.column_checkboxes = {}
        
        for i, column in enumerate(self.column_setup):
            column_frame = ttk.Frame(self.columns_frame)
            column_frame.pack(fill='x', padx=5, pady=3)
            
            # Labeller
            ttk.Label(column_frame, text=column["label"], width=16).pack(side=tk.LEFT)
            
            # Giriş alanı
            self.column_vars[column["name"]] = tk.StringVar(value=column["name"])
            entry = ttk.Entry(column_frame, textvariable=self.column_vars[column["name"]], width=15)
            entry.pack(side=tk.LEFT, padx=5)
            
            # İşlem yapma seçeneği (sadece gerekli olmayanlar için)
            if not column["required"]:
                process_var = tk.BooleanVar(value=True)
                self.column_checkboxes[column["name"]] = process_var
                check = ttk.Checkbutton(
                    column_frame, 
                    text="Topla", 
                    variable=process_var
                )
                check.pack(side=tk.LEFT)
        
        # Arama format ayarları
        self.search_frame = ttk.LabelFrame(self.left_panel, text="Arama Format Ayarları")
        self.search_frame.pack(fill='x', pady=10, padx=5)
        
        # Email format
        self.email_label = ttk.Label(self.search_frame, text="Email Formatı:")
        self.email_label.pack(fill='x', padx=5, pady=5)
        
        self.email_format = tk.StringVar(value=r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.email_entry = ttk.Entry(self.search_frame, textvariable=self.email_format)
        self.email_entry.pack(fill='x', padx=5, pady=5)
        
        # Telefon format
        self.phone_label = ttk.Label(self.search_frame, text="Telefon Formatları:")
        self.phone_label.pack(fill='x', padx=5, pady=5)
        
        self.phone_format_frame = ttk.Frame(self.search_frame)
        self.phone_format_frame.pack(fill='x', padx=5, pady=5)
        
        self.phone_formats = [
            r'(?:\+90|0)?\s*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{2}[-.\s]?\d{2}',
            r'(?:\+90|0)?\s*\d{3}\s*\d{3}\s*\d{2}\s*\d{2}',
            r'(?:\+90|0)?\s*\d{3}\s*\d{3}\s*\d{4}'
        ]
        
        self.phone_vars = []
        self.phone_entries = []
        
        for i, pattern in enumerate(self.phone_formats):
            var = tk.StringVar(value=pattern)
            self.phone_vars.append(var)
            entry = ttk.Entry(self.phone_format_frame, textvariable=var)
            entry.pack(fill='x', pady=2)
            self.phone_entries.append(entry)
            
        # Yeni format ekle düğmesi
        self.add_format_button = ttk.Button(self.phone_format_frame, text="+ Format Ekle", command=self.add_phone_format)
        self.add_format_button.pack(fill='x', pady=5)
        
        # İlerleme çubuğu
        self.progress_frame = ttk.LabelFrame(self.left_panel, text="İşlem Durumu")
        self.progress_frame.pack(fill='x', pady=10, padx=5)
        
        # İlerleme çubuğu
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', padx=5, pady=5)
        
        # İlerleme yüzdesi
        self.progress_percent_var = tk.StringVar(value="0%")
        self.progress_percent_label = ttk.Label(self.progress_frame, textvariable=self.progress_percent_var)
        self.progress_percent_label.pack(anchor='e', padx=5)
        
        # Durum bilgileri grid
        self.status_grid = ttk.Frame(self.progress_frame)
        self.status_grid.pack(fill='x', padx=5, pady=5)
        
        status_items = [
            ("İşlem Durumu:", "status_var", "Hazır"),
            ("İşlenen Firma:", "current_company_var", "-"),
            ("İşlem Aşaması:", "process_stage_var", "-"),
            ("Kalan Firma:", "remaining_var", "-"),
            ("Son Bulunan:", "last_info_var", "-"),
            ("Tahmini Süre:", "estimated_time_var", "-")
        ]
        
        # Status labels oluştur
        for row, (label_text, var_name, default_value) in enumerate(status_items):
            ttk.Label(self.status_grid, text=label_text, font=("Arial", 8, "bold")).grid(row=row, column=0, sticky='w', pady=2)
            status_var = tk.StringVar(value=default_value)
            setattr(self, var_name, status_var)
            ttk.Label(self.status_grid, textvariable=status_var).grid(row=row, column=1, sticky='w', pady=2, padx=5)
        
        # Tab sayfaları oluştur
        # Excel Önizleme Tabı
        self.preview_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.preview_tab, text="Excel Önizleme")
        self.preview_tab.grid_columnconfigure(0, weight=1)
        self.preview_tab.grid_rowconfigure(0, weight=1)
        
        # Excel önizleme içeriği
        self.preview_frame = ttk.Frame(self.preview_tab)
        self.preview_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)
        
        # Excel önizleme butonu
        self.preview_button_frame = ttk.Frame(self.preview_frame)
        self.preview_button_frame.grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        
        self.preview_button = ttk.Button(self.preview_button_frame, text="Excel Dosyasını Önizle", command=self.preview_excel)
        self.preview_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Excel data grid için frame
        self.preview_data_frame = ttk.Frame(self.preview_frame)
        self.preview_data_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.preview_data_frame.grid_columnconfigure(0, weight=1)
        self.preview_data_frame.grid_rowconfigure(0, weight=1)
        
        # Excel önizleme data grid
        self.preview_table = ExcelTableViewer(self.preview_data_frame)
        self.preview_table.grid(row=0, column=0, sticky="nsew")
        
        # Sonuçlar Tabı
        self.results_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.results_tab, text="Sonuçlar")
        self.results_tab.grid_columnconfigure(0, weight=1)
        self.results_tab.grid_rowconfigure(0, weight=1)
        
        # Sonuçlar içeriği
        self.results_frame = ttk.Frame(self.results_tab)
        self.results_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(0, weight=1)
        
        # Sonuç yükleme butonu
        self.results_button_frame = ttk.Frame(self.results_frame)
        self.results_button_frame.grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        
        self.load_results_button = ttk.Button(self.results_button_frame, text="Sonuçları Görüntüle", command=self.view_results)
        self.load_results_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Sonuç data grid için frame
        self.results_data_frame = ttk.Frame(self.results_frame)
        self.results_data_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.results_data_frame.grid_columnconfigure(0, weight=1)
        self.results_data_frame.grid_rowconfigure(0, weight=1)
        
        # Sonuçlar data grid
        self.results_table = ExcelTableViewer(self.results_data_frame)
        self.results_table.grid(row=0, column=0, sticky="nsew")
        
        # Log Tabı
        self.log_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.log_tab, text="İşlem Kayıtları")
        self.log_tab.grid_columnconfigure(0, weight=1)
        self.log_tab.grid_rowconfigure(0, weight=1)
        
        # Log metin alanı
        self.log_text = scrolledtext.ScrolledText(self.log_tab, height=10)
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Log otomatik kayan ayarı
        self.autoscroll_var = tk.BooleanVar(value=True)
        self.autoscroll_frame = ttk.Frame(self.log_tab)
        self.autoscroll_frame.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        self.autoscroll_check = ttk.Checkbutton(
            self.autoscroll_frame, 
            text="Otomatik kaydırma", 
            variable=self.autoscroll_var
        )
        self.autoscroll_check.pack(side=tk.LEFT, padx=5)
        
        # İş parçacığı kontrolü
        self.running = False
        self.thread = None
        self.start_time = None
        self.last_processed_time = None
        
        # Log handler
        self.setup_logging()
        
        # Tema uygula
        self.apply_theme(self.current_theme)
    
    def set_fullscreen(self):
        """Uygulamayı tam ekran olarak ayarla"""
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        self.root.geometry(f"{width}x{height}+0+0")
        # Alt satır tam ekran için, üstteki satır pencere modu için
        #self.root.attributes("-fullscreen", True)
    
    def toggle_theme(self):
        """Açık ve koyu tema arasında geçiş yapar"""
        if self.current_theme == "light":
            self.current_theme = "dark"
            self.theme_button.config(text="☀️ Açık Tema")
            self.apply_theme("dark")
        else:
            self.current_theme = "light"
            self.theme_button.config(text="🌙 Koyu Tema")
            self.apply_theme("light")
    
    def apply_theme(self, theme_name):
        """Verilen tema ayarlarını uygular"""
        if theme_name == "dark":
            # Koyu tema için TTK tema ayarı
            if 'azure-dark' in self.style.theme_names():
                self.style.theme_use('azure-dark')
            elif 'equilux' in self.style.theme_names():
                self.style.theme_use('equilux')
            elif 'black' in self.style.theme_names():
                self.style.theme_use('black')
        else:
            # Açık tema için TTK tema ayarı
            if 'azure' in self.style.theme_names():
                self.style.theme_use('azure')
            else:
                self.style.theme_use('clam')

    def add_phone_format(self):
        """Yeni telefon formatı alanı ekle"""
        var = tk.StringVar(value=r'')
        self.phone_vars.append(var)
        entry = ttk.Entry(self.phone_format_frame, textvariable=var)
        entry.pack(fill='x', pady=2, before=self.add_format_button)
        self.phone_entries.append(entry)
    
    def browse_file(self):
        """Excel dosyası seç"""
        file_path = filedialog.askopenfilename(
            title="Excel Dosyası Seç",
            filetypes=[("Excel Dosyaları", "*.xlsx *.xls")]
        )
        if file_path:
            self.file_path.set(file_path)
            self.logger.info(f"Dosya seçildi: {file_path}")
    
    def preview_excel(self):
        """Excel dosyasını önizleme tab'ında göster"""
        if not self.file_path.get():
            messagebox.showerror("Hata", "Lütfen bir Excel dosyası seçin!")
            return
            
        if not os.path.exists(self.file_path.get()):
            messagebox.showerror("Hata", "Seçilen dosya bulunamadı!")
            return
            
        try:
            # Excel dosyasını oku
            df = pd.read_excel(self.file_path.get())
            self.logger.info(f"Excel dosyası başarıyla okundu: {len(df)} satır.")
            
            # Tabloyu doldur
            self.preview_table.load_dataframe(df)
            
            # Excel önizleme tab'ına geç
            self.tabs.select(self.preview_tab)
            
        except Exception as e:
            self.logger.error(f"Excel dosyası okunamadı: {str(e)}")
            messagebox.showerror("Hata", f"Excel dosyası okunamadı: {str(e)}")
    
    def view_results(self):
        """Son oluşturulan Excel dosyasını sonuçlar tab'ında görüntüle"""
        if not self.file_path.get():
            messagebox.showerror("Hata", "Önce bir Excel dosyası seçmelisiniz!")
            return
            
        # Son işlem dosyasının yolunu oluştur
        output_file = os.path.splitext(self.file_path.get())[0] + "_updated.xlsx"
        
        if not os.path.exists(output_file):
            messagebox.showerror("Hata", f"Sonuç dosyası bulunamadı: {output_file}")
            return
            
        try:
            # Excel dosyasını oku
            df = pd.read_excel(output_file)
            self.logger.info(f"Sonuç dosyası başarıyla okundu: {len(df)} satır.")
            
            # Tabloyu doldur
            self.results_table.load_dataframe(df)
            
            # Sonuçlar tab'ına geç
            self.tabs.select(self.results_tab)
            
        except Exception as e:
            self.logger.error(f"Sonuç dosyası okunamadı: {str(e)}")
            messagebox.showerror("Hata", f"Sonuç dosyası okunamadı: {str(e)}")
    
    def start_scraping(self):
        """Veri çekme işlemini başlat"""
        if not self.file_path.get():
            messagebox.showerror("Hata", "Lütfen bir Excel dosyası seçin!")
            return
            
        if not os.path.exists(self.file_path.get()):
            messagebox.showerror("Hata", "Seçilen dosya bulunamadı!")
            return
            
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Durum değişkenlerini sıfırla
        self.process_stage_var.set("Başlatılıyor")
        self.current_company_var.set("-")
        self.remaining_var.set("-")
        self.last_info_var.set("-")
        self.estimated_time_var.set("Hesaplanıyor...")
        self.progress_percent_var.set("0%")
        
        # Başlangıç zamanı
        self.start_time = time.time()
        self.last_processed_time = self.start_time
        
        # İşlemi ayrı bir thread'de başlat
        self.thread = threading.Thread(target=self.scrape_process)
        self.thread.daemon = True
        self.thread.start()
        
        # Log tab'ına geçiş yap
        self.tabs.select(self.log_tab)
    
    def stop_scraping(self):
        """Veri çekme işlemini durdur"""
        if messagebox.askyesno("Durdurma Onayı", "İşlemi durdurmak istediğinize emin misiniz?"):
            self.running = False
            self.status_var.set("Durduruluyor...")
            self.process_stage_var.set("İşlem durduruluyor")
            self.logger.info("İşlem kullanıcı tarafından durduruldu.")
    
    def scrape_process(self):
        """Veri çekme işlemi ana süreci"""
        try:
            self.logger.info("Scraping işlemi başlatıldı.")
            self.status_var.set("Excel dosyası okunuyor...")
            self.process_stage_var.set("Excel dosyası okunuyor")
            
            # Excel dosyasını oku
            try:
                df = pd.read_excel(self.file_path.get())
                self.logger.info(f"Dosya başarıyla okundu: {len(df)} satır.")
            except Exception as e:
                self.logger.error(f"Excel dosyası okunamadı: {str(e)}")
                messagebox.showerror("Hata", f"Excel dosyası okunamadı: {str(e)}")
                self.reset_ui()
                return
            
            # Kullanıcının belirlediği sütun adlarını al
            column_mapping = {name: self.column_vars[name].get() for name in self.column_vars}
            
            # Seçilen sütunlar ve kontrol
            required_columns = [column_mapping['FirmaAdı'], column_mapping['WebSitesi']]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.logger.error(f"Excel dosyasında gerekli sütunlar bulunamadı: {', '.join(missing_columns)}")
                messagebox.showerror("Hata", f"Excel dosyasında gerekli sütunlar bulunamadı: {', '.join(missing_columns)}")
                self.reset_ui()
                return
            
            # İşlenecek sütunları belirle
            process_columns = {}
            for name, var_name in column_mapping.items():
                # Gerekli sütunlar her zaman işlenir
                if name in ['FirmaAdı', 'WebSitesi']:
                    process_columns[name] = True
                # Diğer sütunlar için checkbox kontrolü
                elif name in self.column_checkboxes:
                    process_columns[name] = self.column_checkboxes[name].get()
                else:
                    process_columns[name] = False
            
            # Format regex'lerini al
            email_pattern = self.email_format.get()
            phone_patterns = [var.get() for var in self.phone_vars if var.get().strip()]
            
            # Google araması için sonuç sırasını al
            google_result_index = self.google_result_menu.current()
            
            # Gerekli sütunlar yoksa ekle
            for original_name, excel_name in column_mapping.items():
                if process_columns[original_name] and excel_name not in df.columns:
                    df[excel_name] = None
            
            # Sonuç dosyası adını hazırla
            output_file = os.path.splitext(self.file_path.get())[0] + "_updated.xlsx"
            
            total_rows = len(df)
            processed_rows = 0
            self.remaining_var.set(f"{total_rows}")
            
            # Her firma için işlem yap
            for idx, row in df.iterrows():
                if not self.running:
                    break
                
                # İşleme süresi hesapla
                current_time = time.time()
                if processed_rows > 0:
                    time_per_company = (current_time - self.start_time) / processed_rows
                    remaining_time = time_per_company * (total_rows - processed_rows)
                    
                    # Kalan süreyi formatlı göster
                    if remaining_time < 60:
                        time_str = f"{int(remaining_time)} saniye"
                    elif remaining_time < 3600:
                        time_str = f"{int(remaining_time / 60)} dakika {int(remaining_time % 60)} saniye"
                    else:
                        time_str = f"{int(remaining_time / 3600)} saat {int((remaining_time % 3600) / 60)} dakika"
                    
                    self.estimated_time_var.set(time_str)
                    
                    # İşlem hızını hesapla
                    if current_time - self.last_processed_time > 0:
                        speed = 1 / (current_time - self.last_processed_time)
                        self.speed_var.set(f"{speed:.2f} firma/saniye") if hasattr(self, 'speed_var') else None
                    
                self.last_processed_time = current_time
                    
                # Sütun adlarını kullanıcının ayarladığı şekilde kullan
                company_name = row[column_mapping['FirmaAdı']]
                website = row[column_mapping['WebSitesi']]
                
                # Durumu güncelle
                self.status_var.set(f"İşleniyor: {company_name}")
                self.current_company_var.set(f"{company_name}")
                self.remaining_var.set(f"{total_rows - processed_rows - 1}")
                self.logger.info(f"İşleniyor: {company_name}")
                
                # Boş firma adlarını atla
                if pd.isna(company_name) or not company_name.strip():
                    self.logger.warning(f"Satır {idx+2}: Firma adı boş, atlanıyor.")
                    continue
                    
                # Web sitesi yoksa arama yap
                if (pd.isna(website) or not website.strip()) and self.google_search_var.get():
                    self.process_stage_var.set("Google araması yapılıyor")
                    self.logger.info(f"{company_name} için Google araması yapılıyor... ({google_result_index+1}. sonuç istenmiş)")
                    website = find_website_via_google(company_name, result_index=google_result_index)
                    df.at[idx, column_mapping['WebSitesi']] = website
                    self.logger.info(f"Bulunan site: {website}")
                    time.sleep(self.delay_var.get())  # Limit aşımını engelle
                
                # Web sitesinden bilgi çek
                if website and website.strip():
                    self.process_stage_var.set("Web sitesi taranıyor")
                    self.logger.info(f"{company_name} için web sitesi taranıyor: {website}")
                    
                    # Kullanıcı tanımlı formatları ilet
                    company_data = scrape_company_website(
                        website, 
                        email_pattern=email_pattern, 
                        phone_patterns=phone_patterns
                    )
                    
                    # DataFrame'i güncelle
                    data_found = []
                    for original_col, excel_col in column_mapping.items():
                        if process_columns.get(original_col, False) and original_col in company_data and company_data[original_col]:
                            df.at[idx, excel_col] = company_data[original_col]
                            data_found.append(original_col)
                    
                    # Bulunan bilgileri logla
                    if data_found:
                        self.logger.info(f"Bulunan bilgiler: {', '.join(data_found)}")
                        self.last_info_var.set(f"Bulunan: {', '.join(data_found)}")
                    else:
                        self.logger.info("Hiç veri bulunamadı")
                        self.last_info_var.set("Hiç veri bulunamadı")
                            
                    # Düzenli kaydet
                    if idx % 5 == 0:
                        self.process_stage_var.set("İlerleme kaydediliyor")
                        df.to_excel(output_file, index=False)
                        self.logger.info(f"Ara ilerleme kaydedildi: {output_file}")
                        
                    time.sleep(self.delay_var.get())  # İstekler arası gecikme
                else:
                    self.logger.warning(f"{company_name} için web sitesi bulunamadı.")
                
                # İlerlemeyi güncelle
                processed_rows += 1
                progress = (processed_rows / total_rows) * 100
                self.progress_var.set(progress)
                self.progress_percent_var.set(f"%{progress:.1f}")
                
            # Son sonuçları kaydet
            self.process_stage_var.set("Sonuçlar kaydediliyor")
            df.to_excel(output_file, index=False)
            
            # Toplam süreyi hesapla
            total_time = time.time() - self.start_time
            if total_time < 60:
                time_str = f"{total_time:.1f} saniye"
            elif total_time < 3600:
                time_str = f"{int(total_time / 60)} dakika {int(total_time % 60)} saniye"
            else:
                time_str = f"{int(total_time / 3600)} saat {int((total_time % 3600) / 60)} dakika"
            
            if self.running:
                self.logger.info(f"İşlem tamamlandı! Sonuçlar kaydedildi: {output_file}")
                self.logger.info(f"Toplam işlem süresi: {time_str}")
                self.status_var.set("Tamamlandı")
                self.process_stage_var.set("İşlem tamamlandı")
                self.estimated_time_var.set("-")
                
                # Sonuçları görüntülemek isteyip istemediğini sor
                if messagebox.askyesno("Başarılı", f"İşlem tamamlandı!\nSonuçlar kaydedildi: {output_file}\nToplam süre: {time_str}\n\nSonuçları görüntülemek ister misiniz?"):
                    self.view_results()
            else:
                self.logger.info(f"İşlem durduruldu! Kısmi sonuçlar kaydedildi: {output_file}")
                self.logger.info(f"Geçen süre: {time_str}")
                self.status_var.set("Durduruldu")
                self.process_stage_var.set("İşlem durduruldu")
                messagebox.showinfo("Bilgi", f"İşlem durduruldu!\nKısmi sonuçlar kaydedildi: {output_file}\nGeçen süre: {time_str}")
            
        except Exception as e:
            self.logger.error(f"İşlem sırasında hata oluştu: {str(e)}")
            self.process_stage_var.set("HATA")
            messagebox.showerror("Hata", f"İşlem sırasında hata oluştu: {str(e)}")
            
        finally:
            self.reset_ui()
    
    def reset_ui(self):
        """Arayüzü sıfırla"""
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def setup_logging(self):
        # Create custom handler to redirect logs to the text widget
        class TextHandler(logging.Handler):
            def __init__(self, text_widget, autoscroll_var, app):
                logging.Handler.__init__(self)
                self.text_widget = text_widget
                self.autoscroll_var = autoscroll_var
                self.app = app
                
            def emit(self, record):
                msg = self.format(record)
                def append():
                    self.text_widget.configure(state='normal')
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.configure(state='disabled')
                    
                    # Update status info based on log message
                    if "için Google araması yapılıyor" in msg:
                        self.app.process_stage_var.set("Google araması yapılıyor")
                    elif "için web sitesi taranıyor" in msg:
                        self.app.process_stage_var.set("Web sitesi taranıyor")
                    elif "Bulunan site:" in msg:
                        site = msg.split("Bulunan site:")[-1].strip()
                        self.app.last_info_var.set(f"Web sitesi: {site}")
                    elif "Mail:" in msg:
                        self.app.last_info_var.set(f"E-posta bulundu")
                    elif "Telefon:" in msg:
                        self.app.last_info_var.set(f"Telefon bulundu")
                    
                    # Autoscroll if enabled
                    if self.autoscroll_var.get():
                        self.text_widget.yview(tk.END)
                        
                self.text_widget.after(0, append)
        
        # Configure the logger
        self.logger = logging.getLogger("GUI_Logger")
        self.logger.setLevel(logging.INFO)
        
        # Add text handler
        text_handler = TextHandler(self.log_text, self.autoscroll_var, self)
        text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(text_handler)
        
        # Also log to file
        file_handler = logging.FileHandler('gui_scraper.log')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()
