const fs = require('fs');
const path = require('path');

class ProfileManager {
  constructor(dbPath, profilesDir) {
    this.dbPath = dbPath || path.join(__dirname, '..', '..', 'profiles.json');
    this.profilesDir = profilesDir || path.join(__dirname, '..', '..', 'bin', 'profiles');
    this.ensureDirectoryExists(this.profilesDir);
  }

  ensureDirectoryExists(dir) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  getDefaultProfile(id = `p-${Date.now()}`) {
    return {
      id,
      name: `Profile ${id}`,
      browserType: 'chromium',
      executablePath: '',
      userDataDir: path.join(this.profilesDir, id),
      proxyConfig: {
        type: 'Direct',
        host: '',
        port: '',
        username: '',
        password: '',
        pacUrl: ''
      },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
      windowSize: {
        width: 1280,
        height: 720,
        x: 50,
        y: 50
      },
      language: 'vi-VN',
      timezone: 'Asia/Ho_Chi_Minh',
      startupConfig: {
        mode: 'blank',
        urls: []
      },
      downloadDir: '',
      extensions: [],
      notes: '',
      group: 'Facebook Ads',
      browserArguments: [
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-notifications'
      ],
      lastOpened: 'Chưa sử dụng',
      port: null
    };
  }

  loadProfiles() {
    let profiles = [];
    if (fs.existsSync(this.dbPath)) {
      try {
        const raw = fs.readFileSync(this.dbPath, 'utf8');
        profiles = JSON.parse(raw);
      } catch (err) {
        console.error('Error loading profiles database:', err);
        profiles = [];
      }
    }

    // Schema validation and upgrade
    let updated = false;
    const validatedProfiles = profiles.map(p => {
      const defaultP = this.getDefaultProfile(p.id);
      
      // Deep merge basic props
      const merged = { ...defaultP, ...p };
      
      // Deep merge nested proxyConfig
      if (p.proxyConfig) {
        merged.proxyConfig = { ...defaultP.proxyConfig, ...p.proxyConfig };
      } else if (p.proxy && p.proxy !== 'No Proxy (Direct)') {
        // Migration from old flat proxy string (e.g. host:port or host:port:user:pass)
        const parts = p.proxy.split(':');
        const host = parts[0] || '';
        const port = parts[1] || '';
        const username = parts[2] || '';
        const password = parts[3] || '';
        merged.proxyConfig = {
          type: 'HTTP',
          host,
          port,
          username,
          password,
          pacUrl: ''
        };
        updated = true;
      }

      // Deep merge nested startupConfig
      if (p.startupConfig) {
        merged.startupConfig = { ...defaultP.startupConfig, ...p.startupConfig };
      } else if (p.startupUrl) {
        merged.startupConfig = {
          mode: 'urls',
          urls: [p.startupUrl]
        };
        updated = true;
      }

      // Deep merge windowSize
      if (p.windowSize) {
        merged.windowSize = { ...defaultP.windowSize, ...p.windowSize };
      }

      // Assign debug port if missing
      if (!merged.port) {
        const existingPorts = profiles.map(x => x.port).filter(Boolean);
        let candidate = 15001;
        while (existingPorts.includes(candidate)) {
          candidate++;
        }
        merged.port = candidate;
        updated = true;
      }

      return merged;
    });

    if (updated || !fs.existsSync(this.dbPath)) {
      this.saveProfiles(validatedProfiles);
    }

    return validatedProfiles;
  }

  saveProfiles(profiles) {
    try {
      fs.writeFileSync(this.dbPath, JSON.stringify(profiles, null, 2), 'utf8');
      return true;
    } catch (err) {
      console.error('Error saving profiles database:', err);
      return false;
    }
  }

  getProfile(id) {
    const profiles = this.loadProfiles();
    return profiles.find(p => p.id === id) || null;
  }

  createProfile(data) {
    const profiles = this.loadProfiles();
    const id = `p-${Date.now()}`;
    const newProfile = {
      ...this.getDefaultProfile(id),
      ...data,
      id // Ensure ID remains immutable on creation
    };

    // Calculate unique port
    const usedPorts = new Set(profiles.map(p => p.port).filter(Boolean));
    let nextPort = 15001;
    while (usedPorts.has(nextPort)) {
      nextPort++;
    }
    newProfile.port = nextPort;

    // Ensure userDataDir exists
    this.ensureDirectoryExists(newProfile.userDataDir);

    profiles.unshift(newProfile);
    this.saveProfiles(profiles);
    return newProfile;
  }

  updateProfile(id, updates) {
    const profiles = this.loadProfiles();
    const idx = profiles.findIndex(p => p.id === id);
    if (idx === -1) return null;

    // Prevent overwriting structural values unless intended
    const current = profiles[idx];
    
    // Deep merge updates
    const merged = { ...current, ...updates };
    if (updates.proxyConfig) {
      merged.proxyConfig = { ...current.proxyConfig, ...updates.proxyConfig };
    }
    if (updates.startupConfig) {
      merged.startupConfig = { ...current.startupConfig, ...updates.startupConfig };
    }
    if (updates.windowSize) {
      merged.windowSize = { ...current.windowSize, ...updates.windowSize };
    }

    profiles[idx] = merged;
    this.saveProfiles(profiles);
    return merged;
  }

  deleteProfile(id) {
    const profiles = this.loadProfiles();
    const filtered = profiles.filter(p => p.id !== id);
    const deleted = profiles.length !== filtered.length;
    
    if (deleted) {
      this.saveProfiles(filtered);
    }
    return deleted;
  }

  cloneProfile(id, suffix = 'Bản sao') {
    const source = this.getProfile(id);
    if (!source) return null;

    const cloneData = {
      ...source,
      name: `${source.name} (${suffix})`,
      lastOpened: 'Chưa sử dụng'
    };
    
    // Create new profile with a brand new ID
    return this.createProfile(cloneData);
  }
}

module.exports = ProfileManager;
