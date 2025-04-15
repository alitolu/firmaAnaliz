from tkinter import Tk, Menu, messagebox
from gemini_gui import GeminiEmailGUI

class FirmaScraper:
    def __init__(self, root: Tk):
        self.root = root
        self.menubar = Menu(self.root)
        self.root.config(menu=self.menubar)
        self.init_menu()

    def init_menu(self):
        self.menubar.add_command(label="Gemini E-posta Şablonu", command=self.open_gemini_email_gui)

    def open_gemini_email_gui(self):
        """Gemini E-posta şablonu oluşturma arayüzünü açar"""
        try:
            gemini_window = GeminiEmailGUI(self.root)
            gemini_window.window.transient(self.root)  # Ana pencereye bağlı
            gemini_window.window.grab_set()  # Odağı bu pencereye ver
        except Exception as e:
            self.log_operation(f"Gemini E-posta şablonu arayüzü açılırken hata: {str(e)}", "error")
            messagebox.showerror("Hata", f"Gemini E-posta şablonu arayüzü açılamadı: {str(e)}")

    def log_operation(self, message: str, level: str = "info"):
        """Log işlemleri için basit bir method"""
        print(f"[{level.upper()}] {message}")