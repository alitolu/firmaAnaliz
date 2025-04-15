import requests
import os
import json
import logging
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from gemini_client import GeminiClient

class WebScraper:
    def __init__(self):
        # GeminiClient'ı kullanarak API yapılandırması
        self.gemini_client = GeminiClient()
        # Logger oluştur
        self.logger = logging.getLogger("WebScraper")
        
    def load_prompts(self) -> None:
        """JSON dosyasından tüm promptları yükle"""
        # GeminiClient zaten promptları yükleyecek
        self.gemini_client.load_prompts()
            
    def configure(self, api_key: str, model: str = "gemini-1.0-pro") -> None:
        """Configure the API key and model"""
        success = self.gemini_client.set_api_key(api_key, model)
        return success
        
    def get_prompt(self, prompt_key: str, replacements: Dict[str, str] = None) -> str:
        """Belirtilen prompt'u getir ve değişkenleri doldur"""
        return self.gemini_client.get_prompt(prompt_key, replacements)

    def fetch_website_content(self, url: str) -> str:
        """Fetch content from a website URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Web sitesi içeriği alınırken hata: {str(e)}")
            return f"Web sitesi içeriği alınırken hata: {str(e)}"

    def extract_company_info(self, html_content: str, url: str = "") -> Dict[str, Any]:
        """Extract company information from website HTML content"""
        if not self.gemini_client.is_configured:
            return {"error": "API yapılandırılmamış. Önce configure() metodunu çağırın."}
            
        try:
            # Basit HTML temizleme ve kısaltma
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Meta tag'lerden açıklama ve anahtar kelimeleri çıkar
            meta_description = ""
            meta_keywords = ""
            
            meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_desc_tag and 'content' in meta_desc_tag.attrs:
                meta_description = meta_desc_tag['content']
                
            meta_kw_tag = soup.find('meta', attrs={'name': 'keywords'})
            if meta_kw_tag and 'content' in meta_kw_tag.attrs:
                meta_keywords = meta_kw_tag['content']
            
            # Gereksiz etiketleri kaldır
            for tag in soup(['script', 'style', 'svg', 'noscript', 'iframe', 'img']):
                tag.decompose()
            
            # Ana içeriğe odaklan
            main_content = soup.body
            if not main_content:
                main_content = soup
                
            # İçeriği temizle ve kısalt
            text_content = main_content.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            cleaned_content = '\n'.join(lines[:300])  # İlk 300 satır
            
            # Özet HTML içeriğini hazırla
            simplified_html = f"""
            <html>
            <head>
                <meta name="description" content="{meta_description}">
                <meta name="keywords" content="{meta_keywords}">
                <title>{soup.title.string if soup.title else ""}</title>
            </head>
            <body>
                {cleaned_content}
            </body>
            </html>
            """
            
            replacements = {
                "html_content": simplified_html
            }
            
            prompt = self.get_prompt("web_scraping", replacements)
            
            # Gemini API'yi kullanarak içerik oluştur
            system_instruction = "Sen web sayfalarından firma bilgilerini çıkaran bir uzmansın. JSON formatında bilgi çıkartabilirsin."
            result_text = self.gemini_client.generate_content(prompt, system_instruction)
            
            # JSON yanıtını işle
            try:
                # JSON bloğunu çıkart
                if '```json' in result_text and '```' in result_text.split('```json', 1)[1]:
                    json_str = result_text.split('```json', 1)[1].split('```', 1)[0]
                elif '{' in result_text and '}' in result_text:
                    json_start = result_text.find('{')
                    json_end = result_text.rfind('}') + 1
                    json_str = result_text[json_start:json_end]
                else:
                    json_str = result_text
                    
                company_data = json.loads(json_str)
                
                # Format anahtarları standardize et
                formatted_data = {}
                key_mappings = {
                    "Firma Adı": "FirmaAdı",
                    "Firma adı": "FirmaAdı",
                    "İsim": "FirmaAdı",
                    "Şirket Adı": "FirmaAdı",
                    "Şirket adı": "FirmaAdı",
                    "Faaliyet Alanı": "FaaliyetAlanı",
                    "Sektör": "FaaliyetAlanı",
                    "İş alanı": "FaaliyetAlanı",
                    "İletişim Bilgileri": "İletişimBilgileri",
                    "İletişim": "İletişimBilgileri",
                    "Açıklama": "Açıklama",
                    "Hakkında": "Açıklama",
                    "Şirket hakkında": "Açıklama",
                    "Açıklama/Hakkında": "Açıklama",
                    "Ürünler": "Ürünler",
                    "Hizmetler": "Hizmetler",
                    "Ürün/Hizmetler": "ÜrünHizmetler"
                }
                
                for key, value in company_data.items():
                    # Key standardizasyonu
                    standard_key = key_mappings.get(key, key)
                    formatted_data[standard_key] = value
                
                # Website bilgisini ekle
                if "Website" not in formatted_data and url:
                    url_parts = url.split('//')
                    domain = url_parts[1] if len(url_parts) > 1 else url_parts[0]
                    domain = domain.split('/')[0]
                    formatted_data["Website"] = domain
                    
                return formatted_data
                
            except json.JSONDecodeError:
                self.logger.error("API yanıtı JSON formatında değil")
                return {"error": "API yanıtı JSON formatında değil", "raw_response": result_text}
                
        except Exception as e:
            self.logger.error(f"Firma bilgileri çıkarılırken hata: {str(e)}")
            return {"error": f"Firma bilgileri çıkarılırken hata: {str(e)}"}

    def scrape_company_info(self, url: str) -> Dict[str, Any]:
        """Scrape company information from a URL"""
        html_content = self.fetch_website_content(url)
        if html_content.startswith("Web sitesi içeriği alınırken hata"):
            return {"error": html_content}
            
        return self.extract_company_info(html_content, url)