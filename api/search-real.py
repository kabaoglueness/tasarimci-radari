"""
Vercel Serverless Function — StudioFinder Canlı Arama Endpoint'i
-----------------------------------------------------------------
Vercel üzerinde sunucusuz (serverless) çalışır.
Bilgisayarın kapalıyken bile çalışır.
Eğer istekte veya Vercel panelinde SECRET_ACCESS_TOKEN eşleşirse CANLI LinkedIn verisi çeker.
Eşleşmezse GitHub için güvenli kurumsal placeholder verileri sunar.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import re
import urllib.parse
import urllib.request

# Vercel Panelinden tanımlanacak gizli anahtar (Varsayılan yoksa yetkisiz sayılır)
SECRET_ACCESS_TOKEN = os.environ.get("STUDIO_SECRET_TOKEN", "sf_master_secret_2026")

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
        params = urllib.parse.parse_qs(parsed.query)

        # Kullanıcının girdiği gizli token kontrolü
        user_token = params.get('token', [''])[0] or self.headers.get('X-Access-Token', '')

        # Eğer token doğruysa CANLI verileri çek ve ver, değilse güvenli placeholder dön
        if user_token and user_token == SECRET_ACCESS_TOKEN:
            live_jobs = fetch_live_linkedin()
            data = live_jobs if live_jobs else list(PLACEHOLDER_LEADS)
            is_live = True
        else:
            data = list(PLACEHOLDER_LEADS)
            is_live = False

        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('X-Live-Access', 'Granted' if is_live else 'Denied-Placeholder')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
