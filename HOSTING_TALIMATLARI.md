# Flask Web Uygulaması - Ücretsiz Hosting Kılavuzu

## 🚀 Hızlı Başlangıç

### Seçenek 1: Railway.app (Önerilen - En Kolay)

1. **Railway'a kaydolun:**
   - https://railway.app adresine gidin
   - GitHub hesabınızla giriş yapın

2. **Yeni proje oluşturun:**
   - "New Project" butonuna tıklayın
   - "Deploy from GitHub repo" seçin
   - GitHub repo'nuzu seçin

3. **Otomatik deploy:**
   - Railway otomatik olarak `requirements.txt` ve `Procfile` dosyalarını algılar
   - Uygulama otomatik olarak deploy edilir
   - Birkaç dakika içinde hazır!

4. **Domain alın:**
   - Railway size ücretsiz bir domain verir (örn: `your-app.railway.app`)
   - Settings > Domains'den özel domain ekleyebilirsiniz

**Ücretsiz Tier:**
- 500 saat/ay ücretsiz
- $5 kredi/ay
- Yeterli!

---

### Seçenek 2: Render.com

1. **Render'a kaydolun:**
   - https://render.com adresine gidin
   - GitHub hesabınızla giriş yapın

2. **Yeni Web Service oluşturun:**
   - "New +" > "Web Service"
   - GitHub repo'nuzu bağlayın

3. **Ayarlar:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
   - **Environment:** Python 3

4. **Deploy:**
   - "Create Web Service" butonuna tıklayın
   - Birkaç dakika içinde hazır!

**Ücretsiz Tier:**
- Sınırsız statik siteler
- Web servisler için: 750 saat/ay ücretsiz
- 15 dakika inaktiflikten sonra uyku modu (ilk istekte uyanır)

---

### Seçenek 3: Fly.io

1. **Fly.io'ya kaydolun:**
   - https://fly.io adresine gidin
   - CLI'yi yükleyin: `curl -L https://fly.io/install.sh | sh`

2. **Deploy:**
   ```bash
   fly launch
   fly deploy
   ```

**Ücretsiz Tier:**
- 3 shared-cpu-1x VM
- 3GB persistent volume storage
- 160GB outbound data transfer

---

## 📝 Gerekli Dosyalar (Zaten Hazır)

✅ `app.py` - Flask uygulaması  
✅ `requirements.txt` - Python kütüphaneleri  
✅ `Procfile` - Railway/Heroku için  
✅ `templates/index.html` - Web arayüzü  

---

## 🔧 Yerel Test

Önce yerel olarak test edin:

```bash
# Kütüphaneleri yükleyin
pip install -r requirements.txt

# Uygulamayı çalıştırın
python app.py
```

Tarayıcıda `http://localhost:5000` adresine gidin.

---

## 📤 GitHub'a Yükleme

1. **GitHub'da yeni repo oluşturun**

2. **Kodları yükleyin:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/kullaniciadi/repo-adi.git
   git push -u origin main
   ```

3. **Hosting servisine bağlayın** (Railway/Render/Fly.io)

---

## ⚙️ Önemli Notlar

### Port Ayarları
- `app.py` dosyasında port otomatik olarak environment variable'dan alınır
- Hosting servisleri otomatik olarak PORT değişkenini ayarlar

### Secret Key
- Production'da `app.secret_key` değiştirin!
- Environment variable kullanın:
  ```python
  app.secret_key = os.environ.get('SECRET_KEY', 'default-key')
  ```

### Dosya Boyutu
- Max dosya boyutu: 16MB (app.py'de ayarlı)
- Daha büyük dosyalar için artırın

---

## 🎯 Hangi Servisi Seçmeliyim?

| Servis | Avantajlar | Dezavantajlar |
|--------|-----------|---------------|
| **Railway** | ✅ En kolay<br>✅ Otomatik deploy<br>✅ İyi dokümantasyon | ⚠️ Sınırlı ücretsiz tier |
| **Render** | ✅ Kolay kurulum<br>✅ İyi performans | ⚠️ Uyku modu (ilk istek yavaş) |
| **Fly.io** | ✅ Hızlı<br>✅ Global CDN | ⚠️ CLI gerekli |

**Öneri:** Railway.app ile başlayın, en kolay!

---

## 🐛 Sorun Giderme

### "Module not found" hatası
- `requirements.txt` dosyasını kontrol edin
- Tüm kütüphaneler listelenmiş mi?

### Port hatası
- `app.py` dosyasında `PORT` environment variable kullanılıyor mu?
- Hosting servisi PORT'u otomatik ayarlar

### Dosya yükleme hatası
- Max dosya boyutunu kontrol edin (16MB)
- `uploads` klasörü oluşturulmuş mu?

---

## 📞 Yardım

Sorun yaşarsanız:
1. Hosting servisinin loglarını kontrol edin
2. Yerel olarak test edin
3. GitHub Issues'da sorun bildirin

