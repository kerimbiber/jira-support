# Support Performans Raporu - Web Uygulaması

Jira performans raporlarını dönüştürmek için Flask web uygulaması.

## Özellikler

- Web tabanlı arayüz
- Excel dosyası yükleme ve indirme
- Time to resolution formatını dönüştürme (örn: "-6 sa. 57 dk." → "-6.57")
- Müdahale SLA formatını dönüştürme (örn: "24 dk." → "0.24")
- Otomatik hesaplamalar:
  - Müdahale SLA (Hesaplama) = 0.30 - Müdahale SLA
  - Time to resolution (Hesaplama) = 8.00 - Time to resolution
  - Sonuç = İki hesaplamanın toplamı

## Yerel Kurulum

1. Gerekli kütüphaneleri yükleyin:
```bash
pip install -r requirements.txt
```

2. Uygulamayı çalıştırın:
```bash
python app.py
```

3. Tarayıcıda açın:
```
http://localhost:5000
```

## Ücretsiz Hosting

Detaylı hosting talimatları için `HOSTING_TALIMATLARI.md` dosyasına bakın.

### Hızlı Başlangıç (Railway.app)

1. GitHub'a yükleyin
2. https://railway.app adresine gidin
3. GitHub repo'nuzu bağlayın
4. Otomatik deploy başlar!

## Kullanım

1. Web arayüzünde Excel dosyanızı seçin
2. "İşlemi Başlat" butonuna tıklayın
3. İşlem tamamlandığında dosya otomatik indirilecek

## Notlar

- Dosyada "Your Jira Issues" sayfası olmalıdır
- Time to resolution ve Müdahale SLA sütunları gerekli formatlarda olmalıdır
- Max dosya boyutu: 16MB
