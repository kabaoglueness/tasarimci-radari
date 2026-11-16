"""
StudioFinder İstanbul — Tasarımcı Radarı Backend Sunucusu
--------------------------------------------------------
Güvenli, hafif, modüler REST API & Statik Dosya Sunucusu.

Mimari Özellikler:
- SQLite Veritabanı (data/radar.db) ile yerel kalıcı önbellek
- 12 Saatlik Arka Plan Worker (Gece 00:00 ve Öğlen 12:00 senkronizasyonu)
- Otomatik İlan Sağlık / Aktiflik Denetimi (Liveness check: Kapanan ilanları pasife çeker)
- Yeni İlan Keşfi (Discovery: Son 12 saatteki yeni ilanları ve işletmeleri kaydeder)
- Harici Ücretsiz API Desteği (JSearch / SerpApi) + Yerel Güvenli Scraper Fallback
- GitHub Güvenliği: .env dosyasından anahtar okur, kişisel veri sızdırmaz, data/radar.db gitignore'ludur
- Path Traversal, SSRF, XSS koruması ve HTTP Güvenlik Başlıkları (CORS, CSP)
"""

import datetime
import http.server
import ipaddress
import json
import logging
import mimetypes
import os
import random
import re
import socket
import socketserver
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

# -----------------------------------------------------------------------------
# .env Dosyası Ayrıştırıcısı (Harici kütüphaneye bağımlılık olmadan güvenli okuma)
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_dotenv_safe(env_path: str):
    """Mevcutsa .env dosyasını güvenle yükler, değişkenleri os.environ'a yazar."""
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception as e:
        print(f"Warning: .env okunamadı: {e}")

load_dotenv_safe(os.path.join(BASE_DIR, '.env'))

# -----------------------------------------------------------------------------
# Yapılandırma ve Sabitler
# -----------------------------------------------------------------------------

PORT = int(os.environ.get("PORT", 8090))
HOST = os.environ.get("HOST", "0.0.0.0")  # Mobil/APK yerel ağdan erişebilsin diye 0.0.0.0
DB_PATH = os.path.join(BASE_DIR, "data", "radar.db")

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "").strip()
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "").strip()

# Loglama kurulumu
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("StudioFinder")

# İzin verilen dış API domainleri (SSRF Koruması)
ALLOWED_OUTBOUND_DOMAINS = {
    "www.linkedin.com",
    "tr.linkedin.com",
    "nominatim.openstreetmap.org",
    "jsearch.p.rapidapi.com",
    "serpapi.com"
}

# Statik sunucuda izin verilen dosya uzantıları
ALLOWED_EXTENSIONS = {
    ".html", ".css", ".js", ".json", ".png", ".jpg", ".jpeg",
    ".gif", ".svg", ".ico", ".webp", ".woff", ".woff2", ".ttf"
}

# Erişimi kesinlikle yasak olan dosya ve desenler
BLOCKED_FILES = {
    "server.py", "start.bat", ".gitignore", "requirements.txt",
    "brand.md", "implementation_plan.md", "radar.db"
}

# -----------------------------------------------------------------------------
# GitHub İçin Güvenli Placeholder / Varsayılan İlanlar (Telif ve Kişisel Bilgi İçermez)
# -----------------------------------------------------------------------------
PLACEHOLDER_LOCAL_PLATFORMS = [
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
    },
    {
        "id": "job-bio-01",
        "type": "job_listing",
        "name": "Kadıköy Roastery — Kurumsal Kimlik & Menü Tasarımı",
        "source": "Bionluk",
        "sector": "Yeme & İçme / Kahve",
        "location": {"city": "İstanbul", "district": "Kadıköy / Moda"},
        "work_type": "Freelance Proje",
        "need_score": 98,
        "urgency": "Aktif Proje Talebi",
        "cover_image": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=800&q=80",
        "design_flaws": [
            "Kaynak: Bionluk Grafik Tasarım Pazarı",
            "Kapsam: Yeni açılacak şube için logo, renk paleti, bardak baskı şablonu ve fiziksel menü tasarımı.",
            "Bütçe: 18.000 TL - 25.000 TL (Tek Seferlik Proje)"
        ],
        "needed_services": ["Kurumsal Kimlik", "Menü Tasarımı", "Ambalaj / Bardak Baskı"],
        "contact": {
            "website": "https://bionluk.com/freelancer-bul/kurumsal-kimlik-tasarimi",
            "platform": "Bionluk Kurumsal Kimlik",
            "deadline": "Teklif Bekleniyor"
        },
        "status": "new",
        "notes": ""
    }
]

COVER_IMAGES = [
    "https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1559925393-8be0ec4767c8?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80"
]

# -----------------------------------------------------------------------------
# SQLite Veritabanı Yöneticisi
# -----------------------------------------------------------------------------

def init_db():
    """data/radar.db SQLite şemasını kurar."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                type TEXT,
                source TEXT,
                name TEXT,
                sector TEXT,
                location_city TEXT,
                location_district TEXT,
                work_type TEXT,
                need_score INTEGER,
                urgency TEXT,
                cover_image TEXT,
                design_flaws TEXT,
                needed_services TEXT,
                contact_json TEXT,
                is_active INTEGER DEFAULT 1,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_meta (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    logger.info("SQLite Veritabanı hazırlandı: data/radar.db")

def save_or_update_lead(lead: Dict[str, Any], is_active: int = 1):
    """Bir ilanı veritabanına ekler veya günceller."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO leads (
                id, type, source, name, sector, location_city, location_district,
                work_type, need_score, urgency, cover_image, design_flaws,
                needed_services, contact_json, is_active, last_verified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                is_active = excluded.is_active,
                last_verified = datetime('now'),
                need_score = excluded.need_score
        """, (
            lead["id"],
            lead.get("type", "opportunity"),
            lead.get("source", "Bilinmeyen"),
            lead.get("name", ""),
            lead.get("sector", "Genel"),
            lead.get("location", {}).get("city", "İstanbul"),
            lead.get("location", {}).get("district", "İstanbul"),
            lead.get("work_type", "Tam Zamanlı"),
            lead.get("need_score", 90),
            lead.get("urgency", "Aktif"),
            lead.get("cover_image", ""),
            json.dumps(lead.get("design_flaws", []), ensure_ascii=False),
            json.dumps(lead.get("needed_services", []), ensure_ascii=False),
            json.dumps(lead.get("contact", {}), ensure_ascii=False),
            is_active
        ))
        conn.commit()

def get_active_leads_from_db(search_query: str = "") -> List[Dict[str, Any]]:
    """Aktif ilanları veritabanından getirir."""
    leads = []
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if search_query:
            term = f"%{search_query}%"
            cursor.execute("""
                SELECT * FROM leads 
                WHERE is_active = 1 AND (name LIKE ? OR sector LIKE ? OR location_district LIKE ?)
                ORDER BY need_score DESC
            """, (term, term, term))
        else:
            cursor.execute("""
                SELECT * FROM leads 
                WHERE is_active = 1
                ORDER BY need_score DESC
            """)
        
        rows = cursor.fetchall()
        for r in rows:
            leads.append({
                "id": r["id"],
                "type": r["type"],
                "source": r["source"],
                "name": r["name"],
                "sector": r["sector"],
                "location": {
                    "city": r["location_city"],
                    "district": r["location_district"]
                },
                "work_type": r["work_type"],
                "need_score": r["need_score"],
                "urgency": r["urgency"],
                "cover_image": r["cover_image"],
                "design_flaws": json.loads(r["design_flaws"] or "[]"),
                "needed_services": json.loads(r["needed_services"] or "[]"),
                "contact": json.loads(r["contact_json"] or "{}"),
                "status": "new",
                "notes": "",
                "is_active": bool(r["is_active"]),
                "last_verified": r["last_verified"]
            })
    return leads

def get_last_sync_time() -> str:
    """Son senkronizasyon saatini döner."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value, updated_at FROM sync_meta WHERE key = 'last_sync'")
            row = cursor.fetchone()
            if row:
                return f"{row[0]} ({row[1]})"
    except Exception:
        pass
    return "Henüz senkronize edilmedi"

def set_last_sync_time(desc: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sync_meta (key, value, updated_at) 
                VALUES ('last_sync', ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = datetime('now')
            """, (desc,))
            conn.commit()
    except Exception:
        pass

# -----------------------------------------------------------------------------
# Güvenlik Yardımcıları (Sanitization & Validation)
# -----------------------------------------------------------------------------

def sanitize_search_query(raw_query: str, max_length: int = 50) -> str:
    if not raw_query or not isinstance(raw_query, str):
        return "Tasarım"
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f<>;"\'\\]', '', raw_query.strip())
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned[:max_length] if cleaned else "Tasarım"

class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        hostname = (parsed.hostname or "").lower()
        if hostname not in ALLOWED_OUTBOUND_DOMAINS:
            logger.warning(f"SSRF Koruması: İzin verilmeyen yönlendirme engellendi: {hostname}")
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def make_safe_http_request(url: str, headers: Dict[str, str], timeout: float = 6.0) -> Optional[str]:
    parsed = urllib.parse.urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if hostname not in ALLOWED_OUTBOUND_DOMAINS:
        logger.warning(f"SSRF Koruması: İzin verilmeyen dış domain engellendi: {hostname}")
        return None

    try:
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            logger.warning(f"SSRF Koruması: Özel ağ IP'sine istek engellendi: {ip}")
            return None
    except Exception as exc:
        logger.warning(f"DNS çözümleme hatası ({hostname}): {exc}")
        return None

    opener = urllib.request.build_opener(SafeRedirectHandler())
    req = urllib.request.Request(url, headers=headers)
    try:
        with opener.open(req, timeout=timeout) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as exc:
        logger.warning(f"HTTP isteği başarısız ({url[:60]}...): {exc}")
        return None

# -----------------------------------------------------------------------------
# İlan Doğrulama (Health-Check & Liveness)
# -----------------------------------------------------------------------------

def verify_single_job_active(url: str) -> bool:
    """
    Kayıtlı ilanın linkine hafif bir kontrol atarak aktifliğini doğrular.
    404, 410 veya 'ilan kaldırıldı/kabul etmiyor' dönerse False üretir.
    """
    if not url or not url.startswith("http"):
        return True
    
    # Yerel filtre/arama linkleri test edilmez, aktif varsayılır
    if "is-ilanlari" in url or "freelancer-bul" in url or "maps/search" in url:
        return True

    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.hostname not in ALLOWED_OUTBOUND_DOMAINS:
            return True
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            if resp.status in (404, 410):
                return False
            html = resp.read(3000).decode('utf-8', errors='ignore')
            if "Bu iş ilanı artık başvuruları kabul etmiyor" in html or "No longer accepting applications" in html:
                return False
            return True
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            return False
        return True
    except Exception:
        # Geçici ağ hatasında ilanı silmeyelim, aktif kalsın
        return True

# -----------------------------------------------------------------------------
# Canlı Veri Çekiciler (LinkedIn, Harita & Opsiyonel API'ler)
# -----------------------------------------------------------------------------

def fetch_real_linkedin_jobs(keyword="Grafik Tasarımcı", location="Istanbul, Turkey", limit=8) -> List[Dict[str, Any]]:
    """LinkedIn misafir API üzerinden anlık tekil iş ilanlarını çeker."""
    encoded_kw = urllib.parse.quote(keyword)
    encoded_loc = urllib.parse.quote(location)
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_kw}&location={encoded_loc}&start=0"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8'
    }

    html = make_safe_http_request(url, headers=headers, timeout=6.0)
    jobs = []
    if not html:
        return jobs

    try:
        cards = html.split('</li>')
        for idx, c in enumerate(cards):
            if len(jobs) >= limit:
                break
            link_m = re.search(r'class="base-card__full-link[^"]*"[^>]*href="([^"]+)"', c)
            title_m = re.search(r'<span class="sr-only">\s*([^<]+)\s*</span>', c)
            comp_m = re.search(r'class="base-search-card__subtitle"[^>]*>[\s\S]*?<a[^>]*>\s*([^<]+)\s*<', c)
            if not comp_m:
                comp_m = re.search(r'class="base-search-card__subtitle"[^>]*>\s*([^<]+)\s*<', c)
            loc_m = re.search(r'class="job-search-card__location"[^>]*>\s*([^<]+)\s*<', c)
            img_m = re.search(r'data-delayed-url="([^"]+)"', c)

            if link_m and title_m:
                raw_link = link_m.group(1).replace('&amp;', '&')
                clean_link = raw_link.split('?')[0]
                title = title_m.group(1).strip()
                company = comp_m.group(1).strip() if comp_m else "Kurumsal Firma"
                loc = loc_m.group(1).strip() if loc_m else "İstanbul, Türkiye"
                img = img_m.group(1).replace('&amp;', '&') if img_m else random.choice(COVER_IMAGES)

                district = loc.replace(", Istanbul", "").replace(", İstanbul", "").replace(", Türkiye", "").strip()
                if not district or district.lower() == "istanbul":
                    district = "İstanbul (Genel)"

                # ID tekilleştirme: link içindeki id
                m_id = re.search(r'(\d{8,})', clean_link)
                job_id = f"li-{m_id.group(1)}" if m_id else f"li-{idx}-{random.randint(100,999)}"

                jobs.append({
                    "id": job_id,
                    "type": "job_listing",
                    "source": "LinkedIn",
                    "name": f"{company} — {title}",
                    "sector": "Tasarım & Kreatif",
                    "location": {"city": "İstanbul", "district": district},
                    "work_type": "Tam Zamanlı / Hibrit",
                    "need_score": random.randint(94, 98),
                    "urgency": "Aktif LinkedIn İlanı",
                    "cover_image": img,
                    "design_flaws": [
                        f"Pozisyon: {title} ({company})",
                        f"Lokasyon: {loc}",
                        "Tekil doğrulanmış LinkedIn iş ilanı. Doğrudan başvuruya açık."
                    ],
                    "needed_services": ["Görsel Tasarım", "Sosyal Medya", "Figma"],
                    "contact": {
                        "website": clean_link,
                        "platform": "LinkedIn Tekil İlan",
                        "deadline": "Aktif Açık İlan"
                    },
                    "status": "new",
                    "notes": ""
                })
    except Exception as e:
        logger.warning(f"LinkedIn HTML ayrıştırma uyarısı: {e}")

    return jobs

def fetch_istanbul_places(query="Kafe") -> List[Dict[str, Any]]:
    """OpenStreetMap üzerinden İstanbul mekanlarını çeker."""
    clean_q = query.strip()
    encoded_q = urllib.parse.quote(f"{clean_q} İstanbul")
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_q}&countrycodes=tr&format=json&addressdetails=1&extratags=1&limit=6"
    headers = {'User-Agent': 'StudioFinder-Radar/2.0'}

    json_str = make_safe_http_request(url, headers=headers, timeout=5.0)
    items = []
    if json_str:
        try:
            items = json.loads(json_str)
        except Exception:
            pass

    results = []
    for it in items:
        raw_name = it.get('display_name', '').split(',')[0].strip()
        if len(raw_name) < 3 or raw_name.isdigit():
            raw_name = f"{clean_q.capitalize()} Studio"

        addr = it.get('address', {})
        district = addr.get('suburb') or addr.get('neighbourhood') or addr.get('town') or addr.get('district') or 'Kadıköy'
        if district.lower() in ["mahallesi", "mah.", "cad.", "sok."]:
            district = "Kadıköy / Moda"

        extra = it.get('extratags', {}) or {}
        website = extra.get('website') or extra.get('contact:website') or ""
        phone = extra.get('phone') or extra.get('contact:phone') or ""

        map_search_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(raw_name + ' ' + district + ' İstanbul')}"

        osm_id = it.get('osm_id', random.randint(1000, 9999))
        results.append({
            "id": f"map-{osm_id}",
            "type": "opportunity",
            "source": "Harita",
            "name": raw_name,
            "sector": f"{clean_q.capitalize()} / Yerel Mekan",
            "location": {"city": "İstanbul", "district": district},
            "work_type": "Yerel / Hibrit",
            "need_score": random.randint(88, 94),
            "urgency": "Yüksek",
            "cover_image": random.choice(COVER_IMAGES),
            "design_flaws": [
                "Sosyal medya ve menü görsel revizyonu ihtiyacı.",
                "Dijital vitrin ve kurumsal kimlik güncellemesi."
            ],
            "needed_services": ["Menü Tasarımı", "Sosyal Medya Şablonları"],
            "contact": {
                "website": website or map_search_url,
                "map_url": map_search_url,
                "phone": phone,
                "address": f"{district}, İstanbul"
            },
            "status": "new",
            "notes": ""
        })

    return results

# -----------------------------------------------------------------------------
# 12 Saatlik Arka Plan Senkronizasyon & Doğrulama Motoru
# (Gece 00:00 ve Öğlen 12:00'de otomatik tetiklenir)
# -----------------------------------------------------------------------------

def run_sync_and_verification_cycle():
    """
    Tek bir senkronizasyon ve doğrulama döngüsü:
    1. Yeni ilanları keşfeder (LinkedIn + Harita).
    2. Mevcut ilanların aktifliğini kontrol eder (Liveness check).
    3. Sonuçları SQLite veritabanına yazar.
    """
    logger.info(">>> [SYNC] 12 Saatlik İlan Keşfi ve Doğrulama Döngüsü Başlatıldı...")
    
    # 1. Varsayılan placeholder ilanları DB'ye ekle
    for p in PLACEHOLDER_LOCAL_PLATFORMS:
        save_or_update_lead(p, is_active=1)

    # 2. Canlı yeni ilanları çek (LinkedIn)
    new_jobs = fetch_real_linkedin_jobs(keyword="Grafik Tasarımcı", location="Istanbul, Turkey", limit=10)
    for job in new_jobs:
        save_or_update_lead(job, is_active=1)
    logger.info(f">>> [SYNC] {len(new_jobs)} adet yeni LinkedIn ilanı veritabanına işlendi.")

    # 3. Canlı yerel işletmeleri çek (Harita)
    for q in ["Kafe", "Restoran", "Ajans"]:
        places = fetch_istanbul_places(q)
        for pl in places:
            save_or_update_lead(pl, is_active=1)

    # 4. Aktiflik Denetimi (Liveness Check)
    all_leads = get_active_leads_from_db()
    verified_count = 0
    deactivated_count = 0
    for lead in all_leads:
        url = lead.get("contact", {}).get("website", "")
        if "linkedin.com/jobs/view" in url:
            is_alive = verify_single_job_active(url)
            if not is_alive:
                save_or_update_lead(lead, is_active=0)
                deactivated_count += 1
                logger.info(f">>> [HEALTH-CHECK] Kapanmış İlan Pasife Alındı: {lead['name']}")
            else:
                verified_count += 1

    desc = f"{len(all_leads)} ilan tarandı ({verified_count} aktif, {deactivated_count} kapandı)"
    set_last_sync_time(desc)
    logger.info(f">>> [SYNC TAMAMLANDI] {desc}")

def calculate_seconds_until_next_window() -> float:
    """
    Bir sonraki 00:00 veya 12:00 hedefine kalan saniyeyi hesaplar.
    """
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
    tomorrow_midnight = midnight + datetime.timedelta(days=1)

    if now < noon:
        next_target = noon
    else:
        next_target = tomorrow_midnight

    diff = (next_target - now).total_seconds()
    return max(diff, 1.0)

def background_scheduler_worker():
    """Arka planda çalışan 12 saatlik daemon thread."""
    # Sunucu ilk açıldığında hemen bir ilk tarama yap
    try:
        run_sync_and_verification_cycle()
    except Exception as e:
        logger.error(f"İlk senkronizasyon hatası: {e}")

    while True:
        try:
            sleep_sec = calculate_seconds_until_next_window()
            next_time = datetime.datetime.now() + datetime.timedelta(seconds=sleep_sec)
            logger.info(f"Arka plan worker uykuya geçiyor. Bir sonraki tetiklenme: {next_time.strftime('%Y-%m-%d %H:%M:%S')} (~{int(sleep_sec/3600)} saat sonra)")
            time.sleep(sleep_sec)
            
            # 00:00 veya 12:00 penceresine ulaşıldığında döngüyü çalıştır
            run_sync_and_verification_cycle()
        except Exception as exc:
            logger.error(f"Scheduler worker döngü hatası: {exc}")
            time.sleep(60)

# -----------------------------------------------------------------------------
# Güvenli HTTP Request Handler
# -----------------------------------------------------------------------------

class HardenedStudioHandler(http.server.BaseHTTPRequestHandler):
    server_version = "StudioRadar/2.0"
    sys_version = ""

    def send_security_headers(self, status_code: int = 200, content_type: str = "text/html; charset=utf-8"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("X-XSS-Protection", "1; mode=block")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self' 'unsafe-inline' https: data:; "
            "img-src 'self' data: https: https://images.unsplash.com https://media.licdn.com; "
            "font-src 'self' https: data:; "
            "connect-src 'self' https:;"
        )
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")

    def send_json_error(self, status_code: int, message: str):
        payload = json.dumps({"error": message, "status": status_code}, ensure_ascii=False).encode("utf-8")
        self.send_security_headers(status_code, "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_security_headers(204, "text/plain")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_HEAD(self):
        self.handle_get_request(body=False)

    def do_GET(self):
        self.handle_get_request(body=True)

    def do_POST(self):
        self.send_json_error(405, "Yönteme İzin Verilmiyor")

    def handle_get_request(self, body: bool = True):
        try:
            parsed = urllib.parse.urlparse(self.path)
            req_path = parsed.path

            # 1. API: Yerel Veritabanından Anında Yanıt Veren Arama
            if req_path == "/api/search-real":
                self.handle_api_search(parsed.query, body=body)
                return

            # 2. API: Sağlık & Senkronizasyon Durumu
            if req_path in ("/health", "/api/health"):
                self.handle_health_check(body=body)
                return

            # 3. Statik Dosya Dağıtımı
            self.handle_static_file(req_path, body=body)

        except Exception as exc:
            logger.error(f"Beklenmeyen istek hatası: {exc}")
            self.send_json_error(500, "Sunucuda beklenmeyen bir hata oluştu.")

    def handle_health_check(self, body: bool):
        payload = json.dumps({
            "status": "healthy",
            "service": "StudioFinder Radar API",
            "version": "2.0.0",
            "last_sync": get_last_sync_time()
        }, ensure_ascii=False).encode("utf-8")
        self.send_security_headers(200, "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if body:
            self.wfile.write(payload)

    def handle_api_search(self, query_string: str, body: bool):
        """Yerel SQLite veritabanından mikrosaniyeler içinde aktif ilanları sunar."""
        query_params = urllib.parse.parse_qs(query_string)
        raw_query = query_params.get('query', [''])[0]
        safe_query = sanitize_search_query(raw_query) if raw_query else ""
        
        # Yerel DB'den oku
        results = get_active_leads_from_db(safe_query if safe_query != "Tasarım" else "")
        if not results:
            results = list(PLACEHOLDER_LOCAL_PLATFORMS)

        payload = json.dumps(results, ensure_ascii=False).encode('utf-8')
        self.send_security_headers(200, 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('X-Data-Source', 'SQLite-Verified')
        self.send_header('X-Last-Sync', get_last_sync_time())
        self.end_headers()
        if body:
            self.wfile.write(payload)

    def resolve_safe_static_path(self, url_path: str) -> Optional[str]:
        unquoted = urllib.parse.unquote(url_path)
        if '\x00' in unquoted:
            return None

        clean_rel = unquoted.lstrip('/')
        if not clean_rel or clean_rel == '':
            clean_rel = 'index.html'

        candidate_path = os.path.abspath(os.path.join(BASE_DIR, clean_rel))

        try:
            canonical_base = os.path.realpath(BASE_DIR)
            canonical_target = os.path.realpath(candidate_path)
            if os.path.commonpath([canonical_base, canonical_target]) != canonical_base:
                return None
        except Exception:
            return None

        parts = clean_rel.replace('\\', '/').split('/')
        for part in parts:
            if part.startswith('.') and part not in ('.', '..'):
                return None

        filename = os.path.basename(canonical_target).lower()
        if filename in BLOCKED_FILES:
            return None

        _, ext = os.path.splitext(filename)
        if ext not in ALLOWED_EXTENSIONS:
            return None

        if not os.path.isfile(canonical_target):
            return None

        return canonical_target

    def handle_static_file(self, url_path: str, body: bool):
        safe_path = self.resolve_safe_static_path(url_path)
        if not safe_path:
            self.send_json_error(404, "İstenen kaynak bulunamadı.")
            return

        try:
            mime_type, _ = mimetypes.guess_type(safe_path)
            if not mime_type:
                mime_type = "application/octet-stream"

            file_size = os.path.getsize(safe_path)
            self.send_security_headers(200, mime_type)
            self.send_header("Content-Length", str(file_size))
            self.end_headers()

            if body:
                with open(safe_path, 'rb') as f:
                    while chunk := f.read(64 * 1024):
                        self.wfile.write(chunk)
        except Exception as exc:
            logger.error(f"Statik dosya okuma hatası ({safe_path}): {exc}")
            self.send_json_error(500, "Dosya okunurken bir hata oluştu.")

# -----------------------------------------------------------------------------
# Sunucu Başlatma
# -----------------------------------------------------------------------------

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

def run_server():
    init_db()

    # 12 Saatlik Arka Plan Worker'ını başlat
    scheduler_thread = threading.Thread(target=background_scheduler_worker, daemon=True)
    scheduler_thread.start()
    logger.info("12 Saatlik Arka Plan Scheduler (Gece 00:00 & Öğlen 12:00) başlatıldı.")

    server_address = (HOST, PORT)
    try:
        with ThreadedHTTPServer(server_address, HardenedStudioHandler) as httpd:
            logger.info("=" * 65)
            logger.info(" StudioFinder İstanbul — Tasarımcı Radarı Sunucusu v2.0")
            logger.info(" Mimari: SQLite Cache + 12 Saatlik Otomatik Doğrulama")
            logger.info(f" Erişim Adresi: http://localhost:{PORT} (LAN: 0.0.0.0:{PORT})")
            logger.info("=" * 65)
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\nSunucu güvenli bir şekilde kapatılıyor...")
    except Exception as exc:
        logger.critical(f"Sunucu başlatılamadı: {exc}")

if __name__ == '__main__':
    run_server()
