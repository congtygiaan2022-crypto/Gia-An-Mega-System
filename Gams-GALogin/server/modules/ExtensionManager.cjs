const fs = require('fs');
const path = require('path');

class ExtensionManager {
  constructor(extensionsDir) {
    this.extensionsDir = extensionsDir || path.join(__dirname, '..', '..', 'bin', 'extensions');
    this.dbPath = path.join(this.extensionsDir, 'extensions.json');
    this.ensureDirectoryExists(this.extensionsDir);
  }

  ensureDirectoryExists(dir) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  loadGlobalExtensions() {
    if (!fs.existsSync(this.dbPath)) {
      // Seed with empty array
      fs.writeFileSync(this.dbPath, '[]', 'utf8');
      return [];
    }
    try {
      return JSON.parse(fs.readFileSync(this.dbPath, 'utf8'));
    } catch (e) {
      return [];
    }
  }

  saveGlobalExtensions(extensions) {
    try {
      fs.writeFileSync(this.dbPath, JSON.stringify(extensions, null, 2), 'utf8');
      return true;
    } catch (e) {
      return false;
    }
  }

  registerExtension(name, folderPath) {
    const list = this.loadGlobalExtensions();
    const id = `ext-${Date.now()}`;
    const newExt = {
      id,
      name,
      path: folderPath,
      description: 'Custom extension'
    };
    list.push(newExt);
    this.saveGlobalExtensions(list);
    return newExt;
  }

  deleteExtension(id) {
    const list = this.loadGlobalExtensions();
    const filtered = list.filter(e => e.id !== id);
    this.saveGlobalExtensions(filtered);
    return list.length !== filtered.length;
  }

  /**
   * Resolves the list of active extensions for a profile and returns the CLI arguments
   */
  getLoadExtensionArgument(profile, extraExtensionPaths = []) {
    const globalExts = this.loadGlobalExtensions();
    const paths = [];

    // Add profile's enabled extensions
    if (Array.isArray(profile.extensions)) {
      profile.extensions.forEach(ref => {
        if (ref.enabled) {
          // If the profile extension stores its own path, use it. Otherwise, look it up in global list
          let extPath = ref.path;
          if (!extPath) {
            const match = globalExts.find(g => g.id === ref.id);
            if (match) extPath = match.path;
          }

          if (extPath && fs.existsSync(extPath)) {
            paths.push(extPath);
          }
        }
      });
    }

    // Add extra extension paths (e.g. proxy auth extension)
    extraExtensionPaths.forEach(p => {
      if (p && fs.existsSync(p) && !paths.includes(p)) {
        paths.push(p);
      }
    });

    if (paths.length === 0) return [];
    
    // Join with comma for Chrome CLI
    return [`--load-extension=${paths.join(',')}`];
  }
}

module.exports = ExtensionManager;
