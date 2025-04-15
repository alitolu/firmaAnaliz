import os
import google.generativeai as genai
import logging
from gemini_client import GeminiClient

class GeminiEmailGenerator:
    """Gemini API kullanarak firma bilgilerine göre e-posta şablonu oluşturan sınıf"""
    
    def __init__(self):
        # GeminiClient'ı kullanarak API yapılandırması yapacağız
        self.client = GeminiClient()
        # Durumu al
        self.api_key = self.client.api_key
        self.is_configured = self.client.is_configured
        self.logger = logging.getLogger("Gemini_API")
        
        # Dosyadan API anahtarını yüklemeyi dene
        if not self.is_configured:
            self._load_api_key_from_file()
    
    def _load_api_key_from_file(self):
        """Dosyadan API anahtarını yükle"""
        self.client._load_api_key_from_file()
        self.api_key = self.client.api_key
        self.is_configured = self.client.is_configured
    
    def set_api_key(self, api_key, model=None):
        """API anahtarını ayarla ve yapılandırmayı doğrula"""
        success = self.client.set_api_key(api_key, model)
        if success:
            self.api_key = self.client.api_key
            self.is_configured = True
        return success
    
    def analyze_company_info(self, company_info):
        """Firma bilgilerini analiz eder ve bir özet rapor döndürür"""
        if not self.is_configured:
            self.logger.error("API yapılandırılmadı, analiz yapılamıyor")
            return "API yapılandırılmadı, analiz yapılamıyor. Lütfen API anahtarını kontrol edin."
        
        try:
            # Firma bilgilerini bir metin haline getir
            company_name = company_info.get('FirmaAdı', 'Bilinmeyen Firma')
            website = company_info.get('WebSitesi', '')
            about = company_info.get('Hakkımızda', '')
            
            # Prompt oluştur
            prompt = f"""
            Aşağıdaki firma bilgilerini analiz et ve bu firmanın ne iş yaptığını, 
            güçlü yönlerini ve dijital medya/yazılım ihtiyaçlarını kısaca 3-5 cümle ile özetle.
            
            Firma Adı: {company_name}
            Web Sitesi: {website}
            Hakkında: {about}
            
            Yanıtını sadece özet bilgi olarak ver, ekstra açıklama yapma.
            """
            
            # Sistem talimatı oluştur
            system_instruction = "Sen profesyonel bir şirket analisti ve B2B pazarlama uzmanısın."
            
            # API isteği gönder
            result = self.client.generate_content(prompt, system_instruction)
            return result
                
        except Exception as e:
            self.logger.error(f"Firma analizi sırasında hata oluştu: {str(e)}")
            return f"Hata: {str(e)}"
    
    def generate_email_from_analysis(self, company_info, analysis):
        """Firma analizi ve bilgilerine dayanarak e-posta şablonu oluşturur"""
        if not self.is_configured:
            self.logger.error("API yapılandırılmadı, e-posta şablonu oluşturulamıyor")
            return "API yapılandırılmadı, e-posta şablonu oluşturulamıyor. Lütfen API anahtarını kontrol edin."
        
        try:
            company_name = company_info.get('FirmaAdı', 'Değerli İşletme')
            
            # Prompt oluştur
            prompt = f"""
            Aşağıdaki firma analizi temelinde, bu firmaya dijital pazarlama ve yazılım hizmetleri 
            sunmak için profesyonel bir satış e-postası oluştur:
            
            Firma: {company_name}
            Analiz: {analysis}
            
            E-posta şu kriterleri karşılamalıdır:
            1. Türkçe olmalı
            2. Resmi bir dil kullanmalı
            3. Bu analize göre firmanın ihtiyaçlarına odaklanmalı
            4. Dijital pazarlama ve yazılım hizmetleri sunmalı 
            5. Somut çözümler ve faydalar içermeli
            6. Kısa ve öz olmalı (max 250 kelime)
            7. Konu başlığını belirt
            8. Profesyonel hitap cümlesi ve kapanış cümlesi içermeli
            9. İmza bölümünü ve iletişim bilgilerini ekle
            
            E-posta şablonunu doğrudan ver, açıklamalar yapma.
            """
            
            # Sistem talimatı oluştur
            system_instruction = "Sen profesyonel bir B2B satış temsilcisisin."
            
            # API isteği gönder  
            result = self.client.generate_content(prompt, system_instruction)
            return result
                
        except Exception as e:
            self.logger.error(f"E-posta şablonu oluşturulurken hata oluştu: {str(e)}")
            return f"Hata: {str(e)}"


# Test fonksiyonu
def test_email_generator():
    generator = GeminiEmailGenerator()
    if generator.is_configured:
        print("API yapılandırıldı!")
        
        # Test firma bilgileri
        company_info = {
            "FirmaAdı": "Test Firma A.Ş.",
            "WebSitesi": "https://www.testfirma.com",
            "Hakkımızda": "Yazılım geliştirme ve danışmanlık hizmetleri sunuyoruz."
        }
        
        # Analiz yap
        analysis = generator.analyze_company_info(company_info)
        print("\nFirma Analizi:")
        print(analysis)
        
        # E-posta şablonu oluştur
        email = generator.generate_email_from_analysis(company_info, analysis)
        print("\nE-posta Şablonu:")
        print(email)
    else:
        print("API yapılandırılamadı. Lütfen API anahtarınızı kontrol edin.")


if __name__ == "__main__":
    # Test etmek için bu betik doğrudan çalıştırıldığında
    test_email_generator()