import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pandas as pd
import logging
import os
import sys
from gemini_api import GeminiEmailGenerator

class GeminiEmailGUI:
    def __init__(self, parent_window=None):
        # Ana pencere ayarları
        self.window = tk.Toplevel(parent_window) if parent_window else tk.Tk()
        self.window.title("Gemini AI E-posta Şablonu Oluşturucu")
        self.window.geometry("900x700")
        
        # Logging yapılandırması
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("Gemini_GUI")
        
        # Gemini API işleyicisini oluştur
        self.email_generator = GeminiEmailGenerator()
        
        # Tema ayarları
        self.style = ttk.Style()
        self.style.theme_use('clam')  # 'clam', 'alt', 'default', 'classic'
        
        # API durumu
        self.is_api_configured = self.email_generator.is_configured
        
        # Ana çerçeve
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # API Yapılandırma Çerçevesi
        api_frame = ttk.LabelFrame(main_frame, text="API Yapılandırması", padding="10")
        api_frame.pack(fill=tk.X, pady=5)
        
        # API Anahtarı girişi
        ttk.Label(api_frame, text="Gemini API Anahtarı:").grid(column=0, row=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar()
        
        # API anahtarını yükle
        if self.email_generator.api_key:
            self.api_key_var.set(self.email_generator.api_key)
            self.is_api_configured = True
        
        self.api_key_entry = ttk.Entry(api_frame, width=50, textvariable=self.api_key_var)
        self.api_key_entry.grid(column=1, row=0, sticky=tk.W, padx=5)
        
        # API durum etiketi
        self.api_status_label = ttk.Label(api_frame, 
                                        text="API Durumu: " + ("Yapılandırıldı ✓" if self.is_api_configured else "Yapılandırılmadı ✗"), 
                                        foreground="green" if self.is_api_configured else "red")
        self.api_status_label.grid(column=0, row=1, columnspan=2, sticky=tk.W, pady=5)
        
        # API kaydet düğmesi
        ttk.Button(api_frame, text="API Anahtarını Kaydet ve Test Et", command=self.save_and_test_api_key).grid(column=2, row=0, padx=5)
        
        # Excel dosya seçimi
        excel_frame = ttk.LabelFrame(main_frame, text="Veri Kaynağı", padding="10")
        excel_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(excel_frame, text="Excel Dosyası:").grid(column=0, row=0, sticky=tk.W, pady=5)
        self.excel_path_var = tk.StringVar()
        self.excel_path_entry = ttk.Entry(excel_frame, width=50, textvariable=self.excel_path_var)
        self.excel_path_entry.grid(column=1, row=0, sticky=tk.W, padx=5)
        ttk.Button(excel_frame, text="Dosya Seç", command=self.select_excel_file).grid(column=2, row=0, padx=5)
        ttk.Button(excel_frame, text="Verileri Yükle", command=self.load_companies).grid(column=3, row=0, padx=5)
        
        # Firma seçimi
        company_frame = ttk.LabelFrame(main_frame, text="Firma Seçimi", padding="10")
        company_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(company_frame, text="Firma Seçin:").grid(column=0, row=0, sticky=tk.W, pady=5)
        self.company_var = tk.StringVar()
        self.company_combo = ttk.Combobox(company_frame, width=50, textvariable=self.company_var)
        self.company_combo.grid(column=1, row=0, sticky=tk.W, padx=5)
        self.company_combo.bind("<<ComboboxSelected>>", self.on_company_selected)
        
        # Firma bilgileri
        info_frame = ttk.LabelFrame(main_frame, text="Firma Bilgileri", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        info_frame.columnconfigure(1, weight=1)
        
        # Firma bilgi etiketleri
        ttk.Label(info_frame, text="Firma Adı:").grid(column=0, row=0, sticky=tk.W, pady=2)
        self.company_name_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.company_name_var).grid(column=1, row=0, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="Web Sitesi:").grid(column=0, row=1, sticky=tk.W, pady=2)
        self.website_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.website_var).grid(column=1, row=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="Hakkında:").grid(column=0, row=2, sticky=tk.NW, pady=2)
        self.about_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, width=60, height=4)
        self.about_text.grid(column=1, row=2, sticky=(tk.W, tk.E), pady=2)
        self.about_text.config(state=tk.DISABLED)
        
        # E-posta içeriği
        email_frame = ttk.LabelFrame(main_frame, text="E-posta İçeriği", padding="10")
        email_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # E-posta oluşturma düğmesi
        ttk.Button(email_frame, text="E-posta Şablonu Oluştur", command=self.generate_email).pack(pady=5, anchor=tk.W)
        
        # E-posta içeriği metin kutusu
        self.email_text = scrolledtext.ScrolledText(email_frame, wrap=tk.WORD, width=80, height=15)
        self.email_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Alt kısım düğmeleri
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Kopyala", command=self.copy_to_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Kaydet", command=self.save_email).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Temizle", command=self.clear_email).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Kapat", command=self.close_window).pack(side=tk.RIGHT, padx=5)
        
        # Veri depolaması
        self.companies_data = None
        self.selected_company_data = None
        
        # API durumunu kontrol et ve göster
        if self.is_api_configured:
            self.logger.info("API anahtarı başarıyla yüklendi ve yapılandırıldı")
            self.api_status_label.config(text="API Durumu: Yapılandırıldı ✓", foreground="green")
        else:
            self.logger.warning("API yapılandırılmadı, lütfen API anahtarını kontrol edin")
        
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)  # Pencere kapandığında yapılacak işlem
    
    def save_and_test_api_key(self):
        """API anahtarını kaydet ve doğrula, başarılı olursa pencereyi kapat"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Hata", "API anahtarı boş olamaz")
            return
        
        # Progressbar'ı göster ve başlat
        progress = ttk.Progressbar(self.window, mode='indeterminate')
        progress.pack(fill="x", padx=20, pady=5)
        progress.start(10)
        
        try:
            # Arka planda API anahtarını test et
            def test_api_key():
                is_valid = self.email_generator.set_api_key(api_key)
                self.window.after(0, lambda: self.handle_api_test_result(api_key, is_valid))
            
            import threading
            threading.Thread(target=test_api_key, daemon=True).start()
        except Exception as e:
            progress.stop()
            progress.pack_forget()
            messagebox.showerror("Hata", f"API anahtarı test edilirken hata: {str(e)}")
    
    def handle_api_test_result(self, api_key, is_valid):
        """API testi sonuçlarını işle"""
        if is_valid:
            try:
                # API anahtarını dosyaya kaydet
                api_key_file = r"api_key.txt"
                with open(api_key_file, "w") as f:
                    f.write(api_key)
                
                self.is_api_configured = True
                self.api_status_label.config(text="API Durumu: Yapılandırıldı ✓", foreground="green")
                messagebox.showinfo("Başarılı", "API anahtarı doğrulandı ve kaydedildi.")
                self.logger.info(f"API anahtarı başarıyla kaydedildi: {api_key_file}")
            except Exception as e:
                messagebox.showerror("Hata", f"API anahtarı dosyaya kaydedilirken hata: {str(e)}")
                self.logger.error(f"API anahtarı dosyaya kaydedilirken hata: {str(e)}")
        else:
            self.is_api_configured = False
            self.api_status_label.config(text="API Durumu: Yapılandırılmadı ✗", foreground="red")
            messagebox.showerror("Hata", "API anahtarı geçersiz veya API'ye erişilemiyor.")
            self.logger.error("API anahtarı geçersiz veya API'ye erişilemiyor")
    
    def select_excel_file(self):
        """Excel dosyası seçimi"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel Dosyaları", "*.xlsx *.xls")],
            title="Excel Dosyası Seçin"
        )
        
        if file_path:
            self.excel_path_var.set(file_path)
    
    def load_companies(self):
        """Excel dosyasından firma verilerini yükle"""
        file_path = self.excel_path_var.get().strip()
        
        if not file_path:
            messagebox.showerror("Hata", "Lütfen önce bir Excel dosyası seçin")
            return
        
        try:
            # Excel dosyasını oku
            df = pd.read_excel(file_path)
            
            # Firmaların adlarını alarak Combobox'a ekle
            if 'FirmaAdı' in df.columns:
                self.companies_data = df
                company_names = df['FirmaAdı'].tolist()
                self.company_combo['values'] = company_names
                
                if len(company_names) > 0:
                    messagebox.showinfo("Başarılı", f"{len(company_names)} firma yüklendi!")
                    self.company_combo.current(0)
                    self.on_company_selected(None)  # İlk firmayı seç
                else:
                    messagebox.showwarning("Uyarı", "Dosyada firma bulunamadı")
            else:
                messagebox.showerror("Hata", "Excel dosyasında 'FirmaAdı' sütunu bulunamadı")
        
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya yüklenirken hata oluştu: {str(e)}")
    
    def on_company_selected(self, event):
        """Firma seçildiğinde bilgileri göster"""
        selected_company = self.company_var.get()
        
        if selected_company and self.companies_data is not None:
            # Seçilen firmanın verilerini al
            company_data = self.companies_data[self.companies_data['FirmaAdı'] == selected_company]
            
            if not company_data.empty:
                # İlk satırı al (aynı isimde birden fazla firma olabileceği için)
                company_row = company_data.iloc[0]
                self.selected_company_data = company_row.to_dict()
                
                # Firma bilgilerini göster
                self.company_name_var.set(selected_company)
                
                website = company_row.get('WebSitesi', '') if 'WebSitesi' in company_row else ''
                self.website_var.set(website if pd.notna(website) else '')
                
                about = company_row.get('Hakkımızda', '') if 'Hakkımızda' in company_row else ''
                self.about_text.config(state=tk.NORMAL)
                self.about_text.delete(1.0, tk.END)
                self.about_text.insert(tk.END, about if pd.notna(about) else '')
                self.about_text.config(state=tk.DISABLED)
    
    def generate_email(self):
        """Seçilen firma için e-posta şablonu oluştur"""
        if not self.is_api_configured:
            messagebox.showerror("Hata", "Lütfen önce API anahtarını yapılandırın")
            return
        
        if not self.selected_company_data:
            messagebox.showerror("Hata", "Lütfen önce bir firma seçin")
            return
        
        try:
            # Önce firma analizini yap
            analysis = self.email_generator.analyze_company_info(self.selected_company_data)
            
            # Analiz temelinde e-posta şablonu oluştur
            email_template = self.email_generator.generate_email_from_analysis(
                self.selected_company_data, analysis
            )
            
            # E-posta şablonunu göster
            self.email_text.delete(1.0, tk.END)
            self.email_text.insert(tk.END, email_template)
        
        except Exception as e:
            messagebox.showerror("Hata", f"E-posta şablonu oluşturulurken hata: {str(e)}")
    
    def copy_to_clipboard(self):
        """E-posta metnini panoya kopyala"""
        email_content = self.email_text.get(1.0, tk.END)
        if email_content.strip():
            self.window.clipboard_clear()
            self.window.clipboard_append(email_content)
            messagebox.showinfo("Bilgi", "E-posta içeriği panoya kopyalandı")
        else:
            messagebox.showwarning("Uyarı", "Kopyalanacak içerik bulunamadı")
    
    def save_email(self):
        """E-posta şablonunu dosyaya kaydet"""
        email_content = self.email_text.get(1.0, tk.END)
        if not email_content.strip():
            messagebox.showwarning("Uyarı", "Kaydedilecek içerik bulunamadı")
            return
        
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Metin Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")],
            title="E-posta Şablonunu Kaydet"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(email_content)
                messagebox.showinfo("Başarılı", "E-posta şablonu başarıyla kaydedildi")
            except Exception as e:
                messagebox.showerror("Hata", f"Dosya kaydedilirken hata: {str(e)}")
    
    def clear_email(self):
        """E-posta içeriğini temizle"""
        self.email_text.delete(1.0, tk.END)
    
    def close_window(self):
        """Pencereyi kapat"""
        self.window.destroy()

# Bağımsız modül olarak çalıştırılırsa
if __name__ == "__main__":
    app = GeminiEmailGUI()
    app.window.mainloop()