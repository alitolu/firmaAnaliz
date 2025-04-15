import requests
import json
import sys

def test_gemini_api(api_key, verbose=True):
    """
    Gemini API bağlantısını test eder ve çalışıp çalışmadığını kontrol eder
    
    Args:
        api_key (str): Test edilecek API anahtarı
        verbose (bool): Ayrıntılı çıktı görüntüleme durumu
        
    Returns:
        bool: API anahtarı geçerliyse True, değilse False
    """
    if verbose:
        print("Gemini API bağlantısını test ediyorum...")
    
    # Güncel model isimleri
    models = ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"]
    
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
        
        # Simple request payload
        payload = {
            "contents": [{
                "parts": [{"text": "Hello, please respond with a simple greeting."}]
            }]
        }
        
        if verbose:
            print(f"Model deneniyor: {model}")
            print(f"İstek gönderiliyor: {url.replace(api_key, 'API_KEY_HIDDEN')}")
        
        try:
            response = requests.post(url, json=payload)
            
            if verbose:
                print(f"Durum kodu: {response.status_code}")
            
            if response.status_code == 200:
                if verbose:
                    print(f"BAŞARILI! API bağlantısı {model} modeli ile çalışıyor.")
                    print("\nYanıt:")
                    result = response.json()
                    if "candidates" in result and result["candidates"]:
                        content = result["candidates"][0]["content"]
                        for part in content.get("parts", []):
                            if "text" in part:
                                print(part["text"])
                return True  # Success with this model
            else:
                if verbose:
                    print(f"Hata: {response.text}")
        except Exception as e:
            if verbose:
                print(f"Hata oluştu: {str(e)}")
    
    if verbose:
        print("\n----------------------------")
        print("SORUN GİDERME İPUÇLARI:")
        print("1. Google AI Studio'da API anahtarınızı doğrulayın: https://makersuite.google.com/app/apikey")
        print("2. Google Cloud Console'da Generative Language API'nin etkinleştirildiğinden emin olun")
        print("3. Kullanılabilir modelleri kontrol edin: https://ai.google.dev/models/gemini")
        print("4. Doğru API sürümünü kullandığınızdan emin olun (v1)")
    
    return False

def list_available_models(api_key, verbose=True):
    """
    Mevcut Gemini modellerini listeler
    
    Args:
        api_key (str): API anahtarı
        verbose (bool): Ayrıntılı çıktı görüntüleme durumu
        
    Returns:
        list: Kullanılabilir modellerin listesi
    """
    url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
    
    if verbose:
        print("Kullanılabilir modelleri listeliyorum...")
        print(f"İstek gönderiliyor: {url.replace(api_key, 'API_KEY_HIDDEN')}")
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            models = response.json().get("models", [])
            if verbose:
                print(f"{len(models)} model bulundu:")
                for model in models:
                    print(f" - {model.get('name')}: {model.get('displayName')}")
            return [model.get("name") for model in models]
        else:
            if verbose:
                print(f"Modeller alınamadı, durum kodu: {response.status_code}")
                print(f"Yanıt: {response.text}")
            return []
    except Exception as e:
        if verbose:
            print(f"Hata oluştu: {str(e)}")
        return []

def main():
    print("Gemini API Test Aracı")
    api_key = input("Gemini API anahtarınızı girin: ")
    
    if not api_key:
        print("Hata: API anahtarı gereklidir.")
        return
    
    # Önce mevcut modelleri listele
    available_models = list_available_models(api_key)
    
    # Ardından API bağlantısını test et
    test_gemini_api(api_key)

if __name__ == "__main__":
    main()