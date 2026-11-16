# TASARIM RADARI (DesignRadar) — TEKNİK VE TASARIM DOKÜMANI

## 1. Amaç ve Vizyon
Yapay zeka destekli çalışan grafik tasarımcıların, internetteki açık iş ilanlarının yanı sıra **asıl yüksek potansiyelli olan "ilan vermemiş ama görsel/tasarım kalitesi düşük işletmeleri"** nokta atışı tespit edip müşteri portföyü oluşturmalarını sağlayan estetik bir masaüstü/web kokpiti.

## 2. Temel Modüller
1. **İşletme Radarı (Gizli Potansiyel Müşteri Keşfi):**
   - Şehir, ilçe ve sektör filtresi (Örn: *İstanbul / Kadıköy / Özel Klinikler* veya *Restoranlar / Butik Kahveciler*).
   - İşletmenin dijital varlık analizi: Web sitesi var mı? Instagram hesabı aktif mi? Görsel kalitesi nasıl?
   - **Tasarım İhtiyaç Skoru (1-100):** Görselleri zayıf veya sitesi eski olan işletmelere yüksek öncelik puanı atanır.
2. **Açık İlan Radarı (İlan Toplayıcı):**
   - Tasarım iş ilanlarını çalışma modeline (Remote, Hibrit, Yerinde) ve proje tipine (Logo, Sosyal Medya, UI/UX, Ambalaj) göre filtreleme.
3. **Müşteri Kokpiti (Mini Tasarımcı CRM):**
   - Keşfedilen işletmeleri tek tıkla "Radarda", "İletişime Geçilecek", "Teklif Gönderildi", "Kazanıldı" panolarına kaydetme.
   - İletişim bilgileri: Instagram, Web, Telefon, E-posta, Adres ve özel tasarımcı notları.

## 3. UI/UX Tasarım İlkeleri (Taste & Impeccable Standartları)
- **Tasarım Dili:** Linear & Apple sadeliğinde koyu tema (`#09090b` arka plan, `#18181b` kartlar, `border-zinc-800`).
- **Yapay Zeka Klişesi Yok:** Mor gradient, sahte glow, aşırı cam efekti kesinlikle yasak.
- **Tipografi:** Geist / Inter, yüksek hiyerarşi, ferah 8pt grid boşlukları.

## 4. Teknoloji Tercihi
- Hızlı, bağımsız, hafif ve anında tarayıcıda çalışan yerel Python (FastAPI/HTTP server) + Modern Tailwind UI mimarisi.
