const fs = require('fs');
const path = require('path');

class ProxyManager {
  constructor(profilesDir) {
    this.profilesDir = profilesDir || path.join(__dirname, '..', '..', 'bin', 'profiles');
  }

  /**
   * Builds proxy CLI flags and handles credentials via temporary extensions
   * Returns: { args: string[], extensionPath: string | null }
   */
  prepareProxy(profile) {
    const config = profile.proxyConfig;
    if (!config || !config.type || config.type === 'Direct' || config.type === 'No Proxy') {
      return { args: [], extensionPath: null };
    }

    const args = [];
    let extensionPath = null;

    if (config.type === 'PAC') {
      if (config.pacUrl) {
        args.push(`--proxy-pac-url=${config.pacUrl}`);
      }
      return { args, extensionPath };
    }

    // Standard proxy types (HTTP, HTTPS, SOCKS5)
    if (config.host && config.port) {
      const scheme = config.type.toLowerCase(); // 'http', 'https', 'socks5'
      // SOCKS5 flag uses socks5://, HTTP uses http://, etc.
      args.push(`--proxy-server=${scheme}://${config.host}:${config.port}`);

      // If credentials are provided, generate the auth extension
      if (config.username && config.password) {
        extensionPath = this.generateProxyAuthExtension(profile.id, config.username, config.password);
      }
    }

    return { args, extensionPath };
  }

  generateProxyAuthExtension(profileId, username, password) {
    const extDir = path.join(this.profilesDir, profileId, 'proxy_auth_ext');
    if (!fs.existsSync(extDir)) {
      fs.mkdirSync(extDir, { recursive: true });
    }

    const manifestContent = {
      version: '1.0.0',
      manifest_version: 2,
      name: 'Gams-GALogin Proxy Auth',
      permissions: [
        'webRequest',
        'webRequestBlocking',
        '<all_urls>'
      ],
      background: {
        scripts: ['background.js']
      }
    };

    const backgroundContent = `
chrome.webRequest.onAuthRequired.addListener(
  function(details) {
    if (details.isProxy) {
      return {
        authCredentials: {
          username: "${username}",
          password: "${password}"
        }
      };
    }
  },
  { urls: ["<all_urls>"] },
  ["blocking"]
);
`;

    fs.writeFileSync(path.join(extDir, 'manifest.json'), JSON.stringify(manifestContent, null, 2), 'utf8');
    fs.writeFileSync(path.join(extDir, 'background.js'), backgroundContent, 'utf8');

    return extDir;
  }
}

module.exports = ProxyManager;
