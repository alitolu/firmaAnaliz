# Firma Analiz ve E-Posta Şablonu Uygulaması Kullanım Kılavuzu

## Genel Bakış

Bu uygulama, firmalar hakkında bilgi toplamak, bu bilgileri analiz etmek ve kişiselleştirilmiş e-posta şablonları oluşturmak için tasarlanmıştır. Aşağıdaki temel işlevlere sahiptir:

1. Firma listesi yönetimi
2. Web sitelerinden firma bilgilerinin otomatik toplanması (scraping)
3. Firma bilgilerinin AI ile analiz edilmesi
4. Kişiselleştirilmiş e-posta şablonlarının oluşturulması

## Kullanım Adımları

### 1. Uygulamayı Başlatma

```bash
python gui_scraper.py
```

Bu komut, ana uygulama penceresini açacaktır.

### 2. API Anahtarını Yapılandırma

- Uygulama ilk çalıştırıldığında veya "Ayarlar" menüsü üzerinden API anahtarınızı girmeniz gerekmektedir.
- OpenAI API anahtarınızı girerek, firma analizi ve e-posta şablonu oluşturma özelliklerini etkinleştirebilirsiniz.
- Alternatif olarak Google Gemini API anahtarını kullanmak istiyorsanız, ilgili seçeneği seçebilirsiniz.

### 3. Firma Listesi İşlemleri

- **Firma Listesi Yükleme**: "Dosya > Firma Listesi Aç" menüsünden veya "Liste Yükle" düğmesinden bir CSV dosyası seçerek firma listesini yükleyebilirsiniz.
- **Yeni Firma Ekleme**: "Firma Ekle" düğmesiyle manuel olarak yeni firma ekleyebilirsiniz.
- **Firma Bilgilerini Düzenleme**: Listeden bir firmaya tıklayarak detaylarını düzenleyebilirsiniz.

### 4. Web Sitesinden Bilgi Toplama

- Bir firma seçin ve "Web Sitesinden Bilgi Topla" düğmesine tıklayın.
- Firma web sitesi URL'si girilmiş olmalıdır.
- Sistem, web sitesinden firma bilgilerini otomatik olarak çıkaracak ve forma dolduracaktır.
- Çıkarılan bilgileri kontrol edip düzenleyebilirsiniz.

### 5. Firma Analizi Yapma

- "Firmayı Analiz Et" düğmesine tıklayarak seçili firmanın AI analizi yapılabilir.
- Analiz, firmanın faaliyet alanı, güçlü yönleri, dijital ihtiyaçları gibi konuları içerecektir.
- Analiz sonuçları "Analiz Sonuçları" sekmesinde görüntülenecektir.

### 6. E-Posta Şablonu Oluşturma

- Firma analizi tamamlandıktan sonra "E-Posta Şablonu Oluştur" düğmesine tıklayın.
- Sistem, firma bilgilerini ve analiz sonuçlarını kullanarak kişiselleştirilmiş bir e-posta şablonu oluşturacaktır.
- Oluşturulan şablon "E-Posta Şablonu" sekmesinde görüntülenecektir.
- Şablonu kopyalayabilir veya düzenleyebilirsiniz.

### 7. Sonuçları Kaydetme

- "Dosya > Kaydet" menüsünden veya "Kaydet" düğmesinden firma listesini, analiz sonuçlarını ve e-posta şablonlarını kaydedebilirsiniz.
- CSV veya JSON formatında kayıt yapılabilir.

## Örnek Akış

1. Uygulamayı başlat
2. API anahtarını yapılandır
3. Firma listesini yükle veya yeni firma ekle
4. Web sitesinden bilgileri çek (veya manuel gir)
5. Firma analizini yap
6. E-posta şablonunu oluştur
7. Sonuçları kaydet

## Dosya Yapısı ve Bileşenler

- **gui_scraper.py**: Ana uygulama penceresi ve kullanıcı arayüzü
- **web_scraper.py**: Web sitelerinden firma bilgilerini toplama işlevleri
- **email_generator.py**: Firma analizi ve e-posta şablonu oluşturma işlevleri
- **gemini_api.py**: Google Gemini AI API entegrasyonu
- **company_scraper.py**: Alternatif firma bilgisi toplama modülü
- **prompts.json**: AI prompt şablonlarını içeren dosya

## İpuçları

- En iyi sonuçlar için firma web sitesi URL'sini tam olarak belirtin (https:// dahil)
- Otomatik çıkarılan bilgiler her zaman %100 doğru olmayabilir, kontrol edip düzenlemeyi unutmayın
- Kapsamlı bir firma açıklaması, daha iyi analiz sonuçları ve e-posta şablonları üretilmesine yardımcı olur
- Anahtar kelimeler ve sektör bilgisini olabildiğince spesifik girin