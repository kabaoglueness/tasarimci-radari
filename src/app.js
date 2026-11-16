import { LeadEngine } from './engine.js';

/**
 * DOM XSS saldırılarına karşı HTML varlık filtreleme (CWE-79 Remediation)
 */
export function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Güvensiz protokolleri (javascript:, data:, vb.) engelleyen URL temizleyici
 */
export function sanitizeUrl(url) {
  if (!url || typeof url !== 'string') return '#';
  const clean = url.trim();
  if (clean.startsWith('http://') || clean.startsWith('https://')) return clean;
  return '#';
}

let engine;
let activeDetailTab = 'overview'; // 'overview' | 'pitch'

async function init() {
  let initialData = [];
  try {
    const res = await fetch('./data/leads.json');
    initialData = await res.json();
  } catch (err) {
    console.error('Veri yüklenemedi:', err);
  }

  engine = new LeadEngine(initialData);
  populateSectorOptions();
  setupEventListeners();
  render();

  // Canlı backend verisini eşitle
  try {
    const apiBase = engine.getServerUrl();
    const token = engine.getSecretToken();
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
      headers['X-Access-Token'] = token;
    }
    const liveRes = await fetch(`${apiBase}/api/search_real?query=Tasarım`, {
      headers: headers
    });
    const liveAccessStatus = liveRes.headers.get('X-Live-Access');
    const badge = document.getElementById('live-status-badge');

    if (badge) {
      if (liveAccessStatus === 'Granted') {
        badge.className = 'flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-lg border border-emerald-300 bg-emerald-50 text-emerald-800';
        badge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span><span>Canlı Veri Aktif</span>';
      } else if (token) {
        badge.className = 'flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-lg border border-rose-300 bg-rose-50 text-rose-800';
        badge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-rose-500"></span><span>Geçersiz Token</span>';
      } else {
        badge.className = 'flex items-center gap-1.5 text-[11px] font-semibold px-2 py-1 rounded-lg border border-borderSubtle bg-canvas text-fg-muted';
        badge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-zinc-400"></span><span>Demo Modu</span>';
      }
    }

    if (liveRes.ok) {
      const liveData = await liveRes.json();
      if (Array.isArray(liveData) && liveData.length > 0) {
        if (liveAccessStatus === 'Granted') {
          // Canlı ilanları en üste al
          const liveIds = new Set(liveData.map(l => l.id));
          const others = engine.leads.filter(l => !liveIds.has(l.id));
          engine.leads = [...liveData, ...others];
        } else {
          const existingIds = new Set(engine.leads.map(l => l.id));
          const unique = liveData.filter(l => !existingIds.has(l.id));
          if (unique.length > 0) {
            engine.leads = [...unique, ...engine.leads];
          }
        }
        engine.saveToStorage();
        populateSectorOptions();
        render();
      }
    }
  } catch (e) {
    console.warn('Canlı sunucu verisi arka planda alınamadı, doğrulanmış yerel liste devrede.');
  }
}

function populateSectorOptions() {
  const sectorSelect = document.getElementById('sector-select');
  if (!sectorSelect) return;

  const sectors = engine.getSectors();
  sectorSelect.innerHTML = '<option value="all">Tüm Sektörler</option>';
  sectors.forEach(sector => {
    const opt = document.createElement('option');
    opt.value = sector;
    opt.textContent = sector;
    sectorSelect.appendChild(opt);
  });
}

function setupEventListeners() {
  // Hızlı Arama
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      engine.setFilter('search', e.target.value);
      renderGrid();
    });

    searchInput.addEventListener('keydown', async (e) => {
      if (e.key === 'Enter' && searchInput.value.trim().length > 2) {
        const query = searchInput.value.trim();
        try {
          const apiBase = engine.getServerUrl();
          const res = await fetch(`${apiBase}/api/search_real?city=İstanbul&query=${encodeURIComponent(query)}`);
          const newLeads = await res.json();
          if (Array.isArray(newLeads) && newLeads.length > 0) {
            const existingIds = new Set(engine.leads.map(l => l.id));
            const uniqueNew = newLeads.filter(l => !existingIds.has(l.id));
            if (uniqueNew.length > 0) {
              engine.leads = [...uniqueNew, ...engine.leads];
              engine.saveToStorage();
              populateSectorOptions();
              render();
            }
          }
        } catch (err) {
          console.warn('Canlı tarama hatası:', err);
        }
      }
    });

    // Klavye Kısayolu (/)
    window.addEventListener('keydown', (e) => {
      if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
        e.preventDefault();
        searchInput.focus();
      }
    });
  }

  // Kaynak / Platform Filtre Butonları
  const sourceBtns = document.querySelectorAll('.source-filter-btn');
  sourceBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      sourceBtns.forEach(b => {
        b.classList.remove('source-tab-btn-active', 'border-zinc-900', 'shadow-sm');
        b.classList.add('text-fg-muted', 'bg-canvas', 'border-borderSubtle');
      });
      btn.classList.add('source-tab-btn-active', 'border-zinc-900', 'shadow-sm');
      btn.classList.remove('text-fg-muted', 'bg-canvas', 'border-borderSubtle');

      const source = btn.dataset.source;
      engine.setFilter('source', source);
      renderGrid();
    });
  });

  // Hedef Türü Butonları (Tümü, İlanlar, Fırsatlar)
  const typeBtns = document.querySelectorAll('.filter-type-btn');
  typeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      typeBtns.forEach(b => {
        b.classList.remove('border-zinc-900', 'bg-zinc-900', 'text-white', 'shadow-xs');
        b.classList.add('border-borderSubtle', 'bg-white', 'text-fg-muted');
      });
      btn.classList.add('border-zinc-900', 'bg-zinc-900', 'text-white', 'shadow-xs');
      btn.classList.remove('border-borderSubtle', 'bg-white', 'text-fg-muted');

      engine.setFilter('type', btn.dataset.type);
      renderGrid();
    });
  });

  // Sektör Seçimi
  const sectorSelect = document.getElementById('sector-select');
  if (sectorSelect) {
    sectorSelect.addEventListener('change', (e) => {
      engine.setFilter('sector', e.target.value);
      renderGrid();
    });
  }

  // Sıralama
  const sortSelect = document.getElementById('sort-select');
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      engine.setFilter('sortBy', e.target.value);
      renderGrid();
    });
  }
}

function render() {
  updateBadges();
  renderGrid();
  renderDetail();
}

function updateBadges() {
  const counts = engine.getSourceCounts();
  const setBadge = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };

  setBadge('badge-source-all', counts.all || 0);
  setBadge('badge-source-linkedin', counts['LinkedIn'] || 0);
  setBadge('badge-source-kariyernet', counts['Kariyer.net'] || 0);
  setBadge('badge-source-bionluk', counts['Bionluk'] || 0);
  setBadge('badge-source-harita', counts['Harita'] || 0);

  const headerStats = document.getElementById('header-count-stats');
  if (headerStats) {
    headerStats.textContent = engine.leads.length;
  }
  const mobileStats = document.getElementById('mobile-count-stats');
  if (mobileStats) {
    mobileStats.textContent = engine.leads.length;
  }
}

function getSourceStyle(source) {
  // Notion & Figma Light Studio Pill Stilleri
  switch (source) {
    case 'LinkedIn':
      return {
        pill: 'bg-sky-50 border-sky-200 text-sky-800',
        dot: 'bg-sky-500',
        label: 'LinkedIn'
      };
    case 'Kariyer.net':
      return {
        pill: 'bg-purple-50 border-purple-200 text-purple-800',
        dot: 'bg-purple-500',
        label: 'Kariyer.net'
      };
    case 'Bionluk':
      return {
        pill: 'bg-amber-50 border-amber-200 text-amber-800',
        dot: 'bg-amber-500',
        label: 'Bionluk'
      };
    case 'Harita':
    default:
      return {
        pill: 'bg-emerald-50 border-emerald-200 text-emerald-800',
        dot: 'bg-emerald-500',
        label: 'Yerel İşletme'
      };
  }
}

function renderGrid() {
  const container = document.getElementById('leads-grid');
  const leads = engine.getFilteredLeads();
  const selectedLead = engine.getSelectedLead();

  if (leads.length === 0) {
    container.innerHTML = `
      <div class="h-64 flex flex-col items-center justify-center text-center p-6 border border-dashed border-borderStrong rounded-xl bg-white shadow-xs">
        <p class="text-xs text-fg-muted mb-2 font-medium">Bu filtre kriterine uygun açık fırsat bulunamadı.</p>
        <button id="reset-filter-btn" class="text-xs font-semibold text-zinc-900 bg-canvas hover:bg-canvasSubtle px-3 py-1.5 rounded-lg border border-borderSubtle transition-all active:scale-[0.98]">
          Filtreleri Temizle
        </button>
      </div>
    `;
    const resetBtn = document.getElementById('reset-filter-btn');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        engine.filters.source = 'all';
        engine.filters.type = 'all';
        engine.filters.sector = 'all';
        engine.filters.search = '';
        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.value = '';
        render();
      });
    }
    return;
  }

  container.innerHTML = leads.map(lead => {
    const isSelected = selectedLead && selectedLead.id === lead.id;
    const style = getSourceStyle(lead.source);
    const cleanProblem = lead.design_flaws && lead.design_flaws[0]
      ? lead.design_flaws[0].replace(/^(Kaynak|Kapsam):\s*/i, '')
      : 'Görsel iletişim ve tasarım revizyonu ihtiyacı.';

    const safeId = escapeHtml(lead.id);
    const safeDistrict = escapeHtml(lead.location?.district || '');
    const safeNeedScore = Number(lead.need_score) || 0;
    const safeSector = escapeHtml(lead.sector || '');
    const safeName = escapeHtml(lead.name || '');
    const safeProblem = escapeHtml(cleanProblem);

    return `
      <div 
        data-id="${safeId}" 
        class="conversion-card group cursor-pointer ${isSelected ? 'conversion-card-selected' : ''} rounded-xl p-3.5 sm:p-4 flex flex-col gap-2.5 relative"
      >
        <!-- Üst Bar: Kaynak, Lokasyon ve İhtiyaç Skoru -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-1.5">
            <span class="text-[11px] font-sans font-semibold px-2 py-0.5 rounded-md border ${style.pill} flex items-center gap-1.5 tracking-tight">
              <span class="w-1.5 h-1.5 rounded-full ${style.dot}"></span>
              ${escapeHtml(style.label)}
            </span>
            <span class="text-[11px] text-fg-faint truncate max-w-[140px] font-medium">
              ${safeDistrict}
            </span>
          </div>

          <!-- Yüksek Dönüşüm Skoru (Sağa Yaslı Tabular Rakam) -->
          <div class="flex items-center gap-1 text-[11px] font-sans tabular-nums text-right shrink-0">
            <span class="${safeNeedScore >= 95 ? 'text-amber-600 font-bold' : 'text-zinc-700 font-semibold'}">
              %${safeNeedScore}
            </span>
            <span class="text-[10px] text-fg-faint font-medium">İhtiyaç</span>
          </div>
        </div>

        <!-- Başlık ve Firma -->
        <div>
          <div class="text-[10px] font-sans font-semibold uppercase tracking-wider text-fg-faint mb-0.5">${safeSector}</div>
          <h3 class="font-bold text-xs sm:text-sm text-zinc-900 tracking-tight leading-snug group-hover:text-black line-clamp-1">
            ${safeName}
          </h3>
        </div>

        <!-- Problem / Tespit Edilen Açık (Gestalt Yakınlık - Açık Gri Zemin) -->
        <div class="text-[11px] text-fg-muted leading-relaxed line-clamp-2 bg-canvasSubtle/70 border border-borderSubtle rounded-lg p-2 font-normal">
          ${safeProblem}
        </div>

        <!-- Alt Bar: Hizmet Etiketleri ve Seçim Durumu -->
        <div class="flex items-center justify-between gap-2 pt-1 border-t border-borderSubtle text-[10px]">
          <div class="flex items-center gap-1 overflow-hidden">
            ${(lead.needed_services || []).slice(0, 2).map(svc => `
              <span class="font-sans font-medium bg-canvas border border-borderSubtle text-fg-muted px-2 py-0.5 rounded truncate">
                ${escapeHtml(svc)}
              </span>
            `).join('')}
            ${(lead.needed_services || []).length > 2 ? `<span class="font-sans text-fg-faint font-medium">+${(lead.needed_services || []).length - 2}</span>` : ''}
          </div>

          <span class="font-sans font-medium text-[10px] text-fg-faint flex items-center gap-1 group-hover:text-zinc-900 transition-colors shrink-0">
            <span>İncele</span>
            <span>→</span>
          </span>
        </div>
      </div>
    `;
  }).join('');

  // Tıklama Olayları
  container.querySelectorAll('.conversion-card').forEach(card => {
    card.addEventListener('click', () => {
      const id = card.dataset.id;
      engine.selectLead(id);
      renderGrid();
      renderDetail();

      // Mobilde sağ paneli tam ekran aç
      const panel = document.getElementById('detail-panel');
      if (window.innerWidth < 1024) {
        panel.classList.remove('hidden');
        panel.classList.add('fixed', 'inset-0', 'z-50', 'flex');
      } else {
        panel.classList.remove('hidden', 'fixed', 'inset-0', 'z-50');
      }
    });
  });
}

function generateConversionPitch(lead) {
  const isJob = lead.type === 'job_listing';
  const name = lead.name;
  const services = lead.needed_services.slice(0, 2).join(' ve ');

  if (isJob) {
    return `Sayın Yetkili,

${name} için yayınlanan görsel tasarım pozisyonunuzu inceledim. Özellikle ${services} ihtiyaçlarınız kapsamında, geçmişte benzer sektörlerde ürettiğim güncel stüdyo çalışmalarımı portfolyomda görebilirsiniz:

🔗 [Portfolyo Linkiniz]

Pozisyon kapsamındaki hedeflerinize yönelik kısa bir değerlendirme görüşmesi planlamaktan memnuniyet duyarım.

Saygılarımla,
[Adınız Soyadınız]`;
  } else {
    return `Merhaba ${name} Ekibi,

${lead.location.district} şubenizi ve dijital varlığınızı inceledim. ${services} konularında müşteri temasınızı doğrudan artıracak modern ve kurumsal bir görsel kimlik desteği sunabilirim.

Mevcut düzeniniz üzerinden hazırladığım 1 sayfalık ücretsiz örnek tasarım taslağını değerlendirmeniz için iletmek isterim. Uygun olduğunuzda paylaşabilir miyim?

Teşekkürler,
[Adınız Soyadınız]`;
  }
}

function renderDetail() {
  const panel = document.getElementById('detail-panel');
  const lead = engine.getSelectedLead();

  if (!lead) {
    const visibleLeads = engine.getFilteredLeads();
    panel.innerHTML = `
      <div class="h-full flex flex-col items-center justify-center text-center p-8 text-fg-faint text-xs gap-3">
        <div class="w-10 h-10 rounded-xl bg-canvas border border-borderSubtle flex items-center justify-center text-fg-muted">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"></path></svg>
        </div>
        <div>
          <p class="font-semibold text-zinc-900 text-sm">Hedef İnceleme Kokpiti</p>
          <p class="text-[11px] text-fg-faint mt-1 max-w-xs">Listeden bir açık ilan veya müşteri fırsatı seçerek teklif taslağını ve başvuru detaylarını görüntüleyin.</p>
        </div>
        ${visibleLeads.length > 0 ? `
          <button id="select-first-lead-btn" class="mt-2 text-xs font-semibold px-4 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white transition-all active:scale-[0.98] shadow-sm">
            İlk Fırsatı İncele →
          </button>
        ` : ''}
      </div>
    `;

    const firstBtn = document.getElementById('select-first-lead-btn');
    if (firstBtn && visibleLeads.length > 0) {
      firstBtn.addEventListener('click', () => {
        engine.selectLead(visibleLeads[0].id);
        renderGrid();
        renderDetail();
      });
    }
    return;
  }

  const isJob = lead.type === 'job_listing';
  const style = getSourceStyle(lead.source);
  const pitchText = generateConversionPitch(lead);
  const rawDirectUrl = lead.contact?.website || lead.contact?.map_url || '#';
  const directUrl = sanitizeUrl(rawDirectUrl);

  const safeName = escapeHtml(lead.name || '');
  const safeSector = escapeHtml(lead.sector || '');
  const safeCity = escapeHtml(lead.location?.city || '');
  const safeDistrict = escapeHtml(lead.location?.district || '');
  const safeWorkType = escapeHtml(lead.work_type || '');
  const safeNeedScore = Number(lead.need_score) || 0;
  const safeNotes = escapeHtml(lead.notes || '');
  const safePitchText = escapeHtml(pitchText || '');

  // VIEWPORT BAŞINA TEK PRIMARY CTA KURALI (Figma / Notion Light Studio Clean)
  // Ana Aksiyon Butonu: Net, yüksek kontrastlı siyah buton (#111827 / bg-zinc-900 hover:bg-zinc-800 text-white)
  let primaryCtaTitle = 'İlana Doğrudan Başvur ↗';
  let primaryCtaSub = 'Doğrulanmış kaynak • Aracı komisyonu yok';

  if (lead.source === 'LinkedIn') {
    primaryCtaTitle = 'LinkedIn İlanına Doğrudan Başvur ↗';
    primaryCtaSub = 'Doğrulanmış tekil iş ilanı • Doğrudan şirket başvuru sayfası';
  } else if (lead.source === 'Kariyer.net') {
    primaryCtaTitle = 'Kariyer.net İlan Listesini Aç ↗';
    primaryCtaSub = 'İstanbul grafik tasarım arama listesi • Güncel açık ilanlar';
  } else if (lead.source === 'Harita') {
    primaryCtaTitle = 'Google Haritalar Profilini Aç ↗';
    primaryCtaSub = 'İşletme lokasyonu • Doğrudan iletişim ve menü incelemesi';
  } else if (lead.source === 'Bionluk') {
    primaryCtaTitle = 'Bionluk Kategori Taleplerini Aç ↗';
    primaryCtaSub = 'Bionluk grafik & kimlik tasarım pazarı sayfası';
  }

  // İkincil Hayalet Aksiyonlar (Ghost Action Buttons: border border-gray-300 bg-white text-gray-700)
  let secondaryActionsHtml = '';
  if (lead.contact?.phone) {
    const cleanPhone = encodeURIComponent(String(lead.contact.phone).replace(/[^0-9+]/g, ''));
    secondaryActionsHtml += `
      <a 
        href="https://wa.me/${cleanPhone}" 
        target="_blank" 
        rel="noopener noreferrer"
        class="flex-1 py-2 px-3 rounded-lg border border-gray-300 hover:border-gray-400 bg-white hover:bg-gray-50 text-xs text-gray-700 hover:text-gray-900 transition-all text-center flex items-center justify-center gap-1.5 shadow-xs"
      >
        <svg class="w-3.5 h-3.5 text-emerald-600" fill="currentColor" viewBox="0 0 24 24"><path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.582 2.128 2.182-.573c.978.58 1.911.928 3.145.929 3.178 0 5.767-2.587 5.768-5.766.001-3.187-2.575-5.77-5.764-5.771zm3.392 8.244c-.144.405-.837.774-1.17.824-.312.045-.694.072-2.123-.521-1.637-.678-2.684-2.348-2.766-2.457-.082-.11-1.04-1.385-1.04-2.64 0-1.256.657-1.874.89-2.128.233-.254.512-.318.683-.318.17 0 .341.002.49.009.157.007.368-.059.575.438.213.513.727 1.77.791 1.901.063.131.106.284.021.454-.085.17-.128.276-.255.424-.127.148-.266.331-.38.444-.128.127-.261.265-.112.521.149.255.663 1.093 1.422 1.769.977.872 1.8 1.142 2.056 1.27.256.127.405.106.554-.064.149-.17.639-.744.81-1.001.17-.255.341-.212.575-.127.234.085 1.489.702 1.745.83.255.127.426.191.49.297.064.106.064.616-.08 1.021z"/></svg>
        WhatsApp
      </a>
    `;
  }
  if (lead.contact?.website) {
    const safeWebUrl = sanitizeUrl(lead.contact.website);
    secondaryActionsHtml += `
      <a 
        href="${safeWebUrl}" 
        target="_blank" 
        rel="noopener noreferrer"
        class="flex-1 py-2 px-3 rounded-lg border border-gray-300 hover:border-gray-400 bg-white hover:bg-gray-50 text-xs text-gray-700 hover:text-gray-900 transition-all text-center flex items-center justify-center gap-1.5 shadow-xs"
      >
        <svg class="w-3.5 h-3.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
        Web Sitesi
      </a>
    `;
  }
  if (lead.contact?.email) {
    const safeEmail = encodeURIComponent(String(lead.contact.email).trim());
    secondaryActionsHtml += `
      <a 
        href="mailto:${safeEmail}" 
        class="flex-1 py-2 px-3 rounded-lg border border-gray-300 hover:border-gray-400 bg-white hover:bg-gray-50 text-xs text-gray-700 hover:text-gray-900 transition-all text-center flex items-center justify-center gap-1.5 shadow-xs"
      >
        <svg class="w-3.5 h-3.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
        E-posta
      </a>
    `;
  }

  panel.innerHTML = `
    <!-- Kokpit Üst Barı: Başlık, Lokasyon, Mobil Kapatma -->
    <div class="p-4 sm:p-5 border-b border-borderSubtle flex flex-col gap-3 bg-white">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="text-[11px] font-sans font-semibold px-2 py-0.5 rounded border ${style.pill} flex items-center gap-1.5 tracking-tight">
            <span class="w-1.5 h-1.5 rounded-full ${style.dot}"></span>
            ${escapeHtml(style.label)}
          </span>
          <span class="text-xs font-sans font-bold text-amber-600 tabular-data">%${safeNeedScore} İhtiyaç</span>
        </div>
        <button id="close-drawer-btn" class="lg:hidden p-1.5 rounded-lg border border-borderSubtle bg-canvas text-fg-muted hover:text-zinc-900 text-xs font-medium">
          ✕ Kapat
        </button>
      </div>

      <div>
        <div class="text-[10px] font-sans font-semibold uppercase tracking-wider text-fg-faint mb-1">${safeSector}</div>
        <h2 class="font-bold text-base sm:text-lg text-zinc-900 tracking-tight leading-snug">${safeName}</h2>
        <div class="text-xs text-fg-muted mt-1 flex items-center gap-2">
          <span>${safeCity}, ${safeDistrict}</span>
          <span>•</span>
          <span class="font-sans text-fg-faint text-[11px] font-medium">${safeWorkType}</span>
        </div>
      </div>

      <!-- VIEWPORT BAŞINA TEK PRIMARY CTA KURALI (Odaklanmış Koyu Stüdyo Butonu) -->
      <div class="pt-1 flex flex-col">
        <a 
          href="${directUrl}" 
          target="_blank" 
          rel="noopener noreferrer"
          class="w-full py-3 px-4 rounded-xl font-bold text-xs sm:text-sm bg-zinc-900 hover:bg-zinc-800 text-white flex items-center justify-between transition-all duration-150 active:scale-[0.98] shadow-sm"
        >
          <span>${escapeHtml(primaryCtaTitle)}</span>
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
        </a>

        <!-- RİSK TERSİNE ÇEVİRME (Mikro güvence kopyası) -->
        <span class="text-[10px] text-fg-faint text-center mt-2 font-sans font-medium">
          ${escapeHtml(primaryCtaSub)}
        </span>
      </div>

      <!-- İkincil Eylemler (Ghost Butonlar) -->
      ${secondaryActionsHtml ? `
        <div class="flex items-center gap-2 pt-1">
          ${secondaryActionsHtml}
        </div>
      ` : ''}
    </div>

    <!-- DÖNÜŞÜM İÇERİK BÖLÜMÜ -->
    <div class="p-4 sm:p-5 flex flex-col gap-4 bg-white">

      <!-- Problem ➔ Çözüm Değer Matrisi -->
      <div>
        <div class="text-[10px] font-semibold text-fg-faint uppercase tracking-wider mb-2 font-sans">
          ${isJob ? 'İlan Kapsamı & Şartlar' : 'Problem & Değer Eşleşmesi'}
        </div>
        <div class="bg-canvas border border-borderSubtle rounded-xl p-3 flex flex-col gap-2.5">
          ${(lead.design_flaws || []).map(flaw => `
            <div class="flex items-start gap-2.5 text-xs text-fg-muted leading-relaxed">
              <span class="text-amber-500 font-bold shrink-0 mt-0.5">•</span>
              <span>${escapeHtml(flaw)}</span>
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Sunulacak Hizmet Paketi -->
      <div>
        <div class="text-[10px] font-semibold text-fg-faint uppercase tracking-wider mb-2 font-sans">Önerilen Hizmet Paketi</div>
        <div class="flex flex-wrap gap-1.5">
          ${(lead.needed_services || []).map(svc => `
            <span class="text-xs bg-canvas border border-borderSubtle text-zinc-800 px-2.5 py-1 rounded-lg font-sans font-medium">
              ${escapeHtml(svc)}
            </span>
          `).join('')}
        </div>
      </div>

      <!-- HAZIR TEKLİF & PITCH MİMARİSİ (Sürtünmesiz Tek Tık Dönüşüm) -->
      <div class="border-t border-borderSubtle pt-4 flex flex-col gap-2">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-bold text-zinc-900">Doğrudan Teklif & Outreach Taslağı</span>
          <span class="text-[10px] text-emerald-600 font-sans font-semibold">Kullanıma Hazır</span>
        </div>
        <p class="text-[10px] text-fg-faint leading-relaxed">
          Yapay zeka klişelerinden arındırılmış, doğrudan sonuca odaklı profesyonel temas mesajı:
        </p>
        <div class="relative mt-1">
          <textarea 
            id="pitch-textarea" 
            readonly
            class="w-full h-36 bg-canvas border border-borderSubtle rounded-xl p-3 text-xs text-zinc-700 font-sans leading-relaxed resize-none focus:outline-none"
          >${safePitchText}</textarea>
          <button 
            id="copy-pitch-btn" 
            class="absolute bottom-3 right-3 px-3 py-1.5 rounded-lg bg-white hover:bg-gray-50 text-zinc-800 border border-gray-300 hover:border-gray-400 font-medium text-xs flex items-center gap-1.5 transition-all active:scale-[0.98] shadow-xs"
          >
            <svg class="w-3.5 h-3.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg>
            <span id="copy-btn-text">Teklifi Kopyala</span>
          </button>
        </div>
      </div>

      <!-- Özel Tasarımcı Notu (Form Sürtünmesizliği: Otomatik onBlur Kaydetme) -->
      <div class="border-t border-borderSubtle pt-3 flex flex-col gap-1.5">
        <div class="flex items-center justify-between">
          <label class="text-[11px] font-medium text-fg-faint font-sans">Özel Tasarımcı Notun:</label>
          <span id="notes-saved-hint" class="text-[10px] text-emerald-600 font-sans font-semibold transition-opacity duration-200 opacity-0">Kaydedildi ✓</span>
        </div>
        <textarea 
          id="lead-notes-area"
          placeholder="Örn: Portfolyo linkiyle iletişime geçildi, teklif bekleniyor..."
          class="w-full h-16 bg-canvas border border-borderSubtle rounded-xl p-2.5 text-xs text-zinc-900 placeholder-fg-faint focus:outline-none focus:bg-white focus:border-zinc-400 resize-none transition-colors"
        >${safeNotes}</textarea>
        <span class="text-[10px] text-fg-faint">Yazıp çıktığınızda otomatik kaydedilir.</span>
      </div>

    </div>
  `;

  // Kopyalama Butonu
  const copyBtn = document.getElementById('copy-pitch-btn');
  if (copyBtn) {
    copyBtn.addEventListener('click', async () => {
      const textarea = document.getElementById('pitch-textarea');
      if (textarea) {
        try {
          await navigator.clipboard.writeText(textarea.value);
          const btnText = document.getElementById('copy-btn-text');
          if (btnText) btnText.textContent = 'Kopyalandı! ✓';
          setTimeout(() => {
            if (btnText) btnText.textContent = 'Teklifi Kopyala';
          }, 2000);
        } catch (e) {
          textarea.select();
          document.execCommand('copy');
        }
      }
    });
  }

  // Not Otomatik Kaydetme (onBlur)
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

  // Mobil Kapat Butonu
  const closeBtn = document.getElementById('close-drawer-btn');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      panel.classList.add('hidden');
      panel.classList.remove('fixed', 'inset-0', 'z-50', 'flex');
    });
  }
}

// -----------------------------------------------------------------------------
// Bağlantı ve Sunucu Ayarları Modalı (Mobil APK & GitHub Ayrımı)
// -----------------------------------------------------------------------------
const openSettingsBtn = document.getElementById('open-settings-btn');
const closeSettingsBtn = document.getElementById('close-settings-btn');
const settingsModal = document.getElementById('settings-modal');
const serverUrlInput = document.getElementById('server-url-input');
const secretTokenInput = document.getElementById('secret-token-input');
const saveSettingsBtn = document.getElementById('save-settings-btn');
const resetSettingsBtn = document.getElementById('reset-settings-btn');

if (openSettingsBtn && settingsModal) {
  openSettingsBtn.addEventListener('click', () => {
    if (serverUrlInput) serverUrlInput.value = engine.getServerUrl();
    if (secretTokenInput) secretTokenInput.value = engine.getSecretToken();
    settingsModal.classList.remove('hidden');
    settingsModal.classList.add('flex');
  });

  const closeModal = () => {
    settingsModal.classList.add('hidden');
    settingsModal.classList.remove('flex');
  };

  if (closeSettingsBtn) closeSettingsBtn.addEventListener('click', closeModal);
  settingsModal.addEventListener('click', (e) => {
    if (e.target === settingsModal) closeModal();
  });

  if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener('click', () => {
      if (serverUrlInput) engine.setServerUrl(serverUrlInput.value);
      if (secretTokenInput) engine.setSecretToken(secretTokenInput.value);
      closeModal();
      window.location.reload();
    });
  }

  if (resetSettingsBtn) {
    resetSettingsBtn.addEventListener('click', () => {
      if (serverUrlInput) serverUrlInput.value = '';
      if (secretTokenInput) secretTokenInput.value = '';
      engine.setServerUrl('');
      engine.setSecretToken('');
      closeModal();
      window.location.reload();
    });
  }
}

// Başlat
window.addEventListener('DOMContentLoaded', init);
