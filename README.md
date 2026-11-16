# 🎯 StudioFinder İstanbul — Tasarımcı Radarı

> **Freelance tasarımcılar ve kreatif ajanslar için İstanbul odaklı canlı müşteri ve iş fırsatı radarı.**  
> Kurumsal ilanları (LinkedIn, Kariyer.net, Bionluk) ve harita üzerindeki yerel işletmeleri tek bir ekranda analiz edin, tasarım ihtiyaçlarını tespit edin ve saniyeler içinde kişiselleştirilmiş teklifler hazırlayın.

---

## ⚡ Neden Tasarımcı Radarı?

Freelance çalışanlar ve tasarımcılar için müşteri bulmak çoğu zaman saatler süren manuel aramalar, LinkedIn taramaları ve portfolyo spam'leme süreçleriyle geçer. **StudioFinder İstanbul**, bu süreci tersine çevirir:

1. **Çok Kanallı Canlı Keşif:** LinkedIn Misafir API, Kariyer.net, Bionluk ve OpenStreetMap üzerinden tekil fırsatları harmanlar.
2. **Tasarım Odaklı İhtiyaç Analizi:** Her potansiyel müşterinin eksiklerini (menü mizanpajı, kurumsal kimlik, sosyal medya şablonları, mobil UI/UX) otomatik modeller.
3. **Akıllı Fırsat Puanı (Score 0-100):** Dönüşüm ihtimali en yüksek fırsatları öne çıkarır.
4. **Tek Tıkla Özel Pitch / Teklif Üretici:** İşletmenin eksiklerine özel, saygılı ve profesyonel soğuk e-posta / Instagram DM metinleri oluşturur.
5. **Sıfır Dış Bağımlılık (Zero Dependencies):** Ek bir kütüphane (`pip install ...`) kurmanıza gerek yoktur; standart Python 3.8+ ile anında çalışır.

---

## 🛠 Mimari & Teknolojik Altyapı

```
                                  ┌─────────────────────────────┐
                                  │       İstemci (Tarayıcı)     │
                                  │ Tailwind CSS + Vanilla JS   │
                                  └──────────────┬──────────────┘
                                                 │
                                                 │ HTTP / JSON
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      StudioFinder Hardened Backend (server.py)             │
│                                                                             │
│  [Güvenlik Katmanı]                                                         │
│  ├── Chroot Path Traversal Koruması (os.path.commonpath)                    │
│  ├── Anti-SSRF & DNS Pinning (Private IP & Whitelist Denetleyicisi)         │
│  ├── CSP, X-Frame-Options, X-Content-Type-Options, CORS                     │
│  └── Girdi Sanitizasyonu & Null-Byte Koruması                               │
│                                                                             │
│  [Veri & Önbellek Motoru]                                                   │
│  ├── ThreadPoolExecutor (Paralel Veri Çekimi)                               │
│  ├── Memory TTL Cache (5 Dakikalık Akıllı Ön Bellekleme)                    │
│  └── Fallback & Kürasyon Motoru                                             │
└──────────────┬─────────────────────────┬────────────────────────────┬───────┘
               │                         │                            │
               ▼                         ▼                            ▼
      LinkedIn Misafir API          Bionluk & Kariyer.net      OpenStreetMap (OSM)
```

---

## 📁 Proje Dosya Yapısı

```bash
tasarimci-radari/
├── data/
│   └── leads.json            # Doğrulanmış yerel müşteri ve ilan veritabanı
├── docs/
│   └── 2026-11-16-design-radar-spec.md  # Ürün spesifikasyonu ve mimari notlar
├── src/
│   ├── app.js                # Frontend orkestrasyonu, filtreleme ve arayüz etkileşimleri
│   └── engine.js             # Fırsat filtreleme, arama ve pitch üretim motoru
├── tests/
│   ├── conversion-tests/     # UI/UX ve dönüşüm test şablonları
│   └── test_security_and_api.py  # Otomatik backend güvenlik & API test paketi
├── BRAND.md                  # Marka kimliği ve tasarım dili rehberi
├── index.html                # Ana arayüz (Modern, duyarlı, karanlık mod)
├── manifest.json             # Web App & PWA yapılandırması
├── requirements.txt          # Bağımlılık tanımı (Standart Kütüphane)
├── server.py                 # Yüksek güvenlikli multithreaded backend sunucusu
├── start.bat                 # Windows için tek tıkla başlatma betiği
└── README.md                 # Proje dokümantasyonu
```

---

## 🚀 Hızlı Başlangıç (Quick Start)

### Gereksinimler
- Python 3.8 veya üzeri (Ekstra paket gerekmez).

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/kullaniciadi/tasarimci-radari.git
cd tasarimci-radari
```

### 2. Sunucuyu Başlatın
**Windows:**
`start.bat` dosyasına çift tıklayabilir veya terminalden:
```bash
python server.py
```

Sunucu varsayılan olarak `http://127.0.0.1:8090` adresinde çalışmaya başlar. Tarayıcınızda açıp kullanabilirsiniz.

---

## ⚙️ Çevresel Değişkenler (Environment Variables)

Sunucu 12-Factor standartlarına uygundur ve aşağıdaki çevresel değişkenlerle yapılandırılabilir:

| Değişken | Varsayılan | Açıklama |
| :--- | :--- | :--- |
| `PORT` | `8090` | Sunucunun dinleyeceği port numarası |
| `HOST` | `127.0.0.1` | Bağlanılacak adres (`0.0.0.0` ile dış dünyaya açılabilir) |
| `CACHE_TTL` | `300` | Arama sonuçlarının saniye cinsinden önbellek geçerlilik süresi |

Örnek (Linux / macOS):
```bash
PORT=3000 HOST=0.0.0.0 python3 server.py
```

Örnek (Windows PowerShell):
```powershell
$env:PORT="3000"; python server.py
```

---

## 🛡️ Güvenlik Sıkılaştırması (Security Hardening)

Açık kaynak olarak yayınlanma standardında geliştirilen `server.py`, aşağıdaki kurumsal güvenlik önlemlerini içerir:

1. **Path Traversal Önleme (LFI Koruması):**
   - URL-decode ve null-byte kontrolü yapılır.
   - İstenen dosya yolu `os.path.realpath` ve `os.path.commonpath` ile doğrulanır; kök dizin dışına yapılan herhangi bir kaçış (örn. `../../windows/win.ini`) engellenerek 404 döndürülür.
   - `server.py`, `start.bat`, `.git`, `.env` gibi hassas sistem dosyalarının statik olarak indirilmesi engellenmiştir.
2. **SSRF & Open-Proxy Koruması:**
   - Dış API çağrıları için domain whitelist (`ALLOWED_OUTBOUND_DOMAINS`) uygulanır.
   - Özel HTTP yönlendirici (`SafeRedirectHandler`), iç ağlara (127.0.0.1, 10.0.0.0/8, 192.168.0.0/16 vb.) ve loopback adreslerine yönlendirme girişimlerini tespit edip iptal eder.
3. **HTTP Güvenlik Başlıkları:**
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: SAMEORIGIN`
   - `X-XSS-Protection: 1; mode=block`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Content-Security-Policy (CSP)`
   - `Access-Control-Allow-Origin: *` & Güvenli CORS
4. **Güvenli Hata Yönetimi:**
   - Sunucu tarafında oluşan hatalarda sistem dosya yolları veya stack trace istemciye sızdırılmaz; standart JSON formatında temiz hata mesajları iletilir.
5. **Girdi Doğrulama ve Sanitizasyon:**
   - Arama sorguları kontrol karakterlerinden arındırılır, uzunlukları sınırlandırılır ve XSS enjeksiyon girişimleri filtrelenir.

---

## 📡 REST API Uç Noktaları

### 1. Fırsat Arama API
```http
GET /api/search-real?query={arama_kelimesi}
```
**Örnek İstek:**
```bash
curl http://127.0.0.1:8090/api/search-real?query=Kafe
```
**Örnek Yanıt (200 OK):**
```json
[
  {
    "id": "li-1-482",
    "type": "job_listing",
    "source": "LinkedIn",
    "name": "Luminara Creative Studio — Grafik Tasarımcısı",
    "sector": "Tasarım & Kreatif",
    "location": {
      "city": "İstanbul",
      "district": "Kağıthane"
    },
    "work_type": "Tam Zamanlı / Hibrit",
    "need_score": 96,
    "urgency": "Aktif LinkedIn İlanı",
    "cover_image": "https://images.unsplash.com/...",
    "design_flaws": [
      "Pozisyon: Grafik Tasarımcısı (Luminara Creative Studio)",
      "Lokasyon: Kağıthane, İstanbul",
      "Tekil doğrulanmış LinkedIn iş ilanı. Doğrudan başvuruya açık."
    ],
    "needed_services": ["Görsel Kimlik", "Kampanya Tasarımı", "Sosyal Medya"],
    "contact": {
      "website": "https://tr.linkedin.com/jobs/view/...",
      "platform": "LinkedIn Tekil İlan",
      "deadline": "Yeni İlan"
    },
    "status": "new",
    "notes": ""
  }
]
```

### 2. Sistem Sağlık Kontrolü (Health Check)
```http
GET /health
```
**Örnek Yanıt (200 OK):**
```json
{
  "status": "healthy",
  "service": "StudioFinder Radar API",
  "version": "1.0.0"
}
```

---

## 🧪 Test Paketi

Backend güvenlik önlemlerini ve API uç noktalarını doğrulamak için hazır bir birim/entegrasyon test paketi bulunur:

```bash
python -m unittest tests/test_security_and_api.py
```

Test kapsamı:
- Health check ve durum kodları
- Statik dosya dağıtımı ve MIME tipleri
- Path traversal (dizin aşımı) ve URL-encode enjeksiyon denemeleri
- `server.py` ve gizli dosya indirme korumaları
- Geçersiz HTTP yöntemlerinin (`POST`, `PUT`) 405 ile reddedilmesi
- CORS `OPTIONS` preflight işleyicisi
- XSS prob girdilerinin filtrelenmesi

---

## 📄 Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır. Dilediğiniz gibi kullanabilir, geliştirebilir ve katkıda bulunabilirsiniz.
