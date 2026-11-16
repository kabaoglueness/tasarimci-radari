# StudioFinder — Güvenlik Açıklarını Kapatma ve Sıkılaştırma Planı (v2.0)

- [x] Faz 1: `api/search_real.py` Güvenlik Sıkılaştırması
  - [x] `AUTH_KEY_HASH` sabitini sil ve kimlik doğrulamayı sadece `STUDIO_SECRET_TOKEN` ortam değişkenine bağla (`hmac.compare_digest`).
  - [x] `resolve_safe_static_path` içindeki path prefix açığını `os.path.commonpath` ve dosya uzantısı/kara liste denetimi ile kapat.
- [x] Faz 2: Canlı Dağıtım İfşa Koruması (`.vercelignore`)
  - [x] `SECURITY_AUDIT.md`, `*.md`, `docs/`, `package.json`, `pyproject.toml` dosyalarını ekle.
- [x] Faz 3: Canlı HTTP Güvenlik Başlıkları (`vercel.json`)
  - [x] `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy` ve `Permissions-Policy` başlıklarını tanımla.
- [x] Faz 4: İstemci Token İletimi ve PII Temizliği (`src/app.js` & `data/leads.json`)
  - [x] `src/app.js`: URL `&token=...` parametresini kaldır, sadece `Authorization: Bearer` ve `X-Access-Token` başlıklarını gönder.
  - [x] `data/leads.json`: Açık telefon/e-posta verilerini maskele / mock veriye çevir.
- [x] Faz 5: Testlerin ve Doğrulamanın Yapılması (`tests/test_security_and_api.py`)
  - [x] Yeni güvenlik kontrolleri için unit testleri güncelle ve çalıştır (21 testin tümü geçti).
