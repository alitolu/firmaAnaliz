# Yapay Zeka ile Firma Analiz ve E-Posta Şablonu Oluşturma Aracı

## Proje Hakkında
Bu proje, B2B pazarlamada kullanılmak üzere firma analizleri yapar ve bu analizlere dayalı kişiselleştirilmiş e-posta kampanyaları oluşturmayı kolaylaştırır.

## Dosyalar ve İşlevleri

### `gui_scraper.py`
Ana uygulama penceresi ve kullanıcı arayüzü. Şu işlevlere sahiptir:
- Firma listesini yükleme ve görüntüleme
- Web scraping işlevselliği
- Firma bilgilerini düzenleme
- Firma bilgilerine dayalı e-posta şablonları oluşturma
- Firma analizlerini görüntüleme

### `email_generator.py`
Toplanan firma bilgilerini analiz ederek kişiselleştirilmiş e-posta şablonları oluşturan modül. AI API'leri kullanarak firma analizlerini gerçekleştirir.

### `web_scraper.py`
Web sitelerinden firma bilgilerini otomatik olarak toplar.

### `data_manager.py`
Veri yönetimi fonksiyonlarını içerir. Firma verilerini depolama, okuma ve yazma işlemlerini gerçekleştirir.

### `gemini_api.py`
Google'ın Gemini AI API'sine erişim için oluşturulan modül:
- Gemini AI API ile firma analizi yapma
- OpenAI API'ye alternatif olarak kullanılabilir
- Firma analizi için prompt şablonlarını içerir

### `company_scraper.py`
Alternatif firma bilgisi toplama modülü:
- Farklı web yapılarından firma verisi çıkarma
- Belirli sektörler veya web siteleri için özelleştirilmiş scraping fonksiyonları
- `web_scraper.py`'ye tamamlayıcı olarak çalışabilir

## Yeni Özellikler
Son eklenen özellik: E-posta şablonu görüntülenirken aynı ekranda firmanın analiz sonuçları ve kullanılan AI prompt'u da gösterilmektedir.
