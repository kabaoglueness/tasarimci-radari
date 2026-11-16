# StudioFinder — Vercel Serverless & Güvenlik Sıkılaştırma Planı

- [x] Faz 1: Vercel Deploy Yapılandırması (`.vercelignore`, `pyproject.toml`, `vercel.json`)
  - [x] `server.py`, `android/`, `tests/` Vercel build sürecinden hariç tutulması
  - [x] `pyproject.toml` ile Vercel Python runtime entrypoint (`api.search-real:handler`) tanımlanması
  - [x] `vercel.json` temizlenmesi ve statik/sunucusuz rota ayarlarının yapılması
- [x] Faz 2: Güvenlik Açıklarının Kapatılması (SECURITY_AUDIT.md)
  - [x] Kritik: `api/search-real.py` fallback gizli anahtarının silinmesi ve `hmac.compare_digest` ile timing-attack koruması
  - [x] Yüksek: `server.py` HTTP 'latin-1' başlık kodlama çökmesinin (`X-Last-Sync`) URL-encode ile giderilmesi
  - [x] Yüksek: `src/app.js` DOM XSS açıklarının `escapeHtml` ve `sanitizeUrl` ile filtrelenmesi
  - [x] Orta: `server.py` SQLite WAL modu (`PRAGMA journal_mode=WAL;`) ve busy timeout eklenmesi
  - [x] Orta: Android Manifest ve Capacitor `cleartext` ve `allowBackup` sıkılaştırması
  - [x] Düşük: `data/leads.json` PII (telefon/e-posta) maskelenmesi
- [x] Faz 3: Otomasyon ve Güvenlik Testleri Doğrulaması (`tests/test_security_and_api.py`)
- [x] Faz 4: GitHub `main` Dalına Commit & Push
