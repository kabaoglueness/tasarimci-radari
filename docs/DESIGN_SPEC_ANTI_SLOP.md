# StudioFinder: Anti-Slop Tasarım Manifestosu & Beceri Şartnamesi
**Belge Türü:** B2B SaaS Dönüşüm Tasarımı, Ergonomi & Anti-Slop Rehberi  
**Hedef Kitle:** Kıdemli Tasarım Mimarları, Frontend Mühendisleri, Subagent Ağı  
**Referans:** `c:\Projects\tasarimci-radari` Canlı Deneyimi, Kullanıcı Direktifleri & Saha İncelemeleri  

---

## 1. Giriş: Anti-Slop & B2B Radar Tasarım Felsefesi

Modern arayüz geliştirmede yapay zeka ajanlarının ve şablon kütüphanelerinin en tehlikeli yanılgısı, bir arayüzün "şık", "karanlık" veya "fütüristik" görünmesini onun profesyonel bir çalışma aracı olması için yeterli sanmasıdır. Dribbble veya soyut tasarım konseptlerinde parlayan neon mor gradient'ler, sahte parıltılar (glow) ve her köşeye fırlatılan anlamsız tipografik süslemeler, gerçek bir tasarımcının ekmek teknesi olan bir B2B radar kokpitinde ilk saniyede çöker:

1. **B2B Radar Gerçekliği:** Bir grafik tasarımcı, sanat yönetmeni veya ajans kurucusu bu arayüze "eğlenmek" için girmez. Zamanı kısıtlıdır; dakikalar içinde açık ilanları ve gizli müşteri potansiyellerini taramak, ihtiyaç skorunu görmek, portfolyosunu göndereceği doğru bağlantıya ulaşmak ve hazır outreach taslağını kopyalayıp aksiyona geçmek zorundadır. Burada çalışan bir arayüz süs havuzu değil, bir gelir ve dönüşüm motorudur.
2. **Kör Estetik Yanılgısı:** Yapay zekanın "tasarım yapıyorum" sanarak her yere primary buton rengi yapıştırması, arama kutularında ikonla metni çakıştırması, mobilde header öğelerini sıkıştırıp görünmez kılması veya kullanıcıyı genel bir iş arama motoru ana sayfasına yönlendirip "işte başvurdun" demesi tam bir kullanıcı deneyimi sahteciliğidir.
3. **Anti-Slop Disiplini:** Kullanıcının bu projede ortaya koyduğu tavizsiz tavır, tasarımda gereksiz her pikselleri ayıklamayı, tırnaklı/ayaklı yazı tiplerini reddetmeyi, tek bir birincil aksiyona odaklanmayı ve sıfır sürtünmeyle (zero friction) çalışmayı mutlak standart haline getirmiştir.

---

## 2. Ne İstenmedi (Anti-Patterns / Yasaklar) ve Nedenleri

### 2.1. Tipografi Sahteciliği: Tırnaklı (Serif) ve Monospace Ayaklı Fontlar vs Saf Modern Sans-Serif `Inter`
- **Yasaklanan Model:** B2B analitik kokpitte tırnaklı (serif) fontlar veya `font-mono` etiketiyle çağrılan JetBrains Mono / Courier benzeri belirgin slab-serif (ayaklı) monospace fontlar kullanmak.
- **Kullanıcının Direktifi:** *"Tırnaklı fontlar, serif detayları ve monospace ayakları kesinlikle kabul edilemez. B2B radar kokpiti jilet gibi modern, nötr ve saf sans-serif `Inter` olmak zorunda."*
- **Tasarım Psikolojisi & Nedenleri:**
  - JetBrains Mono veya klasik monospace fontlar, kod editörlerinde satır takibi için alt ve üst kısımlarında belirgin ayaklara (slab serif) sahiptir. Ancak bu fontlar bir B2B arayüzün metinlerinde veya butonlarında kullanıldığında arayüzü 1990'ların terminal pencerelerine ya da amatör "hacker temalı" kripto sitelerine çevirir.
  - Serif (tırnaklı) fontlar ise edebi yayınlar veya klasik lüks markalar için uygundur; analitik veri tarayan bir tasarımcı için gözü yoran, taranabilirliği (scannability) düşüren görsel pürüzler üretir.
  - Tasarımcılara yönelik bir araç, tasarımcının kendi estetik ciddiyetine hitap etmelidir.
- **Doğru Uygulama:**
  - Font ailesi global düzeyde sıfır tavizle modern sans-serif `Inter` olarak sabitlenmiştir. Monospace tanımları dahi Inter'e zorlanarak ayaklı glifler tamamen ortadan kaldırılmıştır:
  ```html
  <!-- index.html -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  
  <style>
    * {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    .tabular-data { font-variant-numeric: tabular-nums; }
  </style>
  ```

---

### 2.2. Tailwind CSS Kırılması: `pl-8.5` Sınıf Hatası ve İkon-Placeholder Çakışması
- **Yasaklanan Model:** Tailwind'in varsayılan ölçeğinde bulunmayan hayali bir sınıf olan `pl-8.5` yazıp arama ikonunu placeholder metninin üstüne bindirmek.
- **Tasarım Psikolojisi & Hata Analizi:**
  - Tailwind CSS `spacing` skalasında `8` (2rem = 32px) ve `9` (2.25rem = 36px) vardır; `pl-8.5` varsayılan olarak derlenmez veya CSS motoru tarafından yoksayılır.
  - Arama ikonu `absolute left-3` (12px) konumunda ve 14px genişliğindedir (toplam 26px sağ sınır). `pl-8.5` çalışmadığında input'un sol boşluğu sıfırlanır ya da yetersiz kalır ve placeholder metninin ilk 2-3 harfi ("İşletme...") doğrudan büyüteç ikonunun göbeğine biner.
  - Bu hata, yapay zeka ajanlarının CSS'i görsel olarak test etmeden ezbere sınıf uydurmasının (hallucinated utility class) tipik bir örneğidir. Kullanıcı arayüze ilk baktığı anda arama kutusundaki bu amatörlük güveni yerle bir eder.
- **Doğru Uygulama:**
  - Standart ve cerrahi `pl-9` sınıfı: İkon 12px'ten başlar, 26px'te biter; metin ise tam 36px'ten başlayarak 10px'lik kusursuz bir optik nefes payı bırakır:
  ```html
  <!-- YANLIŞ (AI Slop - İkonla Metin Üst Üste) -->
  <input class="pl-8.5 pr-8 py-1.5 ..." placeholder="İşletme, şirket veya ilçe ara..." />

  <!-- DOĞRU (Cerrahi Tailwind Standartı) -->
  <input 
    id="search-input" 
    type="text" 
    placeholder="İşletme, şirket veya ilçe ara... (Kadıköy, Beşiktaş)"
    class="w-full bg-canvas border border-borderSubtle rounded-lg pl-9 pr-8 py-1.5 text-xs text-fg-main placeholder-fg-faint focus:outline-none focus:border-fg-muted transition-colors font-sans"
  />
  ```

---

### 2.3. Dar Ekran & Mobil Boğulması: Tek Satıra Tıkıştırılan Üst Bar (Header Collapse)
- **Yasaklanan Model:** Logo, sürüm rozeti, radar kapsamı, arama kutusu ve canlı sayaç rozetini tek bir `flex-row items-center justify-between` içine zorlayarak dar ekranda (375px - 414px) öğeleri ekranın dışına taşırmak veya arama kutusunu 40px'e ezmek.
- **Tasarım Psikolojisi & Nedenleri:**
  - Masaüstünde geniş ekranda ferah duran yatay yerleşim, mobilde veya dikey bölünmüş pencerelerde (split-screen) arama kutusunun tamamen kaybolmasına ya da canlı sayaç gibi kritik durum bildirimlerinin ekran dışına taşmasına yol açar.
  - Kullanıcı mobilde girdiğinde arama yapamaz hale gelir ve navigasyon kullanılamaz olur.
- **Doğru Uygulama:**
  - 2 satırlı responsive düzen mimarisi (`flex flex-col sm:flex-row`). Mobilde 1. satırda Marka ve Sayaç yan yana korunur; 2. satırda Arama Kutusu tam genişlik (`w-full`) alır. Masaüstünde (`sm:`) ise kendiliğinden tek satıra toparlanır:
  ```html
  <header class="border-b border-borderSubtle px-4 sm:px-6 py-2.5 sm:py-0 sm:h-14 flex flex-col sm:flex-row sm:items-center justify-between bg-panel shrink-0 z-30 gap-2.5 sm:gap-4">
    <!-- Satır 1: Logo + Marka + Canlı Hedef Sayacı (Mobilde Asla Kırpılmaz) -->
    <div class="flex items-center justify-between sm:justify-start gap-3 shrink-0">
      <div class="flex items-center gap-2.5">
        <div class="w-7 h-7 rounded-md bg-panel border border-borderStrong text-white flex items-center justify-center font-bold text-xs tracking-tight">SF</div>
        <span class="font-bold text-sm tracking-tight text-white">StudioFinder</span>
      </div>
      <!-- Mobilde de sağ üstte daima net görünen sayaç -->
      <div class="flex sm:hidden items-center gap-1.5 px-2.5 py-1 rounded-lg border border-borderSubtle bg-canvas text-xs font-semibold tabular-data text-fg-muted">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span class="text-white font-bold" id="mobile-count-stats">0</span>
        <span>Hedef</span>
      </div>
    </div>

    <!-- Satır 2 (Mobilde Tam Genişlik, Masaüstünde Merkez) -->
    <div class="w-full sm:flex-1 sm:max-w-md relative">
      <input id="search-input" class="w-full pl-9 pr-8 py-1.5 ..." />
    </div>
  </header>
  ```

---

### 2.4. Aksiyon Sahteciliği: Genel Arama Sayfasına Atarak Kullanıcıyı Aldatmak (False Promise Links)
- **Yasaklanan Model:** Kartın veya detayın üzerindeki butona "Başvur" yazıp, tıklandığında kullanıcıyı Kariyer.net'in jenerik ana sayfasına (`kariyer.net/is-ilanlari`) veya rastgele bir arama listesine fırlatmak.
- **Kullanıcının Direktifi:** *"Kullanıcıya tekil bir ilan vaat edip genel arama motoruna fırlatmak dönüşümü öldürür ve güveni sıfırlar. Nereye gittiği şeffafça söylenmeli veya doğrudan tekil ilana bağlanmalıdır."*
- **Tasarım Psikolojisi & Nedenleri:**
  - Kullanıcı butonda "İlana Doğrudan Başvur" gördüğünde, tıklar tıklamaz o spesifik firmanın başvuru formunun açılacağını varsayar. Karşısına yüzlerce alakasız sonucun olduğu genel bir arama kutusu çıktığında bilişsel kırılma (cognitive whiplash) yaşar ve sekmeyi derhal kapatır.
  - Aksiyon dürüstlüğü (Action Honesty), B2B dönüşümün en yüksek kuralıdır. Kullanıcıyı yanıltmak yerine, eldeki verinin doğasını netçe açıklamak saygı ve güven üretir.
- **Doğru Uygulama:**
  - Kaynağa göre buton başlığı ve 6-8px altındaki mikro güvence kopyası dinamik ve şeffaf olarak uyarlanır:
  ```javascript
  // src/app.js
  if (lead.source === 'LinkedIn') {
    primaryCtaTitle = 'LinkedIn İlanına Doğrudan Başvur ↗';
    primaryCtaSub = 'Doğrulanmış tekil iş ilanı • Doğrudan şirket başvuru sayfası';
  } else if (lead.source === 'Kariyer.net') {
    primaryCtaTitle = 'Kariyer.net İlan Listesini Aç ↗';
    primaryCtaSub = 'İstanbul grafik tasarım arama listesi • Güncel açık ilanlar';
  } else if (lead.source === 'Harita') {
    primaryCtaTitle = 'Google Haritalar Profilini Aç ↗';
    primaryCtaSub = 'İşletme lokasyonu • Doğrudan iletişim ve menü incelemesi';
  }
  ```

---

### 2.5. Viewport Başına Çoklu Primary Buton Karmaşası (White Contrast Cannibalization)
- **Yasaklanan Model:** Koyu tema arayüzde hem logo arka planını, hem filtre sekmelerini, hem "Teklifi Kopyala" butonunu, hem de ana başvuru butonunu saf beyaz (`#ffffff`) yapmak.
- **Tasarım Psikolojisi & Nedenleri:**
  - Koyu temada (`#09090b` zemin) saf beyaz (`#ffffff`) en yüksek fotometrik lüminesansa ve optik çekim gücüne sahiptir. Göz istemsizce beyaz lekelere kilitlenir.
  - Bir ekranda 3-4 farklı beyaz buton yarıştığında, Fitts ve Hick Kanunları çiğnenir; kullanıcının karar verme süresi uzar ve ana dönüşüm aksiyonunun etkisi kaybolur.
  - 60-30-10 Kuralı: %60 zemin, %30 panel/kart, **%10 kutsal aksiyon rengi**. Saf beyaz, yalnızca kullanıcının tıklamasını istediğimiz en kritik tekil eyleme tahsis edilmelidir.
- **Doğru Uygulama:**
  - "Teklifi Kopyala" butonu ghost/nötr stile çekilmiştir (`bg-panel hover:bg-panelHover text-white border border-borderSubtle`).
  - Filtre sekmelerinde beyaz dolgu kaldırılmış, nötr gri vurgu (`bg-[#27272a] text-white border-[#3f3f46]`) kullanılmıştır.
  - Viewport'taki TEK saf beyaz dolgulu buton, doğrudan başvuru CTA'sı olarak izole edilmiştir:
  ```html
  <!-- TEK PRIMARY CTA (Kutsal %10 Beyaz Aksiyon Butonu) -->
  <a 
    href="${directUrl}" 
    target="_blank" 
    class="w-full py-3 px-4 rounded-xl font-bold text-xs sm:text-sm bg-white hover:bg-zinc-200 text-zinc-950 flex items-center justify-between transition-all duration-150 active:scale-[0.98] shadow-md shadow-white/5"
  >
    <span>${primaryCtaTitle}</span>
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
  </a>

  <!-- İKİNCİL GHOST BUTON (Teklifi Kopyala - Asla Saf Beyaz Zemin Alamaz) -->
  <button id="copy-pitch-btn" class="absolute bottom-3 right-3 px-3 py-1.5 rounded-lg bg-panel hover:bg-panelHover text-white border border-borderSubtle hover:border-borderStrong font-medium text-xs ...">
    <span>Teklifi Kopyala</span>
  </button>
  ```

---

### 2.6. Form Sürtünmesi: Gereksiz "Notu Kaydet" Butonu
- **Yasaklanan Model:** Tasarımcının müşteri adayı için girdiği özel not alanının altına ayrı bir "Kaydet" butonu koymak ve kullanıcı basmadığında notu kaybetmek.
- **Tasarım Psikolojisi & Nedenleri:**
  - Modern B2B araçlarında (Linear, Notion, Figma) her mini girdi için "Kaydet" butonuna basma zorunluluğu ilkel ve sürtünmeli (friction-heavy) bir deneyimdir.
  - Tasarımcı notunu yazar, başka bir karta tıklar; butona basmayı unuttuysa verisi uçar. Bu durum kullanıcıda anksiyete ve öfke yaratır.
- **Doğru Uygulama:**
  - Manuel buton tamamen kaldırılmıştır. `textarea` üzerinde `onBlur` olayı yakalanarak veri arka planda otomatik kaydedilir.
  - Kullanıcıyı rahatlatmak için sağ üstte 1.8 saniye görünüp kaybolan sessiz bir mikro onay rozeti (`Kaydedildi ✓`) tetiklenir:
  ```javascript
  // src/app.js
  const notesArea = document.getElementById('lead-notes-area');
  const hint = document.getElementById('notes-saved-hint');

  if (notesArea) {
    const triggerSave = () => {
      engine.updateLeadNotes(lead.id, notesArea.value);
      if (hint) {
        hint.classList.remove('opacity-0');
        hint.classList.add('opacity-100');
        setTimeout(() => {
          hint.classList.remove('opacity-100');
          hint.classList.add('opacity-0');
        }, 1800);
      }
    };
    notesArea.addEventListener('blur', triggerSave);
  }
  ```

---

### 2.7. Boş Ekran Eylemsizliği (Dead Empty State)
- **Yasaklanan Model:** Sayfa ilk açıldığında veya hiçbir kart seçili değilken sağ detay panelinde sadece "Lütfen soldan bir kayıt seçin" yazıp kullanıcıyı eylemsiz bir çıkmaza hapsetmek.
- **Tasarım Psikolojisi & Nedenleri:**
  - Pasif boş durumlar (dead ends) kullanıcının akışını (flow state) kesintiye uğratır. Kullanıcı "Şimdi ne yapmalıyım?" tereddüdüne düşer.
  - Arayüz kullanıcıyı beklemez; onu nazikçe ve proaktif olarak bir sonraki mantıklı adıma yönlendirmelidir.
- **Doğru Uygulama:**
  - Detay paneli boşken pasif metnin altına tek tıkla ilk adayı açan birincil katalizör butonu (`İlk Fırsatı İncele →`) yerleştirilmiştir:
  ```html
  <!-- src/app.js: renderDetail() boş durum -->
  <div class="h-full flex flex-col items-center justify-center text-center p-8 text-fg-faint text-xs gap-3">
    <p class="font-semibold text-fg-main text-sm">Hedef İnceleme Kokpiti</p>
    <p class="text-[11px] text-fg-faint mt-1 max-w-xs">Listeden bir açık ilan veya müşteri fırsatı seçerek teklif taslağını ve başvuru detaylarını görüntüleyin.</p>
    <button id="select-first-lead-btn" class="mt-2 text-xs font-semibold px-4 py-2 rounded-lg bg-panel hover:bg-panelHover border border-borderStrong text-white transition-all active:scale-[0.98]">
      İlk Fırsatı İncele →
    </button>
  </div>
  ```

---

### 2.8. Sayısal Veri Düzensizliği: Orantısal ve Sola Yaslı Metrikler
- **Yasaklanan Model:** İhtiyaç skorları, fiyatlar ve başarı yüzdelerini standart orantısal (proportional) fontlarla ve sola dayalı olarak listelemek.
- **Tasarım Psikolojisi & Nedenleri:**
  - Orantısal fontlarda `1` rakamı dar, `8` veya `0` geniştir. Bu yüzden alt alta gelen rakamlarda genişlikler zıplar (jitter).
  - Skorları soldan hizalamak, kullanıcının gözünün dikey tarama (vertical scanning) hızını %40 oranında yavaşlatır. Tasarımcı 20 adayı tararken en yüksek skorlu olanı anında göremez.
- **Doğru Uygulama:**
  - Skor ve metrik verilerinde `tabular-nums` ve `text-right` zorunlu kılınmıştır. Bütün rakam glifleri eşit optik sütun genişliği alır ve sağ kenardan dikey bir çizgi gibi hizalanır:
  ```html
  <div class="flex items-center gap-1 text-[11px] font-sans tabular-nums text-right shrink-0">
    <span class="${lead.need_score >= 95 ? 'text-amber-400 font-bold' : 'text-fg-muted font-semibold'}">
      %${lead.need_score}
    </span>
    <span class="text-[10px] text-fg-faint font-medium">İhtiyaç</span>
  </div>
  ```

---

## 3. Ne İstendi (Best Practices / Kurallar) ve Nedenleri

### 3.1. 60-30-10 Kuralı ile Koyu Tema Renk Disiplini
- **%60 Zemin (Canvas):** `#09090b` (Karanlık ama asla gözü kör eden saf `#000000` değil).
- **%30 Yapı & Kartlar (Panel):** `#121215` (Kart zemini), `#222226` (Sessiz kenarlıklar), `#f4f4f5` (Ana metin).
- **%10 Kutsal Aksiyon Rengi:** Saf Beyaz (`#ffffff`). Yalnızca dönüştürücü tekil CTA'ya aittir.

### 3.2. Mikro-Kopyada Risk Tersine Çevirme (Risk Reversal Guarantee)
- Ana başvuru butonunun tam 6-8px altında daima tek cümlelik bir güvence kopyası sunulmalıdır:
  `"Doğrulanmış tekil iş ilanı • Doğrudan şirket başvuru sayfası"` veya `"Doğrulanmış kaynak • Aracı komisyonu yok"`.
- Bu mikro kopya, butona basma öncesindeki son saniye tereddüdünü (click hesitation) sıfırlar.

### 3.3. Hazır Pitch & Kopyalama Ergonomisi
- Tasarımcı her müşteri adayı için sıfırdan e-posta veya mesaj yazmak zorunda kalmamalıdır.
- Hedefin türüne (İş ilanı vs Yerel müşteri fırsatı) göre dinamik olarak üretilen profesyonel, yapay zeka klişelerinden arındırılmış Türkçe outreach taslağı hazır sunulmalı; tek tıkla kopyalanıp görsel geri bildirim verilmelidir.

---

## 4. Özel Skill Katkısı (Skill Contribution Snippet)

Bu bölüm, kullanıcının global beceri kütüphanesine (`C:\Users\Lost_\.gemini\config\skills\...` altındaki `conversion-design`, `taste` veya `impeccable`) doğrudan eklenebilecek kompakt şartname özetidir.

```markdown
<!-- START: B2B RADAR & ANTI-SLOP CONVERSION SPECIFICATION -->
### B2B Cockpit & Anti-Slop Conversion Kuralları (Radar & Directory UI)

1. **Yasaklı Tipografi (Slab Monospace & Serif Yasağı):**
   - B2B analitik kokpitlerde, dashboard'larda ve radar araçlarında ayaklı monospace fontlar (JetBrains Mono'nun slab serif ayakları vb.) ve tırnaklı (serif) fontlar KULLANILMAZ.
   - Tüm arayüz jilet keskinliğinde, optik dengeli modern nötr sans-serif `Inter` ile oluşturulmalıdır.

2. **Cerrahi Tailwind Sınıf Hassasiyeti (No Hallucinated Classes):**
   - Tailwind'de varsayılan olmayan sınıflar (`pl-8.5` vb.) yazılamaz. Input içi sol ikonlarda (`left-3`, 14px ikon) metin başlangıcı mutlaka `pl-9` (36px) yapılarak ikon ile placeholder çakışması kesinlikle önlenir.

3. **Asla Kırpılmayan 2 Satırlı Mobil Header:**
   - Dar ekranlarda (375-414px) header tek satıra sıkıştırılamaz. 1. satırda Marka ve Canlı Sayaç korunur; 2. satırda Arama Girişi tam genişlik (`w-full`) alır.

4. **Aksiyon Dürüstlüğü (No False Promise Links):**
   - Kullanıcıya "İlana Başvur" vaat edip genel arama motoru sayfasına yönlendirmek yasaktır. Tekil ilansa doğrulanmış link verilir; arama listesiyse butonda "İlan Listesini Aç" denilerek mikro kopyada durum şeffafça açıklanır.

5. **Viewport Başına Tek Primary CTA (60-30-10 Kuralı):**
   - Koyu temada saf beyaz (`#ffffff`) en yüksek kontrasttır. Viewport'ta sadece tek birincil işlem butonu saf beyaz olabilir.
   - İkincil butonlar ("Teklifi Kopyala", "WhatsApp"), sekmeler ve logo asla saf beyaz zemin ile ana aksiyonla yarışamaz; nötr hayalet (ghost/panel) stile çekilir.

6. **Form Sürtünmesizliği (onBlur Auto-save):**
   - Hızlı not veya metin girişlerinde "Kaydet" butonu konulmaz. Veri `onBlur` anında sessizce depolanır ve geçici bir "Kaydedildi ✓" rozetiyle güven verilir.

7. **Eyleme Geçiren Boş Ekran (Actionable Empty State):**
   - Detay panelleri veya listeler boşken eylemsiz bırakılamaz. Doğrudan birincil aksiyonu başlatan bir buton ("İlk Fırsatı İncele →") yerleştirilir.

8. **Sayısal Metrik Taranabilirliği (tabular-nums & text-right):**
   - Yüzdeler, oranlar, skorlar ve para birimleri `tabular-nums` ve `text-right` ile dikey hizada taranabilir kılınır.
<!-- END: B2B RADAR & ANTI-SLOP CONVERSION SPECIFICATION -->
```

---

## 5. Uygulama ve Doğrulama Matrisi

| Dosya / Bileşen | Eski Hali (AI Slop / Hatalı) | Yeni Hali (Anti-Slop / Düzeltilmiş) | Kullanıcı Direktifi & Tasarım Gerekçesi |
| :--- | :--- | :--- | :--- |
| `index.html` (Fontlar) | Monospace ayaklı slab serif ve karmaşık font tanımları | Global düzeyde saf, modern sans-serif `Inter` zorlaması | "Tırnaklı fontlar ve monospace ayakları kesinlikle kabul edilemez." |
| `index.html` (Search Input) | `pl-8.5` geçersiz Tailwind sınıfı (İkon ile metin çakışması) | `pl-9` cerrahi sınıf (12px ikon konumu, 36px metin başlangıcı) | "Arama ikonu ile arama metni üst üste biniyor, düzelt." |
| `index.html` (Header) | Mobilde sıkışan, arama kutusunu ezen tek satırlı header | 2 satırlı responsive düzen (`flex-col sm:flex-row`), mobilde tam genişlik | "Mobilde header elemanları kırpılıyor ve sığmıyor." |
| `src/app.js` (Aksiyon Linkleri) | Kariyer.net için yanıltıcı genel arama yönlendirmesi | Şeffaf buton adı ("İlan Listesini Aç") ve net mikro güvence kopyası | "Kariyer.net genel sayfaya atıyor, dönüşümü öldürüyor, şeffaf ol." |
| `src/app.js` (CTA Hiyerarşisi) | Birden fazla saf beyaz buton ("Teklifi Kopyala" + "Başvur") | Yalnızca tek Primary CTA saf beyaz; kopyalama butonu nötr ghost stil | "Viewport başına tek primary CTA olmalı, beyaz rengi tekilleştir." |
| `src/app.js` (Not Alanı) | Manuel "Notu Kaydet" butonu ve unutulduğunda veri kaybı | `onBlur` ile otomatik sessiz kaydetme & yeşil mikro bildirim rozeti | "Not için ekstra kaydet butonu gereksiz sürtünme yaratıyor." |
| `src/app.js` (Empty State) | "Kayıt seçin" yazan eylemsiz, ölü boş ekran | Tek tıkla ilk adayı açan "İlk Fırsatı İncele →" butonu | "Boş ekran kullanıcıyı çıkmaza sokmamalı, aksiyona yönlendirmeli." |
| `src/app.js` (Kart Skorları) | Orantısal font, sola dayalı rakamlar (okuma zıplaması) | `text-right tabular-nums` (Dikey hizada milimetrik tarama) | "Skorlar taranabilir olmalı, rakam genişlikleri zıplamamalı." |

---

## 6. Sonuç

Bu şartname, `c:\Projects\tasarimci-radari` (StudioFinder) projesinde kullanıcının bizzat yönettiği cerrahi düzeltmelerin kurumsal bir özetidir. Görselliğin işlevselliğe ve dönüşüme hizmet ettiği, yapay zeka klişelerinin ve sözde estetik süslemelerinin ayıklandığı bu ilkeler; gelecekte eğitilecek `conversion-design`, `taste` ve `impeccable` becerilerinin en temel yapı taşlarını oluşturacaktır.
