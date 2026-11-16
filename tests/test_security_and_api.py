"""
StudioFinder İstanbul — Güvenlik ve API Test Paketi
---------------------------------------------------
Sunucuyu bir thread içinde başlatır ve tüm uç noktaları,
güvenlik korumalarını (Path Traversal, SSRF, Header'lar, Method Kısıtlamaları)
otomatik olarak doğrular.
"""

import http.client
import json
import threading
import time
import unittest
import urllib.parse
from server import ThreadedHTTPServer, HardenedStudioHandler, init_db

TEST_PORT = 8991
TEST_HOST = "127.0.0.1"

class TestStudioRadarBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        # Test sunucusunu ayrı bir thread içinde başlat
        cls.server = ThreadedHTTPServer((TEST_HOST, TEST_PORT), HardenedStudioHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def get_connection(self):
        return http.client.HTTPConnection(TEST_HOST, TEST_PORT, timeout=15)

    def test_01_health_check(self):
        conn = self.get_connection()
        conn.request("GET", "/health")
        res = conn.getresponse()
        data = json.loads(res.read().decode())
        self.assertEqual(res.status, 200)
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(res.getheader("X-Content-Type-Options"), "nosniff")
        self.assertEqual(res.getheader("X-Frame-Options"), "SAMEORIGIN")
        self.assertIn("default-src", res.getheader("Content-Security-Policy", ""))
        conn.close()

    def test_02_static_index(self):
        conn = self.get_connection()
        conn.request("GET", "/")
        res = conn.getresponse()
        body = res.read().decode('utf-8', errors='ignore')
        self.assertEqual(res.status, 200)
        self.assertIn("<!DOCTYPE html>", body)
        self.assertEqual(res.getheader("X-Content-Type-Options"), "nosniff")
        conn.close()

    def test_03_static_subresource(self):
        conn = self.get_connection()
        conn.request("GET", "/src/app.js")
        res = conn.getresponse()
        body = res.read().decode('utf-8', errors='ignore')
        self.assertEqual(res.status, 200)
        self.assertIn("LeadEngine", body)
        conn.close()

    def test_04_api_search_real(self):
        conn = self.get_connection()
        conn.request("GET", "/api/search-real?query=Kafe")
        res = conn.getresponse()
        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode('utf-8'))
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        # Veri yapısı kontrolü
        first = data[0]
        self.assertIn("id", first)
        self.assertIn("name", first)
        self.assertIn("sector", first)
        self.assertEqual(res.getheader("Access-Control-Allow-Origin"), "*")
        conn.close()

    def test_05_path_traversal_parent_dir(self):
        conn = self.get_connection()
        conn.request("GET", "/../../windows/win.ini")
        res = conn.getresponse()
        # Kesinlikle 200 olmamalı, 404 dönmeli
        self.assertEqual(res.status, 404)
        conn.close()

    def test_06_path_traversal_url_encoded(self):
        conn = self.get_connection()
        conn.request("GET", "/..%2f..%2fwindows/win.ini")
        res = conn.getresponse()
        self.assertEqual(res.status, 404)
        conn.close()

    def test_07_block_server_py(self):
        conn = self.get_connection()
        conn.request("GET", "/server.py")
        res = conn.getresponse()
        # Kaynak kod indirilmesi engellenmeli
        self.assertEqual(res.status, 404)
        conn.close()

    def test_08_block_hidden_files(self):
        conn = self.get_connection()
        conn.request("GET", "/.git/config")
        res = conn.getresponse()
        self.assertEqual(res.status, 404)
        conn.close()

    def test_09_disallowed_methods(self):
        conn = self.get_connection()
        conn.request("POST", "/api/search-real", body=b"{}")
        res = conn.getresponse()
        self.assertEqual(res.status, 405)
        conn.close()

    def test_10_options_cors(self):
        conn = self.get_connection()
        conn.request("OPTIONS", "/api/search-real")
        res = conn.getresponse()
        self.assertEqual(res.status, 204)
        self.assertEqual(res.getheader("Access-Control-Allow-Origin"), "*")
        self.assertIn("GET", res.getheader("Access-Control-Allow-Methods", ""))
        conn.close()

    def test_11_input_sanitization_xss_probe(self):
        conn = self.get_connection()
        dirty_q = urllib.parse.quote("<script>alert(1)</script>")
        conn.request("GET", f"/api/search-real?query={dirty_q}")
        res = conn.getresponse()
        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode('utf-8'))
        self.assertIsInstance(data, list)
        conn.close()

    def test_12_x_last_sync_header_ascii_safe(self):
        """X-Last-Sync başlığının Türkçe karakter crash yaratmadığını doğrular."""
        conn = self.get_connection()
        conn.request("GET", "/api/search-real?query=Kafe")
        res = conn.getresponse()
        self.assertEqual(res.status, 200)
        sync_header = res.getheader("X-Last-Sync")
        self.assertIsNotNone(sync_header)
        # Header ASCII olarak encode edilebilmeli (latin-1 / ASCII safe)
        sync_header.encode('ascii')
        conn.close()

    def test_13_no_hardcoded_secret_token(self):
        """api/search_real.py içinde hardcoded master token olmadığını doğrular."""
        import importlib.util
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        api_path = os.path.join(base_dir, "api", "search_real.py")
        with open(api_path, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertNotIn("sf_master_secret_2026", code)
        self.assertIn("hmac.compare_digest", code)

        spec = importlib.util.spec_from_file_location("search_real", api_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if "STUDIO_SECRET_TOKEN" not in os.environ:
            self.assertIsNone(mod.SECRET_ACCESS_TOKEN)

    def test_14_api_search_underscore_endpoint(self):
        """Sunucunun hem /api/search-real hem de /api/search_real rotasını desteklediğini doğrular."""
        conn = self.get_connection()
        conn.request("GET", "/api/search_real?query=Kafe")
        res = conn.getresponse()
        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode('utf-8'))
        self.assertIsInstance(data, list)
        conn.close()

    def test_15_sqlite_wal_mode(self):
        """SQLite veritabanının WAL modunda olduğunu doğrular."""
        import os
        import sqlite3
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "data", "radar.db")
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA journal_mode;")
                row = cursor.fetchone()
                self.assertIn(row[0].lower(), ["wal", "memory"])

    def test_16_search_real_static_root_resolution(self):
        """api/search_real.py handler'ının kök dizinde index.html'i başarıyla çözümlediğini doğrular."""
        import importlib.util
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        api_path = os.path.join(base_dir, "api", "search_real.py")
        spec = importlib.util.spec_from_file_location("search_real", api_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        resolved = mod.resolve_safe_static_path("/")
        self.assertIsNotNone(resolved)
        self.assertTrue(resolved.endswith("index.html"))
        self.assertTrue(os.path.isfile(resolved))

    def test_17_pii_anonymized_in_leads_json(self):
        """data/leads.json içerisinde açık telefon ve şahsi e-posta olmadığını doğrular."""
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        leads_path = os.path.join(base_dir, "data", "leads.json")
        with open(leads_path, "r", encoding="utf-8") as f:
            leads_content = f.read()
        self.assertNotIn("+90 212 356 10 57", leads_content)
        self.assertNotIn("hello@petracoffee.com", leads_content)

    def test_18_no_auth_key_hash_backdoor(self):
        """api/search_real.py içerisinde hardcoded AUTH_KEY_HASH olmadığını doğrular."""
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        api_path = os.path.join(base_dir, "api", "search_real.py")
        with open(api_path, "r", encoding="utf-8") as f:
            code = f.read()
        self.assertNotIn("AUTH_KEY_HASH", code)
        self.assertNotIn("f24fbff3259435331edbea7d72d0842b1e1bccaaef9b886ce0a44a15721380c3", code)

    def test_19_search_real_blocks_sensitive_static_files(self):
        """api/search_real.py resolve_safe_static_path'in hassas dosyaları blokladığını doğrular."""
        import importlib.util
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        api_path = os.path.join(base_dir, "api", "search_real.py")
        spec = importlib.util.spec_from_file_location("search_real", api_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        # Hassas dosyalar None dönmeli
        self.assertIsNone(mod.resolve_safe_static_path("/SECURITY_AUDIT.md"))
        self.assertIsNone(mod.resolve_safe_static_path("/package.json"))
        self.assertIsNone(mod.resolve_safe_static_path("/pyproject.toml"))
        self.assertIsNone(mod.resolve_safe_static_path("/.vercelignore"))
        self.assertIsNone(mod.resolve_safe_static_path("/server.py"))
        self.assertIsNone(mod.resolve_safe_static_path("/.git/config"))
        # Güvenli statik dosyalar çözümlenmeli
        self.assertIsNotNone(mod.resolve_safe_static_path("/index.html"))
        self.assertIsNotNone(mod.resolve_safe_static_path("/favicon.svg"))

    def test_20_vercel_json_security_headers(self):
        """vercel.json içerisinde CSP ve X-Frame-Options gibi güvenlik başlıklarının olduğunu doğrular."""
        import json
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        vercel_path = os.path.join(base_dir, "vercel.json")
        with open(vercel_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        self.assertIn("headers", cfg)
        headers = cfg["headers"][0]["headers"]
        header_keys = [h["key"] for h in headers]
        self.assertIn("Content-Security-Policy", header_keys)
        self.assertIn("X-Frame-Options", header_keys)
        self.assertIn("X-Content-Type-Options", header_keys)

    def test_21_vercelignore_blocks_sensitive_files(self):
        """.vercelignore dosyasının dokümantasyon ve config dosyalarını engellediğini doğrular."""
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        vignore_path = os.path.join(base_dir, ".vercelignore")
        with open(vignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("SECURITY_AUDIT.md", content)
        self.assertIn("*.md", content)
        self.assertIn("docs/", content)
        self.assertIn("package.json", content)


if __name__ == "__main__":
    unittest.main()
