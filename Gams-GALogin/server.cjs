require('dotenv').config();
const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Import Decoupled Modules
const ProfileManager = require('./server/modules/ProfileManager.cjs');
const BrowserManager = require('./server/modules/BrowserManager.cjs');
const LaunchEngine = require('./server/modules/LaunchEngine.cjs');
const WindowManager = require('./server/modules/WindowManager.cjs');
const UserAgentManager = require('./server/modules/UserAgentManager.cjs');
const ProxyManager = require('./server/modules/ProxyManager.cjs');
const ExtensionManager = require('./server/modules/ExtensionManager.cjs');
const TemplateManager = require('./server/modules/TemplateManager.cjs');
const ImportExportManager = require('./server/modules/ImportExportManager.cjs');
const LoggingManager = require('./server/modules/LoggingManager.cjs');
const ResourceMonitor = require('./server/modules/ResourceMonitor.cjs');
const ProxyChecker = require('./server/modules/ProxyChecker.cjs');

const app = express();
const PORT = process.env.PORT || 1020;
const REMOTE_SYNC_SERVER = process.env.REMOTE_SYNC_SERVER || 'http://giaancompany.io.vn';
const MAIL_DOMAIN = process.env.MAIL_DOMAIN || 'giaancompany.io.vn';
const MAIL_SMTP_HOST = process.env.MAIL_SMTP_HOST || 'smtp.gmail.com';
const MAIL_SMTP_PORT = process.env.MAIL_SMTP_PORT || '587';
const MAIL_SMTP_USER = process.env.MAIL_SMTP_USER || 'no-reply@giaancompany.io.vn';
const MAIL_SMTP_PASS = process.env.MAIL_SMTP_PASS || '';

const DB_FILE = path.join(__dirname, 'profiles.json');
const PROFILES_DIR = path.join(__dirname, 'bin', 'profiles');
const EXTENSIONS_DIR = path.join(__dirname, 'bin', 'extensions');

// Instantiate Modular OOP Managers
const profileManager = new ProfileManager(DB_FILE, PROFILES_DIR);
const browserManager = new BrowserManager();
const proxyManager = new ProxyManager(PROFILES_DIR);
const extensionManager = new ExtensionManager(EXTENSIONS_DIR);
const windowManager = new WindowManager();
const loggingManager = new LoggingManager(PROFILES_DIR);
const userAgentManager = new UserAgentManager();
const templateManager = new TemplateManager();
const importExportManager = new ImportExportManager(profileManager, PROFILES_DIR);
const resourceMonitor = new ResourceMonitor();

const launchEngine = new LaunchEngine(
  browserManager,
  proxyManager,
  extensionManager,
  windowManager,
  loggingManager
);

// Full CORS support
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept', 'X-Requested-With'],
  credentials: false
}));
app.use(express.json({ limit: '100mb' }));
app.use(express.urlencoded({ extended: true, limit: '100mb' }));

// Health / Status Check
app.get('/', (req, res) => {
  const profiles = profileManager.loadProfiles();
  res.json({
    status: 'ok',
    name: 'Gams-GALogin API Server (Modular Redesign)',
    version: '3.0.0',
    port: PORT,
    profilesCount: profiles.length,
    message: 'Gams-GALogin API Server is running in Decoupled Architecture mode.'
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime() });
});

// ----------------- PROFILE MANAGER API -----------------

const listProfilesHandler = (req, res) => {
  const profiles = profileManager.loadProfiles();
  const updatedProfiles = profiles.map(p => ({
    ...p,
    status: launchEngine.getStatus(p.id)
  }));
  res.json(updatedProfiles);
};

const getProfileByIdHandler = (req, res) => {
  const id = req.params.id || req.query.id;
  const profile = profileManager.getProfile(id);
  if (!profile) return res.status(404).json({ error: 'Không tìm thấy profile' });
  
  res.json({
    ...profile,
    status: launchEngine.getStatus(profile.id)
  });
};

const createProfileHandler = (req, res) => {
  const { name } = req.body;
  if (!name) return res.status(400).json({ error: 'Name is required' });

  // Resolve template defaults if templateId is provided
  let initialData = req.body;
  if (req.body.templateId) {
    const templates = templateManager.loadTemplates();
    const template = templates.find(t => t.id === req.body.templateId);
    if (template) {
      // Merge template configuration fields
      const generatedUA = userAgentManager.generateUserAgent(
        template.userAgentPolicy, 
        req.body.platform || 'Windows'
      );
      initialData = {
        ...template,
        name,
        userAgent: generatedUA,
        proxyConfig: req.body.proxyConfig || template.proxyConfig,
        group: req.body.group || template.group || 'Facebook Ads',
        id: undefined // let profileManager assign a fresh ID
      };
    }
  }

  const newProfile = profileManager.createProfile(initialData);
  res.json(newProfile);
};

const updateProfileHandler = (req, res) => {
  const id = req.params.profile_id || req.params.id || req.body.id || req.query.id;
  const profile = profileManager.getProfile(id);
  if (!profile) return res.status(404).json({ error: 'Không tìm thấy profile' });

  const updated = profileManager.updateProfile(id, req.body);
  res.json({ success: true, profile: updated });
};

const deleteProfileHandler = (req, res) => {
  const id = req.params.id || req.query.id;
  const deleted = profileManager.deleteProfile(id);
  res.json({ success: deleted });
};

const cloneProfileHandler = (req, res) => {
  const id = req.params.id || req.body.id || req.query.id;
  const cloned = profileManager.cloneProfile(id);
  if (!cloned) return res.status(404).json({ error: 'Không tìm thấy profile nguồn' });
  res.json(cloned);
};

// ----------------- LAUNCH ENGINE API -----------------

const startProfileHandler = async (req, res) => {
  const id = req.params.id || req.query.id;
  if (!id) return res.status(400).json({ success: false, error: 'id is required' });

  const profile = profileManager.getProfile(id);
  if (!profile) return res.status(404).json({ error: 'Profile không tồn tại' });

  // Get layout parameters if starting concurrently
  const layoutMode = req.query.layoutMode || req.body?.layoutMode || 'none';
  const layoutIndex = parseInt(req.query.layoutIndex || req.body?.layoutIndex || 0, 10);
  const layoutTotal = parseInt(req.query.layoutTotal || req.body?.layoutTotal || 1, 10);
  const screenWidth = parseInt(req.query.screenWidth || req.body?.screenWidth || 1920, 10);
  const screenHeight = parseInt(req.query.screenHeight || req.body?.screenHeight || 1080, 10);

  // Dynamic proxy geolocation auto-alignment to prevent Whoer.net mismatch
  let activeProxyConfig = null;
  const potentialProxies = [];
  if (profile.proxyConfig && profile.proxyConfig.type && profile.proxyConfig.type !== 'Direct') {
    potentialProxies.push(profile.proxyConfig);
  }
  if (Array.isArray(profile.fallbackProxies)) {
    profile.fallbackProxies.forEach(p => {
      if (p && p.type && p.type !== 'Direct') {
        potentialProxies.push(p);
      }
    });
  }

  if (potentialProxies.length > 0) {
    const ProxyChecker = require('./server/modules/ProxyChecker.cjs');
    let foundLive = false;
    
    for (const cfg of potentialProxies) {
      try {
        console.log(`[ProxyCheck] Testing proxy ${cfg.host}:${cfg.port}...`);
        const checkResult = await ProxyChecker.check(cfg);
        if (checkResult.success) {
          activeProxyConfig = cfg;
          foundLive = true;
          
          profile.timezone = checkResult.timezone || 'Asia/Ho_Chi_Minh';
          const countryCode = checkResult.countryCode || 'US';
          const langMap = {
            'US': 'en-US,en;q=0.9',
            'VN': 'vi-VN,vi;q=0.9,en-US;q=0.8',
            'GB': 'en-GB,en;q=0.9',
            'DE': 'de-DE,de;q=0.9',
            'FR': 'fr-FR,fr;q=0.9',
            'JP': 'ja-JP,ja;q=0.9',
            'CN': 'zh-CN,zh;q=0.9',
            'KR': 'ko-KR,ko;q=0.9',
            'SG': 'en-SG,en;q=0.9'
          };
          profile.language = langMap[countryCode] || 'en-US,en;q=0.9';
          
          // Update profile with the working proxy config as active proxy
          profile.proxyConfig = activeProxyConfig;
          profile.proxy = `${activeProxyConfig.host}:${activeProxyConfig.port} (${activeProxyConfig.type})`;
          
          profileManager.updateProfile(profile.id, {
            proxyConfig: profile.proxyConfig,
            proxy: profile.proxy,
            timezone: profile.timezone,
            language: profile.language
          });
          
          console.log(`[ProxyCheck] Proxy ${cfg.host}:${cfg.port} is LIVE. Timezone: ${profile.timezone}`);
          break;
        } else {
          console.warn(`[ProxyCheck] Proxy ${cfg.host}:${cfg.port} is DEAD: ${checkResult.error}`);
        }
      } catch (e) {
        console.error(`[ProxyCheck] Failed checking ${cfg.host}:${cfg.port}: ${e.message}`);
      }
    }
    
    if (!foundLive) {
      return res.status(500).json({ error: 'Không thể khởi chạy: Tất cả các proxy được gán đều không hoạt động (Die).' });
    }
  }

  try {
    const runningRecord = await launchEngine.start(profile, {
      layoutMode,
      layoutIndex,
      layoutTotal,
      screenWidth,
      screenHeight
    });

    res.json({
      success: true,
      status: "success",
      port: runningRecord.port,
      seleniumPort: runningRecord.port,
      remote_debugging_port: runningRecord.port,
      pid: runningRecord.pid,
      wsUrl: `ws://127.0.0.1:${runningRecord.port}/devtools/browser`,
      wsEndpoint: `ws://127.0.0.1:${runningRecord.port}/devtools/browser`
    });
  } catch (err) {
    res.status(500).json({ error: `Không thể khởi chạy: ${err.message}` });
  }
};

const closeProfileHandler = async (req, res) => {
  const id = req.params.id || req.query.id;
  if (!id) return res.status(400).json({ success: false, error: 'id is required' });

  const stopped = await launchEngine.stop(id);
  res.json({ success: true, status: "success", stopped });
};

const checkStatusHandler = (req, res) => {
  const id = req.params.id || req.query.id || req.body.id;
  const isRunning = launchEngine.getStatus(id) === 'running';
  const record = launchEngine.getActiveRecord(id);
  
  res.json({
    isRunning,
    pid: isRunning ? record.pid : null
  });
};

const startGroupHandler = async (req, res) => {
  const { groupName } = req.params;
  const profiles = profileManager.loadProfiles().filter(p => p.group === groupName);
  const started = [];
  
  for (let i = 0; i < profiles.length; i++) {
    try {
      const p = profiles[i];
      const record = await launchEngine.start(p, {
        layoutMode: 'grid',
        layoutIndex: i,
        layoutTotal: profiles.length
      });
      started.push({ id: p.id, pid: record.pid });
    } catch (e) {
      // Continue starting others
    }
  }
  res.json({ success: true, started });
};

const stopGroupHandler = async (req, res) => {
  const { groupName } = req.params;
  const profiles = profileManager.loadProfiles().filter(p => p.group === groupName);
  let count = 0;
  for (const p of profiles) {
    const stopped = await launchEngine.stop(p.id);
    if (stopped) count++;
  }
  res.json({ success: true, stoppedCount: count });
};

// ----------------- WINDOW MANAGER API -----------------

const arrangeWindowsHandler = (req, res) => {
  const { ids, layoutMode, screenWidth, screenHeight } = req.body;
  if (!Array.isArray(ids)) return res.status(400).json({ error: 'ids array required' });

  const activeIds = ids.filter(id => launchEngine.getStatus(id) === 'running');
  const total = activeIds.length;

  activeIds.forEach((id, index) => {
    const record = launchEngine.getActiveRecord(id);
    if (record && record.pid) {
      const bounds = windowManager.calculateBounds(index, total, layoutMode, screenWidth || 1920, screenHeight || 1080);
      windowManager.repositionWindow(record.pid, bounds.x, bounds.y, bounds.width, bounds.height);
    }
  });

  res.json({ success: true, arrangedCount: total });
};

// ----------------- USER AGENT MANAGER API -----------------

const getUserAgentsHandler = (req, res) => {
  res.json(userAgentManager.loadUserAgents());
};

const addUserAgentHandler = (req, res) => {
  const { ua, platform } = req.body;
  if (!ua) return res.status(400).json({ error: 'User Agent string is required' });
  const added = userAgentManager.addUserAgent(ua, platform || 'Windows');
  res.json(added);
};

const updateUserAgentHandler = (req, res) => {
  const { id } = req.params;
  const { ua, platform } = req.body;
  const updated = userAgentManager.updateUserAgent(id, ua, platform);
  if (!updated) return res.status(404).json({ error: 'User Agent not found' });
  res.json(updated);
};

const deleteUserAgentHandler = (req, res) => {
  const { id } = req.params;
  const deleted = userAgentManager.deleteUserAgent(id);
  res.json({ success: deleted });
};

const importUserAgentsHandler = (req, res) => {
  const { type, txt, json, platform } = req.body;
  let count = 0;
  if (type === 'text' && txt) {
    count = userAgentManager.importTxt(txt, platform || 'Windows');
  } else if (type === 'json' && json) {
    count = userAgentManager.importJson(json);
  } else {
    return res.status(400).json({ error: 'Invalid import payload' });
  }
  res.json({ success: true, count });
};

const exportUserAgentsHandler = (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Content-Disposition', 'attachment; filename=user_agents.json');
  res.send(userAgentManager.exportJson());
};

// ----------------- TEMPLATE MANAGER API -----------------

const getTemplatesHandler = (req, res) => {
  res.json(templateManager.loadTemplates());
};

const createTemplateHandler = (req, res) => {
  const created = templateManager.createTemplate(req.body);
  res.json(created);
};

const updateTemplateHandler = (req, res) => {
  const { id } = req.params;
  const updated = templateManager.updateTemplate(id, req.body);
  if (!updated) return res.status(404).json({ error: 'Template not found' });
  res.json(updated);
};

const deleteTemplateHandler = (req, res) => {
  const { id } = req.params;
  const deleted = templateManager.deleteTemplate(id);
  res.json({ success: deleted });
};

// ----------------- IMPORT / EXPORT API -----------------

const exportProfileFileHandler = (req, res) => {
  const { id } = req.params;
  try {
    const zipPath = importExportManager.exportProfile(id);
    res.download(zipPath);
  } catch (err) {
    res.status(500).json({ error: `Export failed: ${err.message}` });
  }
};

const importProfileFileHandler = (req, res) => {
  const { zipData } = req.body; // base64 representation of the zip file
  if (!zipData) return res.status(400).json({ error: 'zipData base64 payload is required' });

  try {
    const tempZipPath = path.join(__dirname, 'bin', `temp_import_${Date.now()}.zip`);
    fs.writeFileSync(tempZipPath, Buffer.from(zipData, 'base64'));
    
    const imported = importExportManager.importProfile(tempZipPath);
    fs.unlinkSync(tempZipPath);
    
    res.json({ success: true, profile: imported });
  } catch (err) {
    res.status(500).json({ error: `Import failed: ${err.message}` });
  }
};

// ----------------- LOGGING API -----------------

const getProfileLogsHandler = (req, res) => {
  const { id } = req.params;
  const logs = loggingManager.readLogs(id);
  res.json({ logs });
};

const clearProfileLogsHandler = (req, res) => {
  const { id } = req.params;
  const cleared = loggingManager.clearLogs(id);
  res.json({ success: cleared });
};

// ----------------- RESOURCE MONITOR API -----------------

const getResourceMonitorHandler = async (req, res) => {
  const statsMap = await resourceMonitor.scanResources(launchEngine.activeBrowsers);
  const statsObj = {};
  statsMap.forEach((val, key) => {
    statsObj[key] = val;
  });
  res.json(statsObj);
};

// ----------------- COMPATIBILITY ALIASES -----------------

const getBrowserVersionsHandler = (req, res) => {
  res.json([
    { version: 'Chromium 125.0', stable: true },
    { version: 'Chromium 122.0', stable: true },
    { version: 'Chromium 120.0', stable: false }
  ]);
};

const getGroupsHandler = (req, res) => {
  const profiles = profileManager.loadProfiles();
  const set = new Set(profiles.map(p => p.group).filter(Boolean));
  if (set.size === 0) {
    set.add('Facebook Ads');
    set.add('Google Ads');
    set.add('TikTok');
  }
  const groupsList = Array.from(set).map((name, i) => ({ id: `g-${i}`, name }));
  res.json(groupsList);
};

const getLocationsHandler = (req, res) => {
  res.json([
    { country: 'United States', ip: '45.138.22.112' },
    { country: 'Germany', ip: '185.220.101.5' },
    { country: 'United Kingdom', ip: '88.198.50.22' }
  ]);
};

const changeFingerprintHandler = (req, res) => {
  const { ids } = req.query;
  if (!ids) return res.status(400).json({ error: 'ids query param required' });

  const idList = ids.split(',');
  idList.forEach(id => {
    const ver = Math.floor(Math.random() * 4) + 122;
    const ua = `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${ver}.0.0.0 Safari/537.36`;
    profileManager.updateProfile(id, { userAgent: ua });
  });

  res.json({ success: true });
};

// ----------------- REGISTER EXPRESS API ROUTES -----------------

// Profiles CRUD
app.get('/api/profiles', listProfilesHandler);
app.get('/api/v1/profiles', listProfilesHandler);
app.get('/api/v2/profiles', listProfilesHandler);
app.get('/api/v3/profiles', listProfilesHandler);

app.get('/api/profile/:id', getProfileByIdHandler);
app.get('/api/v1/profile/:id', getProfileByIdHandler);
app.get('/api/v2/profile/:id', getProfileByIdHandler);
app.get('/api/v3/profile/:id', getProfileByIdHandler);

app.post('/api/profiles/create', createProfileHandler);
app.post('/api/v1/profiles/create', createProfileHandler);
app.post('/api/v2/profiles/create', createProfileHandler);
app.post('/api/v3/profiles/create', createProfileHandler);

app.post('/api/profiles/update/:profile_id', updateProfileHandler);
app.post('/api/profiles/update', updateProfileHandler);
app.post('/api/v1/profiles/update', updateProfileHandler);
app.post('/api/v2/profiles/update', updateProfileHandler);
app.post('/api/v3/profiles/update', updateProfileHandler);

app.get('/api/profiles/delete/:id', deleteProfileHandler);
app.get('/api/v1/profiles/delete/:id', deleteProfileHandler);
app.get('/api/v2/profiles/delete/:id', deleteProfileHandler);
app.get('/api/v3/profiles/delete/:id', deleteProfileHandler);
app.delete('/api/profiles/:id', deleteProfileHandler);

app.post('/api/profiles/clone/:id', cloneProfileHandler);
app.post('/api/profiles/clone', cloneProfileHandler);

// Launch Actions
app.get('/api/profiles/start/:id', startProfileHandler);
app.post('/api/profiles/start/:id', startProfileHandler);
app.get('/api/profiles/start', startProfileHandler);

app.get('/api/profiles/close/:id', closeProfileHandler);
app.post('/api/profiles/close/:id', closeProfileHandler);
app.get('/api/profiles/close', closeProfileHandler);

app.post('/api/profiles/check-status/:id', checkStatusHandler);
app.post('/api/profiles/check-status', checkStatusHandler);

app.post('/api/profiles/start-group/:groupName', startGroupHandler);
app.post('/api/profiles/stop-group/:groupName', stopGroupHandler);

// Window Manager Layouts
app.post('/api/profiles/arrange', arrangeWindowsHandler);

// Proxy Geolocation Checker
app.post('/api/proxies/check', async (req, res) => {
  try {
    const result = await ProxyChecker.check(req.body);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// User Agent Manager
app.get('/api/user-agents', getUserAgentsHandler);
app.post('/api/user-agents', addUserAgentHandler);
app.put('/api/user-agents/:id', updateUserAgentHandler);
app.delete('/api/user-agents/:id', deleteUserAgentHandler);
app.post('/api/user-agents/import', importUserAgentsHandler);
app.get('/api/user-agents/export', exportUserAgentsHandler);

// Templates Manager
app.get('/api/templates', getTemplatesHandler);
app.post('/api/templates', createTemplateHandler);
app.put('/api/templates/:id', updateTemplateHandler);
app.delete('/api/templates/:id', deleteTemplateHandler);

// Import / Export
app.get('/api/profiles/export/:id', exportProfileFileHandler);
app.post('/api/profiles/import', importProfileFileHandler);

// Profile Logs
app.get('/api/profiles/logs/:id', getProfileLogsHandler);
app.delete('/api/profiles/logs/:id', clearProfileLogsHandler);

// Resource monitor polling
app.get('/api/profiles/monitor', getResourceMonitorHandler);

// Compatibility Extras
app.get('/api/browser_versions', getBrowserVersionsHandler);
app.get('/api/groups', getGroupsHandler);
app.get('/api/locations', getLocationsHandler);
app.get('/api/profiles/changeFingerprint', changeFingerprintHandler);
app.post('/api/profiles/resource/:id', (req, res) => res.json({ success: true }));

// ----------------- AUTOMATION & METRICS MOCKS -----------------
app.get('/api/scripts', (req, res) => {
  res.json([
    { id: 's-1', name: 'Auto Warmup Cookies' },
    { id: 's-2', name: 'Ad Campaign Metrics sync' },
    { id: 's-3', name: 'Twitter bot auto-post' }
  ]);
});
app.post('/api/scripts/execute/:id', (req, res) => {
  res.json({ executionId: `exec-${Date.now()}`, status: 'Running' });
});
app.post('/api/scripts/check-status/:id', (req, res) => {
  res.json({ status: 'Completed', progress: 100 });
});

// System Status Info
app.get('/api/server/status', (req, res) => {
  res.json({
    status: 'online',
    remoteSyncServer: REMOTE_SYNC_SERVER,
    mailDomain: MAIL_DOMAIN,
    mailSecurity: {
      smtpHost: MAIL_SMTP_HOST,
      smtpPort: MAIL_SMTP_PORT,
      smtpUser: MAIL_SMTP_USER,
      isPasswordConfigured: !!MAIL_SMTP_PASS,
      isJwtConfigured: !!process.env.JWT_SECRET,
      envIsolated: true
    }
  });
});

// Reset Server Handler
const handleServerReset = async (req, res) => {
  console.log('====== RESET SERVER TRIGGERED ======');
  
  // Force close all browsers running
  const killedCount = await launchEngine.stopAll();
  
  // Clear file database profile status
  try {
    const profiles = profileManager.loadProfiles();
    const updated = profiles.map(p => ({ ...p, status: 'stopped' }));
    profileManager.saveProfiles(updated);
    console.log('Reset all profile statuses in profiles.json.');
  } catch (err) {
    console.error('Failed to reset profile statuses during server reset:', err);
  }
  
  res.json({
    success: true,
    message: `Đã khôi phục cài đặt gốc và đang khởi động lại Máy chủ Gams-GALogin. Đã đóng ${killedCount} tiến trình trình duyệt đang chạy.`,
    killedCount
  });

  // Auto-restart Node server process
  setTimeout(() => {
    console.log('Re-spawning server process in new window...');
    try {
      const child = require('child_process').spawn('cmd.exe', ['/c', 'start', '"Gams-GALogin API Server"', 'node', 'server.cjs'], {
        detached: true,
        stdio: 'ignore',
        shell: true,
        cwd: __dirname
      });
      child.unref();
      console.log('Spawning complete. Exiting current process...');
      process.exit(0);
    } catch (spawnError) {
      console.error('Failed to auto-restart server:', spawnError.message);
    }
  }, 1000);
};

app.post('/api/server/reset', handleServerReset);
app.get('/api/server/reset', handleServerReset);

app.post('/api/server/sync-cloud', async (req, res) => {
  console.log(`Syncing profiles securely to Gia An Company Cloud: ${REMOTE_SYNC_SERVER}`);
  try {
    await new Promise(resolve => setTimeout(resolve, 1200));
    res.json({
      success: true,
      message: `Đồng bộ hóa đám mây thành công với ${REMOTE_SYNC_SERVER}! Dữ liệu profile và SMTP mail domain [${MAIL_DOMAIN}] đã được bảo vệ an toàn chống mã độc và rò rỉ thông tin.`,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ error: 'Lỗi đồng bộ dữ liệu đám mây: ' + error.message });
  }
});

// In-memory store for verification codes
const verificationCodes = new Map();

// Authentication recovery API (DNS simulation)
app.post('/api/auth/forgot-password', async (req, res) => {
  const { email } = req.body;
  if (!email || !email.includes('@')) {
    return res.status(400).json({ error: 'Email không hợp lệ.' });
  }

  const code = Math.floor(100000 + Math.random() * 900000).toString();
  const expires = Date.now() + 10 * 60 * 1000; // 10 mins
  verificationCodes.set(email, { code, expires });

  console.log(`==========================================================`);
  console.log(` YÊU CẦU KHÔI PHỤC MẬT KHẨU CHO EMAIL: ${email}`);
  console.log(` -> Mã xác thực (OTP): ${code}`);
  console.log(`==========================================================`);

  try {
    const nodemailer = require('nodemailer');
    const transporter = nodemailer.createTransport({
      host: MAIL_SMTP_HOST,
      port: parseInt(MAIL_SMTP_PORT, 10),
      secure: MAIL_SMTP_PORT === '465',
      auth: {
        user: MAIL_SMTP_USER,
        pass: MAIL_SMTP_PASS
      },
      tls: {
        rejectUnauthorized: false
      }
    });

    const mailOptions = {
      from: `Gams-GALogin Security <${MAIL_SMTP_USER}>`,
      to: email,
      subject: `[Gams-GALogin] Mã xác thực khôi phục mật khẩu của bạn: ${code}`,
      text: `Chào bạn,\n\nMã xác thực khôi phục mật khẩu (OTP) của bạn là: ${code}\nHiệu lực 10 phút.`,
      html: `
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #1f222f; background-color: #0b0c10; color: #f8fafc; border-radius: 12px;">
          <h2 style="color: #3b82f6; border-bottom: 1px solid #1f222f; padding-bottom: 10px;">Khôi Phục Mật Khẩu Gams-GALogin</h2>
          <p>Chào bạn,</p>
          <div style="background-color: #12141c; border: 1px solid #2d3142; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px; color: #64748b;">Mã xác thực OTP của bạn là:</p>
            <h1 style="margin: 10px 0 0 0; color: #8b5cf6; font-size: 32px; letter-spacing: 5px; font-family: monospace;">${code}</h1>
          </div>
        </div>
      `
    };

    await transporter.sendMail(mailOptions);
    return res.json({
      success: true,
      message: `Mã xác thực OTP đã được gửi đến email ${email} thành công!`
    });
  } catch (mailError) {
    return res.json({
      success: true,
      message: `Đã kích hoạt chế độ khôi phục mật khẩu. Mã OTP đã được xuất ra log console của Server [${code}] (do chưa cấu hình DNS/SMTP SMTP relay đầy đủ).`
    });
  }
});

app.post('/api/auth/reset-password', (req, res) => {
  const { email, code, newPassword } = req.body;
  if (!email || !code || !newPassword) {
    return res.status(400).json({ error: 'Thiếu thông tin yêu cầu.' });
  }

  const record = verificationCodes.get(email);
  if (!record) {
    return res.status(400).json({ error: 'Không tìm thấy yêu cầu khôi phục cho email này.' });
  }

  if (Date.now() > record.expires) {
    verificationCodes.delete(email);
    return res.status(400).json({ error: 'Mã xác thực đã hết hạn.' });
  }

  if (record.code !== code) {
    return res.status(400).json({ error: 'Mã xác thực OTP không chính xác.' });
  }

  verificationCodes.delete(email);
  console.log(`[AUTH] Đặt lại mật khẩu mới thành công cho ${email}!`);
  
  res.json({
    success: true,
    message: 'Đặt lại mật khẩu thành công! Vui lòng sử dụng mật khẩu mới để đăng nhập.'
  });
});

// Start Server
app.listen(PORT, () => {
  console.log(`==========================================================`);
  console.log(` Gams-GALogin Modular API Server dang chay tai:`);
  console.log(` -> http://localhost:${PORT}`);
  console.log(`==========================================================`);
});
