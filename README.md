# Jira Support Performans Raporu

Jira'dan indirilen Excel dosyalarını işleyerek SLA performans raporları oluşturan Flask web uygulaması.

## 🚀 Özellikler

- Jira Excel dosyası yükleme (.xlsx / .xls)
- Zaman formatı dönüştürme (ör: `2 sa. 30 dk.` → `2.30`)
- Müdahale SLA ve çözüm süresi hesaplama
- İşlenmiş Excel dosyasını indirme

## 🛠️ Kurulum (Yerel)

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# Uygulamayı çalıştır
python app.py
```

Tarayıcıda `http://localhost:5000` adresine gidin.

## 📋 Kullanım

1. Jira'dan dışa aktarılan Excel dosyasını seçin (`Your Jira Issues` sayfası içermeli)
2. **İşlemi Başlat** butonuna tıklayın
3. İşlenmiş dosya otomatik olarak indirilir

## ☁️ Hosting

Ücretsiz hosting seçenekleri ve adım adım kurulum için [HOSTING_TALIMATLARI.md](HOSTING_TALIMATLARI.md) dosyasına bakın.

## 📁 Proje Yapısı

```
├── app.py                  # Flask uygulaması
├── requirements.txt        # Python bağımlılıkları
├── Procfile                # Railway/Heroku yapılandırması
├── templates/
│   └── index.html          # Web arayüzü
└── HOSTING_TALIMATLARI.md  # Hosting kılavuzu
```
