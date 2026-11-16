# 🛡️ StudioFinder İstanbul — Kapsamlı Güvenlik Denetim Raporu (Security Audit v2.0)

**Tarih:** 17 Kasım 2026  
**Denetlenen Hedefler:**  
1. **Yerel Çalışma Alanı:** `C:\Projects\tasarimci-radari`  
2. **GitHub Deposu:** [https://github.com/kabaoglueness/tasarimci-radari](https://github.com/kabaoglueness/tasarimci-radari)  
3. **Canlı Web Dağıtımı:** [https://tasarimci-radari.vercel.app](https://tasarimci-radari.vercel.app)  
**Denetim Türü:** Acımasız Güvenlik Denetimi (Red Team & AppSec Code Review, DAST Canlı Endpoint Taraması, SAST Statik Kod Analizi)

---

## 📊 Yönetici Özeti (Executive Summary)

İlk denetimden sonra yapılan geliştirmelerle **DOM XSS açıkları (`escapeHtml` / `sanitizeUrl`), Latin-1 HTTP başlık çökmesi ve Android cleartext riskleri** başarıyla ele alınmış ve kapatılmıştır.

Ancak projenin canlıya çıkması (`tasarimci-radari.vercel.app`) ve GitHub'daki son commit'ler (`d5ccf85`, `1a8cdf7`, `649e6a8`) ile birlikte **yeni kritik ve yüksek seviyeli zafiyetler** ortaya çıkmıştır:

* **Genel Güvenlik Skoru:** **68 / 100 (Orta-Yüksek Risk)**
* **Kritik Bulgu:** Kod içerisine gömülen sabit SHA-256 hash anahtarı (`AUTH_KEY_HASH`), iptal edilemeyen (unrevokable) bir arka kapı (backdoor) işlevi görmektedir.
* **Canlı Sistem Açığı:** Canlı Vercel dağıtımında (`tasarimci-radari.vercel.app`), güvenlik raporu (`SECURITY_AUDIT.md`), teknik şartnameler (`docs/`), paket konfigürasyonları doğrudan herkese açık statik dosya olarak servis edilmektedir.
* **Eksik Prodüksiyon Başlıkları:** Canlı web sitesinde hiçbir **Content-Security-Policy (CSP)** ve **X-Frame-Options (Clickjacking Koruması)** başlığı bulunmamaktadır.

### Zafiyet Dağılım Matrisi

| Seviye | Adet | Kategori | Tespit Edilen Hedef | Durum |
| :--- | :---: | :--- | :--- | :--- |
| 🔴 **KRİTİK** | 1 | Kod İçi Kriptografik Hash & Kalıcı Yetki Aşımı | Yerel Kod + GitHub + Canlı API | **AÇIK** |
| 🟠 **YÜKSEK** | 3 | Canlıda Bilgi İfşası, Eksik CSP/Clickjacking, Path Prefix | Canlı Dağıtım (`vercel.app`) | **AÇIK** |
| 🟡 **ORTA** | 4 | CDN SRI Eksikliği, URL'de Token Sızıntısı, Rate Limit Yokluğu, SSRF TOCTOU | Yerel + Canlı | **AÇIK** |
| 🔵 **DÜŞÜK** | 1 | Açık PII Verisi (Telefon / E-posta) | GitHub + Canlı JSON | **AÇIK** |
| 🟢 **DÜZELTİLDİ** | 3 | DOM XSS, Latin-1 Header Crash, Android Cleartext Traffic | Yerel Kod + Repo | **KAPATILDI** |

---

## 🟢 Önceki Denetimden Düzeltilen Güvenlik Maddeleri

* [x] **DOM XSS Koruması:** `src/app.js` içerisine `escapeHtml()` ve `sanitizeUrl()` entegre edildi. Tüm `innerHTML` alanları ve dinamik linkler varlık düzeyinde filtreleniyor.
* [x] **HTTP Header Encoding DoS:** `server.py` içerisinde `get_last_sync_time()` değeri `urllib.parse.quote()` ile güvenli ASCII formatına alındı; birim testler (17 test) yeşile döndü.
* [x] **Android Cleartext:** Karmaşık mobil/Capacitor yapısı kaldırılarak saldırı yüzeyi daraltıldı; pure responsive PWA mimarisine geçildi.

---

## 🔴 1. [KRİTİK] Sabit SHA-256 Hash'i ile Yetki Doğrulama ve İptal Edilemeyen Arka Kapı

* **Etkilenen Dosya:** [api/search_real.py](file:///c:/Projects/tasarimci-radari/api/search_real.py#L20)
* **İlgili Commit:** `d5ccf85` (GitHub'da yayında)
* **Canlı URL:** `https://tasarimci-radari.vercel.app/api/search_real`
* **Zafiyet Türü:** CWE-798: Use of Hard-coded Credentials / CWE-916: Use of Password Hash With Insufficient Computational Effort
* **Zafiyetli Kod:**
  ```python
  # api/search_real.py:20
  AUTH_KEY_HASH = "f24fbff3259435331edbea7d72d0842b1e1bccaaef9b886ce0a44a15721380c3"

  # api/search_real.py:206-209
  user_hash = hashlib.sha256(user_token.encode('utf-8')).hexdigest()
  if hmac.compare_digest(user_hash.encode('utf-8'), AUTH_KEY_HASH.encode('utf-8')):
      is_live = True
  ```

### İstismar ve Risk Analizi:
1. **Tuzsuz (Unsalted) Hızlı Hash:** Düz metin şifreyi koddan çıkarmak iyi bir niyet olsa da, **SHA-256 bir parola hash algoritması değildir**. Hızlı bir mesaj özetleme fonksiyonudur. Tuzsuz (salt) ve tek tur SHA-256 hash'leri, modern GPU'lar (saniyede onlarca milyar hash) veya Rainbow Table / CrackStation gibi çevrim içi veritabanları ile kolayca geri döndürülebilir.
2. **Ortam Değişkenini Hükümsüz Kılma (Bypass):** Geliştirici Vercel panelinde `STUDIO_SECRET_TOKEN` değişkenini değiştirse veya iptal etse bile, **kodun içine gömülen bu hash'e denk gelen şifreyi giren herkes canlı LinkedIn motorunu sınırsızca çalıştırmaya devam eder**. Bu durum iptal edilemeyen (unrevokable) bir statik yetkilendirme arka kapısı oluşturur.
3. **OWASP Kuralı:** Kimlik doğrulama anahtarları veya hash'leri asla kod reposunda bulunmamalıdır. Yalnızca sunucu ortam değişkenleri (`os.environ`) üzerinden okunmalıdır.

### Düzeltme (Remediation):
`AUTH_KEY_HASH` tamamen silinmeli, yalnızca Vercel panelinde tanımlı ortam değişkeni kullanılmalıdır:
```python
# api/search_real.py
SECRET_ACCESS_TOKEN = os.environ.get("STUDIO_SECRET_TOKEN")

is_live = False
if SECRET_ACCESS_TOKEN and user_token:
    if hmac.compare_digest(user_token.strip().encode('utf-8'), SECRET_ACCESS_TOKEN.strip().encode('utf-8')):
        is_live = True
```

---

## 🟠 2. [YÜKSEK] Canlı Vercel Sunucusunda Hassas Dosya ve Dokümantasyon İfşası

* **Etkilenen Dağıtım:** [https://tasarimci-radari.vercel.app](https://tasarimci-radari.vercel.app)
* **Zafiyet Türü:** CWE-552: Files or Directories Accessible to External Parties
* **Doğrudan Erişilebilen Canlı Bağlantılar:**
  * `https://tasarimci-radari.vercel.app/SECURITY_AUDIT.md` (HTTP 200 - 11.9 KB)
  * `https://tasarimci-radari.vercel.app/package.json` (HTTP 200 - 742 B)
  * `https://tasarimci-radari.vercel.app/pyproject.toml` (HTTP 200 - 108 B)
  * `https://tasarimci-radari.vercel.app/.vercelignore` (HTTP 200 - 293 B)
  * `https://tasarimci-radari.vercel.app/docs/DESIGN_SPEC_ANTI_SLOP.md` (HTTP 200 - 22.7 KB)
  * `https://tasarimci-radari.vercel.app/IMPLEMENTATION_PLAN.md` (HTTP 200 - 1.2 KB)

### İstismar ve Risk Analizi:
`.vercelignore` dosyası yapılandırılırken yalnızca `.env*`, `server.py`, `tests/` ve `android/` yoksayılmıştır. Ancak `SECURITY_AUDIT.md` (sistemin geçmişteki tüm açıklarını ve mimari zayıflıklarını anlatan belge), proje bağımlılıkları (`package.json`) ve gizli dokümantasyonlar dışarıya kapatılmamıştır. Saldırganlar web sitesinin kök dizinini tarayarak sistemin tüm güvenlik açığı geçmişini ve iç mimarisini canlı sunucudan anında indirebilmektedir.

### Düzeltme (Remediation):
[.vercelignore](file:///c:/Projects/tasarimci-radari/.vercelignore) dosyasına tüm dokümantasyon, denetim ve konfigürasyon dosyaları eklenmelidir:
```gitignore
# .vercelignore
SECURITY_AUDIT.md
*.md
docs/
package.json
package-lock.json
pyproject.toml
.vercelignore
.gitignore
```

---

## 🟠 3. [YÜKSEK] Canlı Dağıtımda Eksik HTTP Güvenlik Başlıkları (No CSP & Clickjacking Riski)

* **Etkilenen Dağıtım:** [https://tasarimci-radari.vercel.app/](https://tasarimci-radari.vercel.app/)
* **Zafiyet Türü:** CWE-693: Protection Mechanism Failure / CWE-1021: Improper Restriction of Rendered UI Layers or Frames
* **Canlı Sunucudan Alınan Gerçek HTTP Yanıt Başlıkları:**
  ```http
  HTTP/2 200
  server: Vercel
  content-type: text/html; charset=utf-8
  strict-transport-security: max-age=63072000; includeSubDomains; preload
  x-content-type-options: nosniff
  ```

### İstismar ve Risk Analizi:
1. `server.py` yerel sunucusunda güvenlik başlıkları tanımlanmış olsa da, **Vercel üzerinde `index.html` doğrudan Vercel CDN tarafından sunulmaktadır**.
2. Canlı sunucuda **`Content-Security-Policy` (CSP)** başlığı yoktur. Sayfada oluşabilecek herhangi bir enjeksiyon veya harici script yüklemesi kısıtlanamaz.
3. **`X-Frame-Options`** veya `frame-ancestors` başlığı bulunmamaktadır. Bu durum sitenin herhangi bir kötü niyetli sitede `<iframe>` içerisine gömülerek **Clickjacking (Tıklama Kaçırma)** saldırılarına maruz kalmasına yol açar (kullanıcının kendi girdiği API anahtarı veya seçimleri kandırılarak değiştirilebilir).
4. **`Referrer-Policy`** tanımlı değildir.

### Düzeltme (Remediation):
[vercel.json](file:///c:/Projects/tasarimci-radari/vercel.json) içerisine global güvenlik başlıkları tanımlanmalıdır:
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "cleanUrls": true,
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" },
        {
          "key": "Content-Security-Policy",
          "value": "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: https: https://images.unsplash.com https://media.licdn.com; connect-src 'self' https:;"
        }
      ]
    }
  ]
}
```

---

## 🟠 4. [YÜKSEK] `api/search_real.py` İçerisinde Path Prefix Güvenlik Açığı & Filtresiz Dağıtım

* **Etkilenen Dosya:** [api/search_real.py](file:///c:/Projects/tasarimci-radari/api/search_real.py#L41-L51)
* **Zafiyet Türü:** CWE-22: Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal')
* **Zafiyetli Kod:**
  ```python
  def resolve_safe_static_path(url_path: str):
      clean_path = url_path.split('?')[0].lstrip('/')
      if not clean_path or clean_path == "index.html":
          clean_path = "index.html"
      target = os.path.abspath(os.path.join(BASE_DIR, clean_path))
      # Hatalı prefix kontrolü:
      if not target.startswith(BASE_DIR):
          return None
      if os.path.isfile(target):
          return target
      return None
  ```

### İstismar ve Risk Analizi:
1. `target.startswith(BASE_DIR)` ifadesi sonunda dizin ayracı (`/` veya `\`) barındırmaz. Eğer `BASE_DIR` `/var/task` ise, `/var/task_other/secrets.txt` gibi kardeş dizinler de bu koşulu geçer (Klasik Path Prefix Bypass zafiyeti).
2. `server.py` içerisinde olan `ALLOWED_EXTENSIONS` ve `BLOCKED_FILES` filtreleri `api/search_real.py` içerisine **eklenmemiştir**. Bu sayede Vercel container'ı içinde kalan her dosya doğrudan okunabilir hale gelir.

### Düzeltme (Remediation):
```python
def resolve_safe_static_path(url_path: str):
    clean_path = url_path.split('?')[0].lstrip('/')
    if not clean_path or clean_path == "index.html":
        clean_path = "index.html"
    target = os.path.abspath(os.path.join(BASE_DIR, clean_path))
    
    # 1. Standart chroot denetimi
    try:
        if os.path.commonpath([BASE_DIR, target]) != BASE_DIR:
            return None
    except Exception:
        return None
        
    # 2. İzin verilen uzantılar kontrolü
    allowed_exts = {".html", ".js", ".mjs", ".css", ".json", ".svg", ".png", ".jpg", ".jpeg", ".ico"}
    _, ext = os.path.splitext(target)
    if ext.lower() not in allowed_exts:
        return None

    # 3. Yasaklı dosyalar
    if os.path.basename(target).lower() in {"security_audit.md", "package.json", "pyproject.toml", ".vercelignore"}:
        return None

    if os.path.isfile(target):
        return target
    return None
```

---

## 🟡 5. [ORTA] Tailwind Play CDN Kullanımı ve Subresource Integrity (SRI) Eksikliği

* **Etkilenen Dosya:** [index.html](file:///c:/Projects/tasarimci-radari/index.html#L16)
* **Zafiyet Türü:** CWE-353: Missing Support for Integrity Check
* **Zafiyetli Kod:**
  ```html
  <!-- index.html:16 -->
  <script src="https://cdn.tailwindcss.com"></script>
  ```

### İstismar ve Risk Analizi:
1. `cdn.tailwindcss.com` resmi Tailwind dokümantasyonuna göre **sadece geliştirme (development) amaçlıdır**; runtime esnasında istemci tarayıcısında JIT derleme yapar.
2. Script yüklenirken `integrity="sha384-..."` (Subresource Integrity - SRI) denetimi yapılmamaktadır. CDN sağlayıcısının ele geçirilmesi veya DNS zehirlenmesi durumunda, sayfaya enjekte edilecek zararlı bir JavaScript kodu kullanıcının `localStorage` üzerindeki kayıtlı API anahtarını doğrudan çalabilir.

### Düzeltme (Remediation):
Üretim ortamında Tailwind CLI ile oluşturulmuş yerel statik CSS dosyası (`dist/output.css`) kullanılmalı veya harici scriptlere kesinlikle SRI doğrulaması eklenmelidir.

---

## 🟡 6. [ORTA] API Anahtarının URL Parametresinde Taşınması (`&token=...`)

* **Etkilenen Dosyalar:** [src/app.js](file:///c:/Projects/tasarimci-radari/src/app.js#L47-L50) ve [api/search_real.py](file:///c:/Projects/tasarimci-radari/api/search_real.py#L202)
* **Zafiyet Türü:** CWE-598: Use of GET Request Method With Sensitive Query Strings
* **Zafiyetli Kod:**
  ```javascript
  // src/app.js:47-49
  const tokenParam = token ? `&token=${encodeURIComponent(token)}` : '';
  const liveRes = await fetch(`${apiBase}/api/search_real?query=Tasarım${tokenParam}`, {
    headers: token ? { 'X-Access-Token': token } : {}
  });
  ```

### İstismar ve Risk Analizi:
Token zaten HTTP başlığı (`X-Access-Token`) ile gönderildiği halde, aynı zamanda GET sorgu parametresi (`?token=...`) olarak URL'e eklenmektedir. Bu durum gizli anahtarın Vercel Lambda access loglarında, ara proxy sunucularında ve tarayıcı geçmişinde açık metin olarak depolanmasına yol açar.

### Düzeltme (Remediation):
URL parametresi tamamen kaldırılmalı, kimlik doğrulama sadece `Authorization: Bearer <token>` veya `X-Access-Token` başlığıyla yapılmalıdır:
```javascript
const liveRes = await fetch(`${apiBase}/api/search_real?query=Tasarım`, {
  headers: token ? { 'Authorization': `Bearer ${token}` } : {}
});
```

---

## 🟡 7. [ORTA] Hız Sınırlaması (Rate Limiting) Eksikliği ve LinkedIn Kota Tüketimi

* **Etkilenen Uç Nokta:** `https://tasarimci-radari.vercel.app/api/search_real`
* **Zafiyet Türü:** CWE-799: Improper Control of Generation of Code or Resource
* **Risk Analizi:**
  `/api/search_real` uç noktasında IP tabanlı hız sınırlaması (Rate Limit) bulunmamaktadır. Canlı token'a sahip bir kullanıcı veya bot arka arkaya yüzlerce istek attığında:
  1. Vercel sunucusuz fonksiyon kotası hızla tükenir (Denial of Wallet).
  2. Vercel sunucularının IP bloğu LinkedIn tarafından otomatik olarak kara listeye (CAPTCHA / 429 Too Many Requests) alınır ve canlı ilan akışı tamamen durur.

---

## 🟡 8. [ORTA] Yerel `server.py` İçerisinde TOCTOU SSRF & Liveness Doğrulama Tutarsızlığı

* **Etkilenen Dosya:** [server.py](file:///c:/Projects/tasarimci-radari/server.py#L381-L440)
* **Risk Analizi:**
  `verify_single_job_active(url)` fonksiyonu, güvenli wrapper olan `make_safe_http_request()` fonksiyonunu kullanmayıp doğrudan standart `urllib.request.urlopen(req)` çağırmaktadır. İzin verilen domain'e yönlendirme yapan kötü niyetli bir URL ile yerel ağ taraması yapılabilir.

---

## 🔵 9. [DÜŞÜK] GitHub Reposunda ve Canlı Veride Açık İşletme İletişim Bilgileri (PII)

* **Etkilenen Dosya:** [data/leads.json](file:///c:/Projects/tasarimci-radari/data/leads.json#L194-L195)
* **Risk Analizi:**
  Gerçek bir yerel işletmeye ait telefon numarası (`+90 212 356 10 57`) ve kurumsal e-posta adresi (`hello@petracoffee.com`) hem GitHub'da hem de `tasarimci-radari.vercel.app/data/leads.json` adresinde filtrelenmeden yayınlanmaktadır. Web botları tarafından toplanarak spam listelerine sokulabilir.

---

## 🛠️ Adım Adım Güvenlik İyileştirme Planı (Action Checklist)

- [ ] **1. Kriptografik Arka Kapıyı Temizle (`api/search_real.py`):**
  - `AUTH_KEY_HASH` sabitini sil.
  - Sadece Vercel panelindeki `STUDIO_SECRET_TOKEN` ortam değişkeniyle `hmac.compare_digest` üzerinden doğrula.
- [ ] **2. Canlı Sunucu Bilgi İfşasını Engelle (`.vercelignore`):**
  - `SECURITY_AUDIT.md`, `*.md`, `package.json`, `pyproject.toml` dosyalarını `.vercelignore` listesine ekle.
- [ ] **3. Canlı Dağıtıma Güvenlik Başlıklarını Ekle (`vercel.json`):**
  - `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` başlıklarını tanımla.
- [ ] **4. `api/search_real.py` Statik Sunucusunu Sıkılaştır:**
  - `os.path.commonpath` ile path prefix açığını kapat; izin verilen uzantı beyaz listesi uygula.
- [ ] **5. Token İletimini Temizle (`src/app.js`):**
  - `&token=...` query parametresini kaldır, sadece `Authorization: Bearer` başlığını kullan.
