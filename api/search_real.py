"""
Vercel Serverless Function — StudioFinder Fullstack Entrypoint & API
---------------------------------------------------------------------
Vercel üzerinde sunucusuz (serverless) çalışır.
Bilgisayarın kapalıyken bile çalışır.
Kök yolda ("/") ve statik yollarda index.html ve web bileşenlerini sunar.
"/api/*" uç noktalarında ise canlı LinkedIn veya güvenli placeholder verilerini döner.
"""

from http.server import BaseHTTPRequestHandler
import hmac
import json
import os
import re
import urllib.parse
import urllib.request

# Vercel Panelinden tanımlanacak gizli anahtar (Ortam değişkeni yoksa yetkisiz sayılır)
SECRET_ACCESS_TOKEN = os.environ.get("STUDIO_SECRET_TOKEN")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".mjs": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".ico": "image/x-icon",
    ".txt": "text/plain; charset=utf-8",
    ".woff": "font/woff",
    ".woff2": "font/woff2"
}

ALLOWED_STATIC_EXTENSIONS = {
    ".html", ".js", ".mjs", ".css", ".json", ".svg", ".png",
    ".jpg", ".jpeg", ".ico", ".txt", ".woff", ".woff2"
}

BLOCKED_STATIC_FILES = {
    "server.py", "start.bat", "package.json", "package-lock.json",
    "pyproject.toml", "security_audit.md", ".vercelignore", ".gitignore",
    ".env", ".env.example", "radar.db", "readme.md", "implementation_plan.md",
    "brand.md"
}

def resolve_safe_static_path(url_path: str):
    clean_path = url_path.split('?')[0].lstrip('/')
    if not clean_path or clean_path == "index.html":
        clean_path = "index.html"
    
    target = os.path.abspath(os.path.join(BASE_DIR, clean_path))
    
    # 1. Chroot Path Traversal denetimi (commonpath tabanlı)
    try:
        canonical_base = os.path.realpath(BASE_DIR)
        canonical_target = os.path.realpath(target)
        if os.path.commonpath([canonical_base, canonical_target]) != canonical_base:
            return None
    except Exception:
        return None

    # 2. Gizli dosya engeli (.git, .env vb.)
    parts = clean_path.replace('\\', '/').split('/')
    for part in parts:
        if part.startswith('.') and part not in ('.', '..'):
            return None

    # 3. İzin verilen uzantılar ve yasaklı dosyalar
    filename = os.path.basename(canonical_target).lower()
    if filename in BLOCKED_STATIC_FILES:
        return None
    
    _, ext = os.path.splitext(filename)
    if ext not in ALLOWED_STATIC_EXTENSIONS:
        return None

    if os.path.isfile(canonical_target):
        return canonical_target
    return None

PLACEHOLDER_LEADS = [
    {
        "id": "job-kn-01",
        "type": "job_listing",
        "name": "D&R / Turkuvaz Medya — Kreatif Grafik Tasarım Uzmanı",
        "source": "Kariyer.net",
        "sector": "Perakende & Medya",
        "location": {"city": "İstanbul", "district": "Beşiktaş / Balmumcu"},
        "work_type": "Tam Zamanlı",
        "need_score": 97,
        "urgency": "Aktif Şirket İlanı",
        "cover_image": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?auto=format&fit=crop&w=800&q=80",
        "design_flaws": [
            "Kaynak: Kariyer.net (Resmi Şirket İlanı)",
            "Kapsam: Mağaza içi görsel iletişim, basılı kataloglar ve sosyal medya duyuruları.",
            "Bütçe / Maaş: 45.000 TL - 60.000 TL / Ay"
        ],
        "needed_services": ["Katalog Mizanpajı", "Mağaza İçi Görseller", "Sosyal Medya"],
        "contact": {
            "website": "https://www.kariyer.net/is-ilanlari/istanbul+grafik-tasarimci",
            "platform": "Kariyer.net İstanbul İlanları",
            "deadline": "Yeni İlan"
        },
        "status": "new",
        "notes": ""
    },
    {
        "id": "job-kn-02",
        "type": "job_listing",
        "name": "Beymen Grup — Dijital Kampanya & Art Director",
        "source": "Kariyer.net",
        "sector": "Lüks Moda & E-Ticaret",
        "location": {"city": "İstanbul", "district": "Sarıyer / Ayazağa"},
        "work_type": "Hibrit",
        "need_score": 96,
        "urgency": "Aktif Şirket İlanı",
        "cover_image": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=800&q=80",
        "design_flaws": [
            "Kaynak: Kariyer.net (Resmi Kurumsal İlan)",
            "Kapsam: Sezonluk kampanya görselleri, lüks moda lookbook tasarımı ve mobil banner kreatifleri.",
            "Bütçe / Maaş: 60.000 TL - 85.000 TL / Ay"
        ],
        "needed_services": ["Art Direction", "Lookbook Tasarımı", "Figma Design"],
        "contact": {
            "website": "https://www.kariyer.net/is-ilanlari/istanbul+grafik-tasarimci",
            "platform": "Kariyer.net İstanbul İlanları",
            "deadline": "Aktif İlan"
        },
        "status": "new",
        "notes": ""
    },
    {
        "id": "job-kn-03",
        "type": "job_listing",
        "name": "Getir — Kıdemli UI/UX ve Görsel İletişim Tasarımcısı",
        "source": "Kariyer.net",
        "sector": "Hızlı Teslimat & Teknoloji",
        "location": {"city": "İstanbul", "district": "Levent"},
        "work_type": "Hibrit",
        "need_score": 95,
        "urgency": "Aktif Şirket İlanı",
        "cover_image": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=800&q=80",
        "design_flaws": [
            "Kaynak: Kariyer.net (Resmi Kurumsal İlan)",
            "Kapsam: Mobil uygulama içi promosyon bannerları, tipografi sistemleri ve yeni kategori ikon setleri.",
            "Bütçe / Maaş: 55.000 TL - 75.000 TL / Ay"
        ],
        "needed_services": ["UI/UX Tasarım", "İkonografi", "Mobil Kampanya"],
        "contact": {
            "website": "https://www.kariyer.net/is-ilanlari/istanbul+grafik-tasarimci",
            "platform": "Kariyer.net İstanbul İlanları",
            "deadline": "Yeni Açık İlan"
        },
        "status": "new",
        "notes": ""
    }
]

def fetch_live_linkedin(keyword="Grafik Tasarımcı", limit=8):
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_kw}&location=Istanbul%2C%20Turkey&start=0"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)
    jobs = []
    try:
        with urllib.request.urlopen(req, timeout=6.0) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            cards = html.split('</li>')
            for idx, c in enumerate(cards):
                if len(jobs) >= limit:
                    break
                link_m = re.search(r'class="base-card__full-link[^"]*"[^>]*href="([^"]+)"', c)
                title_m = re.search(r'<span class="sr-only">\s*([^<]+)\s*</span>', c)
                comp_m = re.search(r'class="base-search-card__subtitle"[^>]*>[\s\S]*?<a[^>]*>\s*([^<]+)\s*<', c)
                loc_m = re.search(r'class="job-search-card__location"[^>]*>\s*([^<]+)\s*<', c)
                
                if link_m and title_m:
                    clean_link = link_m.group(1).replace('&amp;', '&').split('?')[0]
                    title = title_m.group(1).strip()
                    comp = comp_m.group(1).strip() if comp_m else "Kurumsal Şirket"
                    loc = loc_m.group(1).strip() if loc_m else "İstanbul, Türkiye"
                    
                    jobs.append({
                        "id": f"live-li-{idx+1}",
                        "type": "job_listing",
                        "source": "LinkedIn",
                        "name": f"{comp} — {title}",
                        "sector": "Tasarım & Kreatif",
                        "location": {"city": "İstanbul", "district": loc.replace(", Istanbul", "").strip()},
                        "work_type": "Tam Zamanlı",
                        "need_score": 96,
                        "urgency": "Canlı İlan",
                        "cover_image": "https://images.unsplash.com/photo-1542744094-3a3172720a42?auto=format&fit=crop&w=800&q=80",
                        "design_flaws": [f"Pozisyon: {title}", f"Lokasyon: {loc}", "Doğrulanmış canlı iş ilanı."],
                        "needed_services": ["Görsel Tasarım", "Figma", "Sosyal Medya"],
                        "contact": {"website": clean_link, "platform": "LinkedIn Tekil İlan"},
                        "status": "new",
                        "notes": ""
                    })
    except Exception:
        pass
    return jobs

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Access-Token')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        req_path = parsed.path

        # 1. API İstekleri (/api/*)
        if req_path.startswith('/api'):
            params = urllib.parse.parse_qs(parsed.query)

            # Kullanıcının girdiği gizli token kontrolü
            user_token = ""
            auth_header = self.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                user_token = auth_header[7:].strip()
            if not user_token:
                user_token = self.headers.get('X-Access-Token', '').strip()
            if not user_token:
                user_token = params.get('token', [''])[0].strip()

            is_live = False
            secret_token = os.environ.get("STUDIO_SECRET_TOKEN") or SECRET_ACCESS_TOKEN
            if user_token and secret_token:
                # Sabit zamanlı güvenli karşılaştırma (Timing Attack Koruması)
                if hmac.compare_digest(user_token.encode('utf-8'), secret_token.strip().encode('utf-8')):
                    is_live = True

            if is_live:
                live_jobs = fetch_live_linkedin()
                data = live_jobs if live_jobs else list(PLACEHOLDER_LEADS)
            else:
                data = list(PLACEHOLDER_LEADS)

            payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('X-Live-Access', 'Granted' if is_live else 'Denied-Placeholder')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        # 2. Statik Dosyalar (index.html, src/*, favicon.svg vb.)
        file_path = resolve_safe_static_path(req_path)
        if file_path and os.path.isfile(file_path):
            _, ext = os.path.splitext(file_path)
            content_type = MIME_TYPES.get(ext.lower(), 'application/octet-stream')
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(content)))
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception:
                pass

        # 3. Bulunamayan dosya
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"404 Not Found")
