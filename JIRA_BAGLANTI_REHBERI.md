# Jira Bağlantı Kurulum Rehberi (Türkçe)

Bu döküman, Destek Merkezi platformunu mevcut bir Jira alanına nasıl bağlayacağınızı adım adım açıklar.

---

## 📋 İçindekiler

1. [Genel Bakış](#genel-bakış)
2. [Jira'da Yapılacaklar](#jirada-yapılacaklar)
3. [API Token Oluşturma](#api-token-oluşturma)
4. [Proje Anahtarını Bulma](#proje-anahtarını-bulma)
5. [Sitemizde Yapılacaklar](#sitemizde-yapılacaklar)
6. [Bağlantıyı Test Etme](#bağlantıyı-test-etme)
7. [Kayıtlar Sayfası](#kayıtlar-sayfası)
8. [Sorun Giderme](#sorun-giderme)

---

## Genel Bakış

Bu özellik, Jira'daki mevcut projenize bağlanarak kayıtları (issue) doğrudan bu platformdan görüntülemenize olanak tanır. Bağlantı, Atlassian'ın resmi **REST API v3**'ü kullanılarak gerçekleştirilir.

**Desteklenen Jira türü:** Atlassian Cloud (Örn: `sirket.atlassian.net`)  
Şirket içi (Server/Data Center) kurulumlar için URL formatı aynıdır, kendi sunucu adresinizi kullanırsınız.

---

## Jira'da Yapılacaklar

Bağlantı kurmadan önce Jira tarafında iki bilgiye ihtiyacınız var:

1. Atlassian hesabınıza ait **API Token**
2. Bağlanmak istediğiniz Jira projesinin **Proje Anahtarı** (Project Key)

> **Not:** Bu işlemleri yapmak için Jira'ya erişim yetkiniz ve projeye üyeliğiniz olması gerekir.

---

## API Token Oluşturma

API Token, Jira hesabınıza şifrenizi paylaşmadan güvenli erişim sağlar.

### Adımlar:

1. Tarayıcınızda [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens) adresine gidin.
2. Gerekirse Atlassian e-posta ve şifrenizle giriş yapın.
3. **"Create API token"** butonuna tıklayın.
4. Açılan pencerede tokene bir isim verin (örn: `Destek Merkezi`).
5. **Create** butonuna tıklayın.
6. Oluşturulan tokeni kopyalayın — **bu token bir daha gösterilmez!**

> ⚠️ **Güvenlik Uyarısı:** API tokenı kimseyle paylaşmayın. Token, Jira hesabınıza tam erişim sağlar. İhtiyaç duymazsanız veya tehlikeye girdiyse Atlassian hesabı sayfasından iptal edin.

---

## Proje Anahtarını Bulma

Her Jira projesinin benzersiz bir kısa kodu (Project Key) vardır. Örneğin: `SUP`, `IT`, `HELP`, `DEV`.

### Nasıl bulunur?

1. Jira'da hedef projenize gidin.
2. Sol alt köşede **"Project settings"** (Proje ayarları) bağlantısına tıklayın.
3. **"Details"** (Ayrıntılar) sekmesinde **"Key"** alanını bulun.

**En hızlı yöntem:** Herhangi bir Jira kaydının başlığına bakın. `SUP-42` gibi görünüyorsa proje anahtarınız `SUP`'tur.

---

## Sitemizde Yapılacaklar

Jira'dan gerekli bilgileri aldıktan sonra **Jira Ayarları** sayfasına gidin:

| Alan | Açıklama | Örnek |
|------|----------|-------|
| Jira Alan URL'si | Jira sitenizin tam adresi (sonda `/` olmadan) | `https://sirket.atlassian.net` |
| E-posta Adresi | Atlassian hesabınızda kayıtlı e-posta | `ali@sirket.com` |
| Proje Anahtarı | Jira proje kodu (büyük harf) | `SUP` |
| API Token | Atlassian hesabından oluşturulan token | `ATATT3xFf...` |

### Adımlar:

1. Sol menüden **"Jira Ayarları"** seçeneğine tıklayın.
2. Yukarıdaki tabloya göre tüm alanları eksiksiz doldurun.
3. **"Bağlan"** butonuna tıklayın.

Sistem otomatik olarak Jira'ya bağlanıp kimlik doğrulamasını test eder. Başarılı ise **"Kayıtlar"** sayfasına yönlendirilirsiniz.

---

## Bağlantıyı Test Etme

Form gönderildiğinde sistem otomatik olarak `GET /rest/api/3/myself` endpoint'ini çağırarak kimlik doğrular.

| Sonuç | Anlam |
|-------|-------|
| ✅ Başarılı | Kayıtlar sayfasına yönlendirilirsiniz |
| ❌ 401 Hatası | E-posta veya API Token hatalı |
| ❌ Bağlantı Hatası | URL hatalı ya da Jira'ya erişilemiyor |

**Manuel test (terminal):**

```bash
curl -u "e-posta@sirket.com:API_TOKEN" \
     -H "Accept: application/json" \
     "https://sirket.atlassian.net/rest/api/3/myself"
```

Başarılı ise JSON formatında hesap bilgilerinizi içeren yanıt döner.

---

## Kayıtlar Sayfası

Bağlantı kurulduktan sonra **Kayıtlar** sayfası şu bilgileri listeler:

| Alan | Açıklama |
|------|----------|
| 🔑 Kayıt Anahtarı | Jira'daki kayda doğrudan link (örn: SUP-42) |
| 📋 Başlık | Kayıt özeti ve tipi (Bug, Task, Story, Epic) |
| 🔵 Durum | To Do / In Progress / Done |
| 🟡 Öncelik | Highest, High, Medium, Low, Lowest |
| 👤 Atanan | Göreve atanan kişi |
| 📅 Güncelleme | Son güncelleme tarihi |

### Filtreleme Özellikleri

- **Metin Arama** — Başlık veya içerikte arama yapabilirsiniz.
- **Durum Filtresi** — To Do, In Progress veya Done durumlarına göre filtreleyin.
- **Sayfalama** — Her sayfada 20 kayıt gösterilir.

> **İpucu:** Kayıt anahtarına (örn: `SUP-42`) tıkladığınızda Jira'daki kayda yeni sekmede doğrudan ulaşabilirsiniz.

---

## Sorun Giderme

### 401 Unauthorized (Yetkisiz Erişim)

- E-posta adresi yanlış girilmiş olabilir. Atlassian hesabınızdaki e-postayla aynı olmalı.
- API Token yanlış kopyalanmış olabilir. Yeni bir token oluşturun.
- Token iptal edilmiş olabilir. [Atlassian hesabından](https://id.atlassian.com/manage-profile/security/api-tokens) kontrol edin.

### Bağlantı Hatası / Zaman Aşımı

- URL formatını kontrol edin: `https://sirket.atlassian.net` (sonda `/` olmadan)
- İnternet bağlantısını ve Jira'nın erişilebilir olduğunu doğrulayın.
- Şirket güvenlik duvarı (firewall) Atlassian'ı engelliyor olabilir.

### Kayıtlar Sayfası Boş Görünüyor

- Proje Anahtarı'nın doğru girildiğini kontrol edin (büyük harf, boşluksuz).
- Jira hesabınızın bu projeye üye olduğunu doğrulayın.
- Proje gerçekten kayıt içeriyor mu? Jira'da kontrol edin.

### Gerekli İzinler

Bağlantı için gereken minimum izinler:

| İzin | Gereklilik |
|------|-----------|
| Browse Projects (Projeleri Görüntüle) | ✅ Gerekli |
| View Issues (Kayıtları Görüntüle) | ✅ Gerekli |
| Edit / Create / Delete Issues | ❌ Gerekli Değil |

> Kullanıcının projeye en az **"Gözlemci" (Viewer)** rolü atanmış olması yeterlidir.

---

## 📞 Yardım

Sorun yaşarsanız:
1. Uygulama loglarını kontrol edin.
2. Jira'da manuel API testi yapın (yukarıdaki `curl` komutunu kullanın).
3. Jira Ayarları sayfasından bağlantıyı yeniden yapılandırın.
