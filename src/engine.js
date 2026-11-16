/**
 * Tasarımcı Müşteri Radarı — Veri ve Filtreleme Motoru v3
 */

export class LeadEngine {
  constructor(initialData = []) {
    this.storageKey = 'design_radar_leads_v4';
    this.serverUrlKey = 'design_radar_server_url';
    this.secretTokenKey = 'design_radar_secret_token';
    this.leads = this.loadFromStorage(initialData);
    this.selectedLeadId = this.leads.length > 0 ? this.leads[0].id : null;
    this.filters = {
      search: '',
      source: 'all', // 'all', 'LinkedIn', 'Kariyer.net', 'Bionluk', 'Harita'
      type: 'all',   // 'all', 'opportunity', 'job_listing'
      city: 'all',
      sector: 'all',
      workType: 'all',
      sortBy: 'need_score' // 'need_score', 'name'
    };
  }

  getServerUrl() {
    try {
      const saved = localStorage.getItem(this.serverUrlKey);
      if (saved && saved.trim()) return saved.trim().replace(/\/+$/, '');
    } catch (e) {}
    return '';
  }

  setServerUrl(url) {
    try {
      if (url && url.trim()) {
        localStorage.setItem(this.serverUrlKey, url.trim().replace(/\/+$/, ''));
      } else {
        localStorage.removeItem(this.serverUrlKey);
      }
    } catch (e) {}
  }

  getSecretToken() {
    try {
      return localStorage.getItem(this.secretTokenKey) || '';
    } catch (e) {
      return '';
    }
  }

  setSecretToken(token) {
    try {
      if (token && token.trim()) {
        localStorage.setItem(this.secretTokenKey, token.trim());
      } else {
        localStorage.removeItem(this.secretTokenKey);
      }
    } catch (e) {}
  }

  loadFromStorage(initialData) {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].source) {
          return parsed;
        }
      }
    } catch (e) {
      console.warn('LocalStorage okunamadı, varsayılan veri kullanılıyor.', e);
    }
    return [...initialData];
  }

  saveToStorage() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.leads));
    } catch (e) {
      console.error('LocalStorage kaydetme hatası:', e);
    }
  }

  setFilter(key, value) {
    if (this.filters.hasOwnProperty(key)) {
      this.filters[key] = value;
    }
  }

  getFilteredLeads() {
    return this.leads.filter(lead => {
      // Metin araması
      if (this.filters.search.trim()) {
        const query = this.filters.search.toLowerCase();
        const matchName = lead.name.toLowerCase().includes(query);
        const matchSector = lead.sector.toLowerCase().includes(query);
        const matchCity = lead.location?.city?.toLowerCase().includes(query);
        const matchDistrict = lead.location?.district?.toLowerCase().includes(query);
        if (!matchName && !matchSector && !matchCity && !matchDistrict) {
          return false;
        }
      }

      // Kaynak Filtresi (LinkedIn, Kariyer.net, Bionluk, Harita)
      if (this.filters.source && this.filters.source !== 'all') {
        if (lead.source !== this.filters.source) {
          return false;
        }
      }

      // Tür Filtresi (Fırsat vs İlan)
      if (this.filters.type !== 'all' && lead.type !== this.filters.type) {
        return false;
      }

      // Şehir Filtresi
      if (this.filters.city !== 'all' && lead.location?.city !== this.filters.city) {
        return false;
      }

      // Sektör Filtresi
      if (this.filters.sector !== 'all' && !lead.sector.includes(this.filters.sector)) {
        return false;
      }

      // Çalışma Tipi (Remote, Hibrit vb.)
      if (this.filters.workType !== 'all') {
        const isRemote = lead.work_type.toLowerCase().includes('uzaktan') || lead.work_type.toLowerCase().includes('remote');
        if (this.filters.workType === 'remote' && !isRemote) return false;
        if (this.filters.workType === 'local' && isRemote) return false;
      }

      return true;
    }).sort((a, b) => {
      if (this.filters.sortBy === 'need_score') {
        return b.need_score - a.need_score;
      }
      return a.name.localeCompare(b.name, 'tr');
    });
  }

  getSourceCounts() {
    const counts = { all: this.leads.length, 'LinkedIn': 0, 'Kariyer.net': 0, 'Bionluk': 0, 'Harita': 0 };
    this.leads.forEach(l => {
      if (counts[l.source] !== undefined) {
        counts[l.source]++;
      }
    });
    return counts;
  }

  getSelectedLead() {
    return this.leads.find(l => l.id === this.selectedLeadId) || this.leads[0] || null;
  }

  selectLead(id) {
    this.selectedLeadId = id;
  }

  updateLeadStatus(id, newStatus) {
    const lead = this.leads.find(l => l.id === id);
    if (lead) {
      lead.status = newStatus;
      this.saveToStorage();
    }
  }

  updateLeadNotes(id, notes) {
    const lead = this.leads.find(l => l.id === id);
    if (lead) {
      lead.notes = notes;
      this.saveToStorage();
    }
  }

  getCities() {
    const cities = new Set(this.leads.map(l => l.location?.city).filter(Boolean));
    return Array.from(cities);
  }

  getSectors() {
    const sectors = new Set(this.leads.map(l => l.sector.split('/')[0].trim()).filter(Boolean));
    return Array.from(sectors);
  }
}
