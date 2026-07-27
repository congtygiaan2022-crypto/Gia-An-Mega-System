const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

/**
 * Interface/Base class for Browser Providers
 */
class IBrowserProvider {
  constructor(name) {
    this.name = name;
  }

  getExecutablePath() {
    throw new Error('Method getExecutablePath() must be implemented.');
  }

  getVersion() {
    const exe = this.getExecutablePath();
    if (!exe || !fs.existsSync(exe)) {
      return `${this.name} (Not Installed)`;
    }
    try {
      // On Windows, sometimes running --version prints to stdout, or we can use wmic/powershell
      const output = execSync(`"${exe}" --version`, { encoding: 'utf8', timeout: 3000 });
      return output.trim();
    } catch (e) {
      // Fallback
      return `${this.name} 125.0`;
    }
  }

  /**
   * Generates CLI arguments for this browser based on profile settings
   */
  getLaunchArguments(profile, customArgs = []) {
    const args = [
      `--user-data-dir=${profile.userDataDir}`,
      `--remote-debugging-port=${profile.port || 15001}`,
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-features=UserAgentClientHint',
      `--lang=${profile.language || 'vi-VN'}`,
      `--accept-lang=${profile.language || 'vi-VN'}`
    ];

    // WebRTC Leak Protection when using proxy
    if (profile.proxyConfig && profile.proxyConfig.type && profile.proxyConfig.type !== 'Direct') {
      args.push('--force-webrtc-ip-handling-policy=disable_non_proxied_udp');
    }

    // User Agent
    if (profile.userAgent) {
      args.push(`--user-agent=${profile.userAgent}`);
    }

    // Window sizing & positioning
    if (profile.windowSize) {
      const { width, height, x, y } = profile.windowSize;
      if (width && height) {
        args.push(`--window-size=${width},${height}`);
      }
      if (x !== undefined && y !== undefined) {
        args.push(`--window-position=${x},${y}`);
      }
    }

    // Startup URLs
    if (profile.startupConfig) {
      const { mode, urls } = profile.startupConfig;
      if (mode === 'blank') {
        args.push('about:blank');
      } else if (mode === 'urls' && Array.isArray(urls) && urls.length > 0) {
        urls.forEach(url => {
          if (url && url.trim()) {
            args.push(url.trim());
          }
        });
      } else if (mode === 'last_session') {
        args.push('--restore-last-session');
      }
    }

    // Custom arguments
    if (Array.isArray(profile.browserArguments)) {
      profile.browserArguments.forEach(arg => {
        if (arg && !args.includes(arg)) {
          args.push(arg);
        }
      });
    }

    // Additional custom args passed dynamically
    customArgs.forEach(arg => {
      if (arg && !args.includes(arg)) {
        args.push(arg);
      }
    });

    return args;
  }

  /**
   * Spawns the browser process
   */
  launch(profile, extraArgs = []) {
    const exe = this.getExecutablePath();
    if (!exe || !fs.existsSync(exe)) {
      throw new Error(`Browser executable not found at: ${exe}`);
    }

    const args = this.getLaunchArguments(profile, extraArgs);

    // Spawn detached process
    const child = spawn(exe, args, {
      detached: true,
      stdio: 'ignore',
      env: {
        ...process.env,
        // Apply timezone environment variable (for Chromium engines)
        TZ: profile.timezone || 'Asia/Ho_Chi_Minh'
      }
    });

    child.unref();
    return child;
  }

  /**
   * Closes browser process via PID
   */
  close(pid) {
    if (!pid) return;
    try {
      execSync(`taskkill /pid ${pid} /f /t`);
    } catch (err) {
      try {
        process.kill(pid, 'SIGKILL');
      } catch (e) {
        console.warn(`Failed to kill process PID ${pid}:`, e.message);
      }
    }
  }
}

/**
 * Built-in Chromium Browser Provider
 */
class ChromiumBrowserProvider extends IBrowserProvider {
  constructor() {
    super('Chromium (Built-in)');
    this.defaultPath = path.join(__dirname, '..', '..', 'bin', 'chromium', 'chrome-win', 'chrome.exe');
  }

  getExecutablePath() {
    return this.defaultPath;
  }
}

/**
 * Google Chrome System Browser Provider
 */
class ChromeBrowserProvider extends IBrowserProvider {
  constructor() {
    super('Google Chrome');
  }

  getExecutablePath() {
    const paths = [
      'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
      'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
      path.join(process.env.USERPROFILE || 'C:\\', 'AppData\\Local\\Google\\Chrome\\Application\\chrome.exe')
    ];
    for (const p of paths) {
      if (fs.existsSync(p)) return p;
    }
    return paths[0]; // fallback
  }
}

/**
 * Microsoft Edge System Browser Provider
 */
class EdgeBrowserProvider extends IBrowserProvider {
  constructor() {
    super('Microsoft Edge');
  }

  getExecutablePath() {
    const paths = [
      'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
      'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
      path.join(process.env.USERPROFILE || 'C:\\', 'AppData\\Local\\Microsoft\\Edge\\Application\\msedge.exe')
    ];
    for (const p of paths) {
      if (fs.existsSync(p)) return p;
    }
    return paths[0]; // fallback
  }
}

/**
 * Custom Path Browser Provider
 */
class CustomBrowserProvider extends IBrowserProvider {
  constructor(customPath) {
    super('Custom Browser');
    this.customPath = customPath;
  }

  getExecutablePath() {
    return this.customPath;
  }
}

module.exports = {
  IBrowserProvider,
  ChromiumBrowserProvider,
  ChromeBrowserProvider,
  EdgeBrowserProvider,
  CustomBrowserProvider
};
