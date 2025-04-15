import os
import json
import logging
import google.generativeai as genai

class GeminiClient:
    """Google Gemini API ile etkileşim kuracak temel sınıf"""
    
    def __init__(self):
        self.api_key = None
        self.model = "gemini-pro"  # Güncel model adı
        self.is_configured = False
        self.prompts = {}
        self.logger = logging.getLogger("GeminiAPI")
        self.load_prompts()
        
    def load_prompts(self):
        """JSON dosyasından tüm promptları yükle"""
        try:
            prompt_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts.json")
            with open(prompt_file, "r", encoding="utf-8") as f:
                self.prompts = json.load(f)
            self.logger.info("Promptlar başarıyla yüklendi")
        except Exception as e:
            self.logger.error(f"Promptlar yüklenirken hata: {e}")
            # Dosya bulunamazsa varsayılan prompt kullanılacak
            self.prompts = {}
    
    def _load_api_key_from_file(self):
        """Dosyadan API anahtarını yükleme"""
        try:
            # Önce tam yol ile dene
            api_key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_key.txt")
            
            # Eğer dosya bulunamazsa, çalışma dizininde kontrol et
            if not os.path.exists(api_key_file):
                api_key_file = "api_key.txt"
            
            # Son olarak, doğrudan tam yolu dene
            if not os.path.exists(api_key_file):
                api_key_file = r"c:\Users\alito\OneDrive\Masaüstü\firmalar\api_key.txt"
                
            if os.path.exists(api_key_file):
                with open(api_key_file, "r") as f:
                    api_key = f.read().strip()
                    if api_key:
                        self.set_api_key(api_key)
                        self.logger.info(f"API anahtarı başarıyla yüklendi: {api_key_file}")
                        return True
                    else:
                        self.logger.error("API anahtarı dosyası boş")
            else:
                self.logger.error(f"API anahtarı dosyası bulunamadı: {api_key_file}")
        except Exception as e:
            self.logger.error(f"API anahtarı yüklenirken hata oluştu: {str(e)}")
        return False
                
    def set_api_key(self, api_key, model=None):
        """API anahtarını ayarla ve yapılandırmayı doğrula"""
        if not api_key:
            self.logger.error("API anahtarı boş olamaz")
            return False
        
        try:
            self.api_key = api_key
            if model:
                self.model = model
                
            # Google Gemini API yapılandırması
            genai.configure(api_key=self.api_key)
            
            # Kullanılabilir modelleri listele ve doğrula
            try:
                # Mevcut modelleri kontrol et
                available_models = [m.name for m in genai.list_models()]
                self.logger.info(f"Kullanılabilir modeller: {available_models}")
                
                # En iyi model eşleşmesini bul
                if "gemini-pro" in available_models:
                    self.model = "gemini-pro"
                elif "gemini-1.5-pro" in available_models:
                    self.model = "gemini-1.5-pro"
                elif "gemini-1.5-flash" in available_models:
                    self.model = "gemini-1.5-flash"
                else:
                    # Varsayılan olarak ilk gemini modelini kullan
                    for model_name in available_models:
                        if "gemini" in model_name:
                            self.model = model_name
                            break
                
                self.logger.info(f"Seçilen model: {self.model}")
            except Exception as e:
                self.logger.warning(f"Model listesi alınamadı: {e}. Varsayılan model kullanılacak: {self.model}")
            
            # API yapılandırmasını test et
            model = genai.GenerativeModel(self.model)
            response = model.generate_content("Merhaba, bu bir test mesajıdır.")
            if response:
                self.is_configured = True
                self.logger.info(f"Gemini API başarıyla yapılandırıldı, model: {self.model}")
                return True
            else:
                self.logger.error("API anahtarı geçerli değil veya API yanıt vermedi")
                return False
        except Exception as e:
            self.logger.error(f"API yapılandırılırken hata oluştu: {str(e)}")
            self.is_configured = False
            return False
    
    def get_prompt(self, prompt_key, replacements=None):
        """Belirtilen prompt'u getir ve değişkenleri doldur"""
        if prompt_key not in self.prompts:
            self.logger.error(f"Prompt bulunamadı: {prompt_key}")
            return f"Prompt bulunamadı: {prompt_key}"
            
        prompt_text = self.prompts[prompt_key].get("text", "")
        
        if replacements and prompt_text:
            for key, value in replacements.items():
                placeholder = "{{" + key + "}}"
                # None değerlerini boş string ile değiştir
                value_str = "" if value is None else str(value)
                prompt_text = prompt_text.replace(placeholder, value_str)
                
        return prompt_text
    
    def generate_content(self, prompt, system_instruction=None):
        """Gemini API'ye istek gönder"""
        if not self.is_configured:
            self.logger.error("API yapılandırılmamış, lütfen önce API anahtarını ayarlayın")
            return "API yapılandırılmamış, lütfen önce API anahtarı ekleyin."
        
        try:
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            # Safety settings
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            
            # Model oluştur
            model = genai.GenerativeModel(
                model_name=self.model,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Sistem talimatı varsa ekle
            if system_instruction:
                chat = model.start_chat(system_instruction=system_instruction)
                response = chat.send_message(prompt)
            else:
                response = model.generate_content(prompt)
            
            if response:
                return response.text
            else:
                return "API'den geçerli bir yanıt alınamadı."
                
        except Exception as e:
            self.logger.error(f"İçerik oluşturulurken hata: {str(e)}")
            return f"Hata: {str(e)}"