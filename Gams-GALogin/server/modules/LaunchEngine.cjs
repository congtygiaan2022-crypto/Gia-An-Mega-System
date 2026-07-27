const path = require('path');
const fs = require('fs');

class LaunchEngine {
  constructor(browserManager, proxyManager, extensionManager, windowManager, loggingManager) {
    this.browserManager = browserManager;
    this.proxyManager = proxyManager;
    this.extensionManager = extensionManager;
    this.windowManager = windowManager;
    this.loggingManager = loggingManager;
    
    // In-memory active browsers store
    // Key: profileId, Value: { process, port, pid, startTime, status: 'starting' | 'running' | 'error', errorMsg }
    this.activeBrowsers = new Map();
  }

  async start(profile, layoutOptions = {}) {
    const profileId = profile.id;
    
    if (this.activeBrowsers.has(profileId)) {
      const running = this.activeBrowsers.get(profileId);
      if (running.status === 'running') {
        this.loggingManager.log(profileId, `Browser already running on port ${running.port} (PID ${running.pid}).`, 'WARNING');
        return running;
      }
    }

    this.loggingManager.log(profileId, `--- Initiating Browser Launch for Profile: ${profile.name} ---`, 'INFO');
    this.loggingManager.log(profileId, `Browser Type: ${profile.browserType || 'chromium'}. Timezone: ${profile.timezone || 'System'}`, 'INFO');

    // 1. Set status to starting
    const startingRecord = {
      port: profile.port || 15001,
      pid: null,
      startTime: new Date().toISOString(),
      status: 'starting',
      browserType: profile.browserType || 'chromium'
    };
    this.activeBrowsers.set(profileId, startingRecord);

    try {
      // 2. Resolve Proxy
      const { args: proxyArgs, extensionPath: proxyAuthExtPath } = this.proxyManager.prepareProxy(profile);
      if (proxyArgs.length > 0) {
        this.loggingManager.log(profileId, `Proxy CLI configured: ${proxyArgs.join(' ')}`, 'INFO');
      }
      if (proxyAuthExtPath) {
        this.loggingManager.log(profileId, `Proxy requires authentication. Extension generated at: ${proxyAuthExtPath}`, 'INFO');
      }

      // 3. Resolve Extensions
      const extraExtPaths = [];
      if (proxyAuthExtPath) {
        extraExtPaths.push(proxyAuthExtPath);
      }
      const extensionArgs = this.extensionManager.getLoadExtensionArgument(profile, extraExtPaths);
      if (extensionArgs.length > 0) {
        this.loggingManager.log(profileId, `Extensions loaded: ${extensionArgs.join(' ')}`, 'INFO');
      }

      // 4. Resolve Window size / position layout
      let windowLayoutArgs = [];
      const { layoutMode, layoutIndex, layoutTotal, screenWidth, screenHeight } = layoutOptions;
      if (layoutMode && layoutMode !== 'none') {
        windowLayoutArgs = this.windowManager.getLayoutArguments(
          layoutIndex || 0,
          layoutTotal || 1,
          layoutMode,
          screenWidth || 1920,
          screenHeight || 1080
        );
        this.loggingManager.log(profileId, `Window Manager Layout applied: ${layoutMode} -> CLI args: ${windowLayoutArgs.join(' ')}`, 'INFO');
      }

      // 5. Build combined arguments
      const extraArgs = [
        ...proxyArgs,
        ...extensionArgs,
        ...windowLayoutArgs
      ];

      // 6. Resolve Browser Provider
      const provider = this.browserManager.getProvider(profile.browserType, profile.executablePath);
      const exePath = provider.getExecutablePath();
      
      this.loggingManager.log(profileId, `Executable resolved: ${exePath}`, 'INFO');
      
      if (!fs.existsSync(exePath)) {
        throw new Error(`Executable file does not exist: ${exePath}`);
      }

      // 7. Launch
      this.loggingManager.log(profileId, `Spawning child process...`, 'INFO');
      const child = provider.launch(profile, extraArgs);

      if (!child || !child.pid) {
        throw new Error('Failed to spawn browser process (PID is null).');
      }

      // 8. Register running browser record
      const runningRecord = {
        process: child,
        port: profile.port || 15001,
        pid: child.pid,
        startTime: new Date().toISOString(),
        status: 'running',
        browserType: profile.browserType || 'chromium'
      };
      this.activeBrowsers.set(profileId, runningRecord);

      this.loggingManager.log(profileId, `Browser spawned successfully. PID: ${child.pid}, Debug Port: ${runningRecord.port}`, 'SUCCESS');

      // 8.5 Apply CDP overrides (e.g. Timezone Override & Fingerprints)
      this.applyCDPOverrides(profileId, runningRecord.port, profile);

      // 9. Attach exit listeners
      child.on('exit', (code, signal) => {
        this.loggingManager.log(profileId, `Browser process exited. Code: ${code}, Signal: ${signal}`, code === 0 ? 'INFO' : 'ERROR');
        const running = this.activeBrowsers.get(profileId);
        if (running && running.cdpWs) {
          try {
            running.cdpWs.close();
          } catch (e) {}
        }
        this.activeBrowsers.delete(profileId);
      });

      child.on('error', (err) => {
        this.loggingManager.log(profileId, `Browser process error: ${err.message}`, 'ERROR');
        const running = this.activeBrowsers.get(profileId);
        if (running && running.cdpWs) {
          try {
            running.cdpWs.close();
          } catch (e) {}
        }
        this.activeBrowsers.delete(profileId);
      });

      return runningRecord;

    } catch (err) {
      this.loggingManager.log(profileId, `Launch failed: ${err.message}`, 'ERROR');
      this.activeBrowsers.set(profileId, {
        port: profile.port || 15001,
        pid: null,
        startTime: new Date().toISOString(),
        status: 'error',
        errorMsg: err.message,
        browserType: profile.browserType || 'chromium'
      });
      throw err;
    }
  }

  async applyCDPOverrides(profileId, port, profile) {
    const timezone = profile.timezone;
    const hwConcurrency = profile.hardwareConcurrency || 8;
    const devMemory = profile.deviceMemory || 8;
    const spoofFingerprints = profile.spoofFingerprints !== false; // enabled by default

    this.loggingManager.log(profileId, `CDP: Attempting to connect to browser on port ${port} to apply overrides...`, 'INFO');
    
    const axios = require('axios');
    const WebSocket = require('ws');
    
    let debuggerUrl = null;
    for (let i = 0; i < 15; i++) {
      try {
        const res = await axios.get(`http://127.0.0.1:${port}/json/version`, { timeout: 1000 });
        if (res.data && res.data.webSocketDebuggerUrl) {
          debuggerUrl = res.data.webSocketDebuggerUrl;
          break;
        }
      } catch (err) {
        // Wait and retry
      }
      await new Promise(r => setTimeout(r, 300));
    }

    if (!debuggerUrl) {
      this.loggingManager.log(profileId, `CDP WARNING: Failed to retrieve webSocketDebuggerUrl from browser port ${port}. Overrides skipped.`, 'WARNING');
      return;
    }

    // Build fingerprint injection script
    const fingerprintScript = `
      // 1. Hardware Spoofer
      try {
        Object.defineProperty(Navigator.prototype, 'hardwareConcurrency', { get: () => ${hwConcurrency}, configurable: true });
        Object.defineProperty(Navigator.prototype, 'deviceMemory', { get: () => ${devMemory}, configurable: true });
      } catch (e) {}

      // 2. ClientRects Spoofer (adds tiny sub-pixel noise)
      try {
        const originalGetClientRects = Element.prototype.getClientRects;
        Element.prototype.getClientRects = function() {
          const rects = originalGetClientRects.apply(this, arguments);
          const fakeRects = [];
          for (let i = 0; i < rects.length; i++) {
            const r = rects[i];
            fakeRects.push({
              x: r.x + 0.0001,
              y: r.y + 0.0001,
              width: r.width,
              height: r.height,
              top: r.top + 0.0001,
              bottom: r.bottom + 0.0001,
              left: r.left + 0.0001,
              right: r.right + 0.0001,
              toJSON: () => r.toJSON()
            });
          }
          return fakeRects;
        };
      } catch (e) {}

      // 3. Canvas Spoofing (injects tiny color channel noise)
      try {
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function(x, y, w, h) {
          const imgData = originalGetImageData.apply(this, arguments);
          const noise = 3;
          for (let i = 0; i < imgData.data.length; i += 4) {
            imgData.data[i] = Math.min(255, Math.max(0, imgData.data[i] + (i % noise === 0 ? 1 : 0)));
          }
          return imgData;
        };
      } catch (e) {}

      // 4. WebGL Metadata Spoofer
      try {
        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
          // UNMASKED_VENDOR_WEBGL
          if (parameter === 37445) {
            return 'NVIDIA Corporation';
          }
          // UNMASKED_RENDERER_WEBGL
          if (parameter === 37446) {
            return 'NVIDIA GeForce GTX 1660/PCIe/SSE2';
          }
          return originalGetParameter.apply(this, arguments);
        };
      } catch (e) {}
    `;

    try {
      const ws = new WebSocket(debuggerUrl);
      
      const sendCommand = (method, params = {}, sessionId = undefined) => {
        const id = Math.floor(Math.random() * 1000000);
        ws.send(JSON.stringify({ id, method, params, sessionId }));
      };

      ws.on('open', () => {
        // Enable Auto-Attach to capture all tabs
        sendCommand('Target.setAutoAttach', {
          autoAttach: true,
          waitForDebuggerOnStart: false,
          flatten: true
        });
        this.loggingManager.log(profileId, `CDP: Auto-Attach enabled to capture all browser tabs.`, 'INFO');
      });

      ws.on('message', (data) => {
        try {
          const msg = JSON.parse(data);
          
          if (msg.method === 'Target.attachedToTarget') {
            const { sessionId, targetInfo } = msg.params;
            if (targetInfo.type === 'page') {
              this.loggingManager.log(profileId, `CDP: Target tab detected (Session ${sessionId}).`, 'INFO');
              
              // 1. Timezone Override
              if (timezone) {
                this.loggingManager.log(profileId, `CDP: Injecting timezone: ${timezone} to Session ${sessionId}`, 'INFO');
                sendCommand('Emulation.setTimezoneOverride', {
                  timezoneId: timezone
                }, sessionId);
              }

              // 2. Fingerprints Spoofing injection
              if (spoofFingerprints) {
                this.loggingManager.log(profileId, `CDP: Injecting browser fingerprint masking to Session ${sessionId}`, 'INFO');
                sendCommand('Page.enable', {}, sessionId);
                sendCommand('Page.addScriptToEvaluateOnNewDocument', {
                  source: fingerprintScript
                }, sessionId);
              }
            }
          }
        } catch (err) {
          // ignore parsing error
        }
      });

      ws.on('error', (err) => {
        this.loggingManager.log(profileId, `CDP ERROR: WebSocket error: ${err.message}`, 'ERROR');
      });

      const running = this.activeBrowsers.get(profileId);
      if (running) {
        running.cdpWs = ws;
      }

    } catch (err) {
      this.loggingManager.log(profileId, `CDP ERROR: Failed to connect to WebSocket on ${debuggerUrl}: ${err.message}`, 'ERROR');
    }
  }

  async stop(profileId) {
    if (!this.activeBrowsers.has(profileId)) {
      this.loggingManager.log(profileId, 'Stop request skipped: Browser process is not active.', 'WARNING');
      return false;
    }

    const browser = this.activeBrowsers.get(profileId);
    this.loggingManager.log(profileId, `Closing browser process for PID ${browser.pid}...`, 'INFO');
    
    if (browser.cdpWs) {
      try {
        browser.cdpWs.close();
      } catch (e) {}
    }

    try {
      const provider = this.browserManager.getProvider(browser.browserType);
      provider.close(browser.pid);
      this.activeBrowsers.delete(profileId);
      this.loggingManager.log(profileId, 'Browser closed and process terminated.', 'SUCCESS');
      return true;
    } catch (err) {
      this.loggingManager.log(profileId, `Failed to close browser: ${err.message}`, 'ERROR');
      return false;
    }
  }

  async stopAll() {
    console.log(`Stopping all active browsers (${this.activeBrowsers.size} running)...`);
    const ids = Array.from(this.activeBrowsers.keys());
    let count = 0;
    for (const id of ids) {
      const stopped = await this.stop(id);
      if (stopped) count++;
    }
    return count;
  }

  getStatus(profileId) {
    if (!this.activeBrowsers.has(profileId)) {
      return 'stopped';
    }
    return this.activeBrowsers.get(profileId).status;
  }

  getActiveRecord(profileId) {
    return this.activeBrowsers.get(profileId) || null;
  }
}

module.exports = LaunchEngine;
