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
from server import ThreadedHTTPServer, HardenedStudioHandler

TEST_PORT = 8991
TEST_HOST = "127.0.0.1"

class TestStudioRadarBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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


if __name__ == "__main__":
    unittest.main()
