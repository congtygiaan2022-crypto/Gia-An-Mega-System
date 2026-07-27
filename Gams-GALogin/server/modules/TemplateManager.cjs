const fs = require('fs');
const path = require('path');

class TemplateManager {
  constructor(dbPath) {
    this.dbPath = dbPath || path.join(__dirname, '..', '..', 'templates.json');
    this.seedDefaultTemplates();
  }

  seedDefaultTemplates() {
    if (!fs.existsSync(this.dbPath)) {
      const defaults = [
        {
          id: 'temp-default',
          name: 'Template Tiêu Chuẩn (Windows)',
          browserType: 'chromium',
          windowSize: { width: 1440, height: 900, x: 50, y: 50 },
          language: 'vi-VN',
          timezone: 'Asia/Ho_Chi_Minh',
          proxyConfig: { type: 'Direct', host: '', port: '', username: '', password: '', pacUrl: '' },
          userAgentPolicy: 'Random',
          startupConfig: { mode: 'blank', urls: [] },
          extensions: [],
          browserArguments: ['--no-first-run', '--no-default-browser-check', '--disable-notifications']
        },
        {
          id: 'temp-mac-us',
          name: 'Template US Agency (macOS)',
          browserType: 'chrome',
          windowSize: { width: 1536, height: 864, x: 100, y: 100 },
          language: 'en-US',
          timezone: 'America/New_York',
          proxyConfig: { type: 'Direct', host: '', port: '', username: '', password: '', pacUrl: '' },
          userAgentPolicy: 'Random',
          startupConfig: { mode: 'urls', urls: ['https://whoer.net', 'https://google.com'] },
          extensions: [],
          browserArguments: ['--no-first-run', '--no-default-browser-check', '--incognito']
        }
      ];
      fs.writeFileSync(this.dbPath, JSON.stringify(defaults, null, 2), 'utf8');
    }
  }

  loadTemplates() {
    try {
      if (fs.existsSync(this.dbPath)) {
        return JSON.parse(fs.readFileSync(this.dbPath, 'utf8'));
      }
    } catch (e) {
      console.error('Error loading Templates:', e.message);
    }
    return [];
  }

  saveTemplates(list) {
    try {
      fs.writeFileSync(this.dbPath, JSON.stringify(list, null, 2), 'utf8');
      return true;
    } catch (e) {
      return false;
    }
  }

  createTemplate(data) {
    const list = this.loadTemplates();
    const id = `temp-${Date.now()}`;
    const newTemp = {
      id,
      name: data.name || `Template ${id}`,
      browserType: data.browserType || 'chromium',
      windowSize: data.windowSize || { width: 1280, height: 720, x: 50, y: 50 },
      language: data.language || 'vi-VN',
      timezone: data.timezone || 'Asia/Ho_Chi_Minh',
      proxyConfig: data.proxyConfig || { type: 'Direct', host: '', port: '', username: '', password: '', pacUrl: '' },
      userAgentPolicy: data.userAgentPolicy || 'Random',
      startupConfig: data.startupConfig || { mode: 'blank', urls: [] },
      extensions: data.extensions || [],
      browserArguments: data.browserArguments || []
    };
    list.push(newTemp);
    this.saveTemplates(list);
    return newTemp;
  }

  updateTemplate(id, updates) {
    const list = this.loadTemplates();
    const idx = list.findIndex(t => t.id === id);
    if (idx === -1) return null;
    list[idx] = { ...list[idx], ...updates };
    this.saveTemplates(list);
    return list[idx];
  }

  deleteTemplate(id) {
    const list = this.loadTemplates();
    const filtered = list.filter(t => t.id !== id);
    this.saveTemplates(filtered);
    return list.length !== filtered.length;
  }
}

module.exports = TemplateManager;
