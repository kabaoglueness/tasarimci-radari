# StudioFinder İstanbul - Tasarımcı Radarı

Freelance çalışanlar ve tasarım ekipleri için İstanbul odaklı müşteri ve iş radarı.

LinkedIn ilanları ve yerel işletmeleri tek ekranda listeler, tasarım ihtiyaçlarını puanlar ve doğrudan iletişime geçmek için metin taslağı üretir.

---

## Özellikler

1. **Açık ilanlar ve yerel işletmeler.** LinkedIn iş ilanlarını ve OpenStreetMap üzerindeki yerel mekanları bir arada gösterir.
2. **Tasarım ihtiyaç puanı.** Menü mizanpajı, kurumsal kimlik, sosyal medya şablonları ve mobil arayüz ihtiyaçlarını inceler, 0-100 arası puanlar.
3. **Teklif metni taslağı.** İşletmenin eksiklerine göre kişiselleştirilmiş e-posta veya mesaj metni hazırlar.
4. **12 saatlik döngü ve doğrulama.** Sunucu gece 00:00 ve öğlen 12:00 saatlerinde yeni ilanları kaydeder, kapanan ilanları listeden düşürür.
5. **Standart kütüphane.** Ek paket yüklemesi gerektirmez, Python 3.8 ve üzeri ile çalışır.
6. **Vercel ve mobil destek.** Vercel üzerinde sunucusuz çalışır. Android için Capacitor altyapısı hazırdır.

---

## Mimari

```
                                  ┌─────────────────────────────┐
                                  │       İstemci (Tarayıcı)     │
                                  │ Tailwind CSS + Vanilla JS   │
                                  └──────────────┬──────────────┘
                                                 │
                                                 │ HTTP / JSON
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      StudioFinder Backend (server.py)                       │
│                                                                             │
│  [Güvenlik]                                                                 │
│  ├── Chroot Path Traversal Koruması (os.path.commonpath)                    │
│  ├── SSRF ve DNS Doğrulaması (Domain Whitelist ve Yerel Ağ Engeli)          │
│  ├── CSP, X-Frame-Options, X-Content-Type-Options, CORS                     │
│  └── Girdi Temizleme ve Null-Byte Kontrolü                                  │
│                                                                             │
│  [Veri ve Senkronizasyon]                                                   │
│  ├── SQLite Veritabanı (data/radar.db)                                      │
│  ├── 12 Saatlik Otomatik Senkronizasyon (00:00 ve 12:00)                    │
│  └── Liveness Check (Kapanan ilanları pasife alma)                          │
└──────────────┬─────────────────────────┬────────────────────────────┬───────┘
               │                         │                            │
               ▼                         ▼                            ▼
       LinkedIn Misafir API          Bionluk & Kariyer.net      OpenStreetMap (OSM)
```

---

## Dosya Yapısı

```bash
tasarimci-radari/
├── api/
│   └── search-real.py        # Vercel Serverless arama uç noktası
├── data/
│   └── leads.json            # Varsayılan yerel müşteri ve ilan veritabanı
├── docs/
│   └── DESIGN_SPEC_ANTI_SLOP.md # Tasarım manifestosu ve kural şartnamesi
├── src/
│   ├── app.js                # Arayüz yönetimi ve filtreleme
│   └── engine.js             # Fırsat filtreleme ve arama motoru
├── tests/
│   └── test_security_and_api.py # Güvenlik ve API testleri
├── BRAND.md                  # Kurumsal kimlik ve tasarım standartları
├── index.html                # Ana arayüz (Figma / Notion açık tema)
├── manifest.json             # Web App ve PWA yapılandırması
├── requirements.txt          # Bağımlılık listesi
├── server.py                 # SQLite destekli backend sunucusu
├── start.bat                 # Windows başlatma betiği
├── vercel.json               # Vercel dağıtım kuralları
└── README.md                 # Proje dokümantasyonu
```

---

## Kurulum ve Çalıştırma

### 1. Depoyu klonlayın

```bash
git clone https://github.com/kabaoglueness/tasarimci-radari.git
cd tasarimci-radari
```

### 2. Sunucuyu başlatın

**Windows:**
`start.bat` dosyasına çift tıklayın veya terminalde çalıştırın:

```bash
python server.py
```

Tarayıcınızda `http://localhost:8090` adresini açın.

---

## Ortam Değişkenleri

Sunucu aşağıdaki çevresel değişkenlerle çalışır:

| Değişken | Varsayılan | Açıklama |
| :--- | :--- | :--- |
| `PORT` | `8090` | Sunucunun dinleyeceği port |
| `HOST` | `0.0.0.0` | Bağlantı adresi (Yerel ağ ve telefon erişimi için) |
| `RAPIDAPI_KEY` | Boş | İsteğe bağlı harici ilan API anahtarı |
| `SERPAPI_KEY` | Boş | İsteğe bağlı Google Jobs API anahtarı |

Değişkenleri tanımlamak için `.env.example` dosyasını `.env` olarak kopyalayabilirsiniz. `.env` dosyası Git tarafından takip edilmez.

---

## Güvenlik Önlemleri

- **Path traversal engeli.** Dosya yolları `os.path.commonpath` ile doğrulanır. Kök dizin dışındaki dosya istekleri 404 döner. Sistem ve kaynak kod dosyaları indirmeye kapatılmıştır.
- **SSRF koruması.** Dış API çağrıları için alan adı listesi (`ALLOWED_OUTBOUND_DOMAINS`) kullanılır. Yerel ağ IP adreslerine yönlendirme yapılmaz.
- **Güvenlik başlıkları.** Yanıtlara `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN` ve `Content-Security-Policy` eklenir.
- **Girdi denetimi.** Arama parametreleri uzunluk sınırına tabi tutulur, denetim karakterleri ve HTML etiketleri temizlenir.

---

## API Uç Noktaları

### 1. Fırsat arama

```http
GET /api/search-real?query={arama_kelimesi}
```

Örnek istek:
```bash
curl http://localhost:8090/api/search-real?query=Kafe
```

### 2. Sağlık kontrolü

```http
GET /health
```

Yanıt:
```json
{
  "status": "healthy",
  "service": "StudioFinder Radar API",
  "version": "2.0.0",
  "last_sync": "12 ilan tarandı"
}
```

---

## Testler

Güvenlik ve API testlerini çalıştırmak için:

```bash
python -m unittest tests/test_security_and_api.py
```

11 güvenlik ve uç nokta testi çalıştırılır: path traversal denemeleri, hassas dosya erişimleri, CORS kontrolleri ve girdi temizliği.

---

## Lisans

Bu proje **GNU Affero General Public License v3.0 (AGPL-3.0-or-later)** ile lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına göz atabilirsiniz.
