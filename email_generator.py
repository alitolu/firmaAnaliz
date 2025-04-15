import os
import json
import logging
from typing import Dict, Any, Optional
from gemini_client import GeminiClient

class EmailGenerator:
    def __init__(self):
        # GeminiClient'ı kullanarak API yapılandırması
        self.gemini_client = GeminiClient()
        # API durumu
        self.is_configured = False
        # Logger oluştur
        self.logger = logging.getLogger("EmailGenerator")
        self._load_api_key()
        
    def _load_api_key(self):
        """API anahtarını dosyadan yüklemeyi dene"""
        self.gemini_client._load_api_key_from_file()
        self.is_configured = self.gemini_client.is_configured
        
    def load_prompts(self) -> None:
        """JSON dosyasından tüm promptları yükle"""
        # GeminiClient zaten promptları yükleyecek
        self.gemini_client.load_prompts()
            
    def configure(self, api_key: str, model: str = "gemini-1.0-pro") -> bool:
        """Configure the API key and model"""
        success = self.gemini_client.set_api_key(api_key, model)
        self.is_configured = success
        return success
        
    def get_prompt(self, prompt_key: str, replacements: Dict[str, str] = None) -> str:
        """Belirtilen prompt'u getir ve değişkenleri doldur"""
        return self.gemini_client.get_prompt(prompt_key, replacements)

    def analyze_company_info(self, company_info: Dict[str, Any]) -> str:
        """Analyze company information using Gemini API"""
        if not self.is_configured:
            return "API yapılandırılmamış. Önce configure() metodunu çağırın."
        
        try:
            replacements = {
                "firma_adi": company_info.get("FirmaAdı", ""),
                "faaliyet_alani": company_info.get("FaaliyetAlanı", ""),
                "website": company_info.get("Website", ""),
                "aciklama": company_info.get("Açıklama", ""),
                "urun_hizmetler": company_info.get("ÜrünHizmetler", "")
            }
            
            prompt = self.get_prompt("gemini_analysis", replacements)
            
            # Gemini API'yi kullanarak içerik oluştur
            system_instruction = "Sen profesyonel bir şirket analisti ve B2B pazarlama uzmanısın."
            result = self.gemini_client.generate_content(prompt, system_instruction)
            
            return result
        except Exception as e:
            self.logger.error(f"Analiz sırasında hata oluştu: {str(e)}")
            return f"Analiz sırasında hata oluştu: {str(e)}"

    def generate_email_from_analysis(self, company_info: Dict[str, Any], analysis: str) -> str:
        """Generate an email template based on company information and analysis"""
        if not self.is_configured:
            return "API yapılandırılmamış. Önce configure() metodunu çağırın."
        
        try:
            replacements = {
                "firma_adi": company_info.get("FirmaAdı", ""),
                "faaliyet_alani": company_info.get("FaaliyetAlanı", ""),
                "website": company_info.get("Website", ""),
                "analiz": analysis,
                "yonetici_adi": company_info.get("YöneticiAdı", "")
            }
            
            prompt = self.get_prompt("email_template", replacements)
            
            # Gemini API'yi kullanarak içerik oluştur
            system_instruction = "Sen profesyonel bir B2B satış temsilcisisin."
            result = self.gemini_client.generate_content(prompt, system_instruction)
            
            return result
        except Exception as e:
            self.logger.error(f"E-posta şablonu oluşturulurken hata oluştu: {str(e)}")
            return f"E-posta şablonu oluşturulurken hata oluştu: {str(e)}"