const fs = require('fs');
const path = require('path');

class UserAgentManager {
  constructor(dbPath) {
    this.dbPath = dbPath || path.join(__dirname, '..', '..', 'user_agents.json');
    this.currentIndex = 0;
    this.seedDefaultUserAgents();
  }

  seedDefaultUserAgents() {
    if (!fs.existsSync(this.dbPath)) {
      const defaults = [
        { id: 'ua-1', ua: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36', platform: 'Windows' },
        { id: 'ua-2', ua: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36', platform: 'Windows' },
        { id: 'ua-3', ua: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36', platform: 'macOS' },
        { id: 'ua-4', ua: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36', platform: 'macOS' },
        { id: 'ua-5', ua: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36', platform: 'Linux' },
        { id: 'ua-6', ua: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36', platform: 'Linux' }
      ];
      fs.writeFileSync(this.dbPath, JSON.stringify(defaults, null, 2), 'utf8');
    }
  }

  loadUserAgents() {
    try {
      if (fs.existsSync(this.dbPath)) {
        return JSON.parse(fs.readFileSync(this.dbPath, 'utf8'));
      }
    } catch (e) {
      console.error('Error loading User Agents:', e.message);
    }
    return [];
  }

  saveUserAgents(list) {
    try {
      fs.writeFileSync(this.dbPath, JSON.stringify(list, null, 2), 'utf8');
      return true;
    } catch (e) {
      return false;
    }
  }

  addUserAgent(ua, platform = 'Windows') {
    const list = this.loadUserAgents();
    const newUa = {
      id: `ua-${Date.now()}`,
      ua: ua.trim(),
      platform
    };
    list.push(newUa);
    this.saveUserAgents(list);
    return newUa;
  }

  updateUserAgent(id, ua, platform) {
    const list = this.loadUserAgents();
    const idx = list.findIndex(u => u.id === id);
    if (idx === -1) return null;
    list[idx] = { ...list[idx], ua: ua.trim(), platform };
    this.saveUserAgents(list);
    return list[idx];
  }

  deleteUserAgent(id) {
    const list = this.loadUserAgents();
    const filtered = list.filter(u => u.id !== id);
    this.saveUserAgents(filtered);
    return list.length !== filtered.length;
  }

  importTxt(txtContent, platform = 'Windows') {
    const lines = txtContent.split('\n').map(l => l.trim()).filter(Boolean);
    const list = this.loadUserAgents();
    const added = [];
    lines.forEach(line => {
      if (line.startsWith('Mozilla')) {
        const item = {
          id: `ua-${Date.now()}-${Math.floor(Math.random()*1000)}`,
          ua: line,
          platform
        };
        list.push(item);
        added.push(item);
      }
    });
    this.saveUserAgents(list);
    return added.length;
  }

  importJson(jsonContent) {
    try {
      const parsed = typeof jsonContent === 'string' ? JSON.parse(jsonContent) : jsonContent;
      if (!Array.isArray(parsed)) return 0;
      const list = this.loadUserAgents();
      let count = 0;
      parsed.forEach(item => {
        if (item.ua) {
          list.push({
            id: `ua-${Date.now()}-${count++}`,
            ua: item.ua,
            platform: item.platform || 'Windows'
          });
        }
      });
      this.saveUserAgents(list);
      return count;
    } catch (e) {
      return 0;
    }
  }

  exportJson() {
    return JSON.stringify(this.loadUserAgents(), null, 2);
  }

  /**
   * Generates a User Agent based on a policy (Fixed, Random, Sequential)
   */
  generateUserAgent(policy, platform = 'Windows', fixedValue = '') {
    if (policy === 'Fixed') {
      return fixedValue || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36';
    }

    const list = this.loadUserAgents().filter(u => u.platform.toLowerCase() === platform.toLowerCase());
    if (list.length === 0) {
      // Fallback if list is empty
      return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36';
    }

    if (policy === 'Random') {
      const randIdx = Math.floor(Math.random() * list.length);
      return list[randIdx].ua;
    }

    if (policy === 'Sequential') {
      const idx = this.currentIndex % list.length;
      this.currentIndex++;
      return list[idx].ua;
    }

    return list[0].ua;
  }
}

module.exports = UserAgentManager;
