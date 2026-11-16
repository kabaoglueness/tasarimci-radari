# BRAND.md — StudioFinder Kurumsal Kimlik & Dönüşüm Standartları

## 1. Kurum Tonu & Misyon
- **Ton:** Analitik, profesyonel, süssüz B2B radar aracı. Boş vaat veya AI süslemesi yok; doğrudan iş fırsatı ve gelir odaklı.
- **Hedef Kitle:** Profesyonel grafik tasarımcılar, kreatif direktörler ve tasarım stüdyoları.

## 2. Renk Sistemi (60-30-10 Kuralı)
- **%60 Zemin (Canvas):** `#09090b` (Zinc / Slate derin koyu zemin, asla saf #000000 kullanılmaz).
- **%30 Yapı & Kartlar (Panel):** 
  - Kart ve Panel Zemini: `#121215`
  - Hover Zemini: `#18181c`
  - Kenarlıklar (Borders): İnce nötr `#222226` (aktif kartlarda `#383840`)
  - Metin Renkleri: `#f4f4f5` (Ana metin), `#a1a1aa` (İkincil metin), `#71717a` (Mikro etiketler)
- **%10 Kutsal Aksiyon Rengi:** 
  - Yalnızca viewport başındaki **tek birincil işlem butonu** için saf beyaz (`#ffffff`) ve yüksek kontrast kullanılır.
  - Logo, sekmeler veya ikincil butonlar bu rengi tüketemez; nötr/çerçeveli kalır.

## 3. Tipografi Standartları
- **Font Ailesi:** Modern sans-serif `Inter` (Sıfır tırnak, sıfır serif, sıfır slab monospace).
- **Sayısal Veriler:** Skorlar, oranlar ve para birimleri `tabular-nums` ve `text-right` ile taranabilir yapılır.

## 4. Dönüşüm Kuralları
- **Tek Primary CTA:** Viewport başına tek birincil buton. İkincil eylemler ghost (çerçeveli/nötr) yapılır.
- **Güvence Kopyası:** Ana butonun 6-8px altında doğrudan güvence kopyası sunulur.
- **Form Sürtünmesizliği:** Kullanıcı girdileri `onBlur` ile otomatik kaydedilir, gereksiz onay butonları konulmaz.
- **Aksiyon Dürüstlüğü:** Kullanıcıya nereye yönlendirildiği şeffafça söylenir.
