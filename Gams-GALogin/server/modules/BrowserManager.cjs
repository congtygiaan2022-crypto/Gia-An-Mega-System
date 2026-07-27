const {
  ChromiumBrowserProvider,
  ChromeBrowserProvider,
  EdgeBrowserProvider,
  CustomBrowserProvider
} = require('./BrowserProviders.cjs');

class BrowserManager {
  constructor() {
    this.providers = {
      chromium: new ChromiumBrowserProvider(),
      chrome: new ChromeBrowserProvider(),
      edge: new EdgeBrowserProvider()
    };
  }

  getProvider(browserType, customPath = '') {
    const type = (browserType || 'chromium').toLowerCase();
    if (type === 'custom' && customPath) {
      return new CustomBrowserProvider(customPath);
    }
    return this.providers[type] || this.providers['chromium'];
  }

  getAvailableBrowsers() {
    return Object.keys(this.providers).map(key => {
      const provider = this.providers[key];
      return {
        type: key,
        name: provider.name,
        path: provider.getExecutablePath(),
        version: provider.getVersion()
      };
    });
  }
}

module.exports = BrowserManager;
