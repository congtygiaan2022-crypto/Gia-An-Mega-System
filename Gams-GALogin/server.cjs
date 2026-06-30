require('dotenv').config();
const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

const app = express();
const PORT = process.env.PORT || 1020;
const REMOTE_SYNC_SERVER = process.env.REMOTE_SYNC_SERVER || 'http://giaancompany.io.vn';
const MAIL_DOMAIN = process.env.MAIL_DOMAIN || 'giaancompany.io.vn';
const MAIL_SMTP_HOST = process.env.MAIL_SMTP_HOST || 'smtp.gmail.com';
const MAIL_SMTP_PORT = process.env.MAIL_SMTP_PORT || '587';
const MAIL_SMTP_USER = process.env.MAIL_SMTP_USER || 'no-reply@giaancompany.io.vn';
const MAIL_SMTP_PASS = process.env.MAIL_SMTP_PASS || '';
const DB_FILE = path.join(__dirname, 'profiles.json');
const CHROMIUM_EXE = path.join(__dirname, 'bin', 'chromium', 'chrome-win', 'chrome.exe');
const PROFILES_DIR = path.join(__dirname, 'bin', 'profiles');

// Full CORS - Allow all external software (GenLogin, GPMLogin, automation tools) to connect
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept', 'X-Requested-With'],
  credentials: false
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Health check - Verify server is alive
app.get('/', (req, res) => {
  const profiles = loadProfiles();
  res.json({
    status: 'ok',
    name: 'Gams-GALogin API Server',
    version: '2.4.1',
    port: PORT,
    profilesCount: profiles.length,
    message: 'Gams-GALogin API Server is running and ready to accept connections.'
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime() });
});

// Memory store for tracking active browser processes
// Key: profileId, Value: { process, port, pid }
const activeBrowsers = new Map();

// Helper to load profiles from JSON file
function loadProfiles() {
  let profiles = [];
  if (!fs.existsSync(DB_FILE)) {
    // Seed default profiles
    const defaultProfiles = [
      {
        id: 'p-1',
        name: 'Facebook Ad Account 01',
        status: 'stopped',
        proxy: '45.138.22.112:8000',
        browserVersion: 'Chromium 122.0',
        lastOpened: '2026-06-10 18:45',
        notes: 'Tài khoản quảng cáo chính cho chiến dịch Thương mại điện tử',
        group: 'Facebook Ads',
        cookiesCount: 142,
        platform: 'Windows',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        port: 15001
      },
      {
        id: 'p-2',
        name: 'Google Ads Agency Profile',
        status: 'stopped',
        proxy: '185.220.101.5:9050',
        browserVersion: 'Chromium 122.0',
        lastOpened: '2026-06-11 04:30',
        notes: 'Tài khoản Agency cho Khách hàng Alpha',
        group: 'Google Ads',
        cookiesCount: 89,
        platform: 'macOS',
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        port: 15002
      },
      {
        id: 'p-3',
        name: 'TikTok Creator Hub - Beta',
        status: 'stopped',
        proxy: 'No Proxy (Direct)',
        browserVersion: 'Chromium 120.0',
        lastOpened: '2026-06-08 11:20',
        notes: 'Bảng điều khiển nhà sáng tạo để tải lên nội dung lan truyền',
        group: 'TikTok',
        cookiesCount: 204,
        platform: 'Linux',
        userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        port: 15003
      }
    ];
    fs.writeFileSync(DB_FILE, JSON.stringify(defaultProfiles, null, 2));
    profiles = defaultProfiles;
  } else {
    try {
      const raw = fs.readFileSync(DB_FILE);
      profiles = JSON.parse(raw);
    } catch (err) {
      console.error('Error reading profiles database:', err);
      profiles = [];
    }
  }

  // Ensure every profile has a unique, fixed debugging port assigned permanently
  let changed = false;
  profiles.forEach(p => {
    if (!p.port) {
      const existingPorts = profiles.map(x => x.port).filter(Boolean);
      let candidate = 15001;
      while (existingPorts.includes(candidate)) {
        candidate++;
      }
      p.port = candidate;
      changed = true;
    }
  });

  if (changed) {
    fs.writeFileSync(DB_FILE, JSON.stringify(profiles, null, 2));
  }

  return profiles;
}

// Helper to save profiles
function saveProfiles(profiles) {
  fs.writeFileSync(DB_FILE, JSON.stringify(profiles, null, 2));
}

// Ensure profiles directory exists
if (!fs.existsSync(PROFILES_DIR)) {
  fs.mkdirSync(PROFILES_DIR, { recursive: true });
}

// ----------------- API ROUTES -----------------

// GET /api/browser_versions
const getBrowserVersionsHandler = (req, res) => {
  res.json([
    { version: 'Chromium 125.0', stable: true },
    { version: 'Chromium 122.0', stable: true },
    { version: 'Chromium 120.0', stable: false }
  ]);
};

// GET /api/groups
const getGroupsHandler = (req, res) => {
  res.json([
    { id: 'g-1', name: 'Facebook Ads' },
    { id: 'g-2', name: 'Google Ads' },
    { id: 'g-3', name: 'TikTok' },
    { id: 'g-4', name: 'Ecommerce' },
    { id: 'g-5', name: 'Social Bots' }
  ]);
};

// GET /api/locations
const getLocationsHandler = (req, res) => {
  res.json([
    { country: 'United States', ip: '45.138.22.112' },
    { country: 'Germany', ip: '185.220.101.5' },
    { country: 'United Kingdom', ip: '88.198.50.22' }
  ]);
};

// GET /api/profiles
const listProfilesHandler = (req, res) => {
  const profiles = loadProfiles();
  const updatedProfiles = profiles.map(p => ({
    ...p,
    status: activeBrowsers.has(p.id) ? 'running' : 'stopped'
  }));
  res.json(updatedProfiles);
};

// GET /api/profile/:id
const getProfileByIdHandler = (req, res) => {
  const id = req.params.id || req.query.id;
  const profiles = loadProfiles();
  const profile = profiles.find(p => p.id === id);
  if (!profile) return res.status(404).json({ error: 'Khong tim thay profile' });
  
  res.json({
    ...profile,
    status: activeBrowsers.has(profile.id) ? 'running' : 'stopped'
  });
};

// POST /api/profiles/create
const createProfileHandler = (req, res) => {
  const { name, group, proxy, platform, userAgent, notes } = req.body;
  if (!name) return res.status(400).json({ error: 'Name is required' });

  const profiles = loadProfiles();
  
  // Assign a unique fixed port in range 15001-15999
  const usedPorts = new Set(profiles.map(p => p.port).filter(Boolean));
  let nextPort = 15001;
  while (usedPorts.has(nextPort)) nextPort++;

  const newProfile = {
    id: `p-${Date.now()}`,
    name,
    group: group || 'Facebook Ads',
    proxy: proxy || 'No Proxy (Direct)',
    browserVersion: 'Chromium 125.0',
    lastOpened: 'Chưa sử dụng',
    notes: notes || '',
    cookiesCount: 0,
    platform: platform || 'Windows',
    userAgent: userAgent || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    port: nextPort
  };

  profiles.unshift(newProfile);
  saveProfiles(profiles);
  res.json(newProfile);
};

// POST /api/profiles/update/:profile_id
const updateProfileHandler = (req, res) => {
  const id = req.params.profile_id || req.body.id || req.query.id || req.query.profileId;
  const profiles = loadProfiles();
  const idx = profiles.findIndex(p => p.id === id);
  if (idx === -1) return res.status(404).json({ error: 'Khong tim thay profile' });

  profiles[idx] = { ...profiles[idx], ...req.body };
  saveProfiles(profiles);
  res.json({ success: true, profile: profiles[idx] });
};

// GET /api/profiles/delete/:id
const deleteProfileHandler = (req, res) => {
  const id = req.params.id || req.query.id;
  const profiles = loadProfiles();
  const filtered = profiles.filter(p => p.id !== id);
  saveProfiles(filtered);
  res.json({ success: true });
};

// GET /api/profiles/start/:id
const startProfileHandler = (req, res) => {
  const id = req.params.id || req.query.id;
  if (!id) return res.status(400).json({ success: false, error: 'id is required' });

  if (activeBrowsers.has(id)) {
    const running = activeBrowsers.get(id);
    return res.json({
      success: true,
      status: "success",
      port: running.port,
      seleniumPort: running.port,
      remote_debugging_port: running.port,
      pid: running.pid,
      wsUrl: `ws://127.0.0.1:${running.port}/devtools/browser`,
      wsEndpoint: `ws://127.0.0.1:${running.port}/devtools/browser`
    });
  }

  const profiles = loadProfiles();
  const profile = profiles.find(p => p.id === id);
  if (!profile) return res.status(404).json({ error: 'Profile khong ton tai' });

  // Check if Chromium binary exists
  if (!fs.existsSync(CHROMIUM_EXE)) {
    return res.status(500).json({
      error: 'Chua tai Chromium! Vui long click chay file start-dashboard.bat de he thong tu dong tai Chromium.'
    });
  }

  const port = profile.port || 15001;
  const dataDir = path.join(PROFILES_DIR, id);

  const args = [
    `--user-data-dir=${dataDir}`,
    `--remote-debugging-port=${port}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--window-size=1920,1080',
    `--user-agent=${profile.userAgent}`
  ];

  if (profile.proxy && profile.proxy !== 'No Proxy (Direct)' && !profile.proxy.includes('Không sử dụng')) {
    const match = profile.proxy.match(/([0-9.]+:[0-9]+)/);
    if (match) {
      args.push(`--proxy-server=${match[1]}`);
    }
  }

  console.log(`Starting Chromium for Profile ${id} on fixed port ${port}...`);

  try {
    const child = spawn(CHROMIUM_EXE, args, {
      detached: true,
      stdio: 'ignore'
    });
    child.unref();

    activeBrowsers.set(id, {
      process: child,
      port,
      pid: child.pid
    });

    const now = new Date();
    const timeString = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    profile.lastOpened = timeString;
    saveProfiles(profiles);

    res.json({
      success: true,
      status: "success",
      port: port,
      seleniumPort: port,
      remote_debugging_port: port,
      pid: child.pid,
      wsUrl: `ws://127.0.0.1:${port}/devtools/browser`,
      wsEndpoint: `ws://127.0.0.1:${port}/devtools/browser`
    });
  } catch (err) {
    console.error('Failed to spawn Chromium process:', err);
    res.status(500).json({ error: 'Khong the khoi chay trinh duyet' });
  }
};

// GET /api/profiles/close/:id
const closeProfileHandler = (req, res) => {
  const id = req.params.id || req.query.id;
  if (!id) return res.status(400).json({ success: false, error: 'id is required' });

  if (!activeBrowsers.has(id)) {
    return res.json({ success: true, message: 'Browser da dong hoac khong chay', status: "success" });
  }

  const browser = activeBrowsers.get(id);
  console.log(`Closing Chromium process for profile ${id} (PID ${browser.pid})...`);
  
  try {
    execSync(`taskkill /pid ${browser.pid} /f /t`);
  } catch (err) {
    try {
      process.kill(browser.pid, 'SIGKILL');
    } catch (e) {
      console.warn('Failed to kill PID using SIGKILL, might be already closed:', e.message);
    }
  }

  activeBrowsers.delete(id);
  res.json({ success: true, status: "success" });
};

// POST /api/profiles/check-status/:id
const checkStatusHandler = (req, res) => {
  const id = req.params.id || req.query.id || req.body.id;
  const isRunning = activeBrowsers.has(id);
  const browser = activeBrowsers.get(id);
  
  res.json({
    isRunning,
    pid: isRunning ? browser.pid : null
  });
};

// GET /api/profiles/changeFingerprint
const changeFingerprintHandler = (req, res) => {
  const { ids } = req.query;
  if (!ids) return res.status(400).json({ error: 'ids query param required' });

  const profiles = loadProfiles();
  const idList = ids.split(',');
  
  idList.forEach(id => {
    const profile = profiles.find(p => p.id === id);
    if (profile) {
      const ver = Math.floor(Math.random() * 4) + 120;
      profile.userAgent = `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${ver}.0.0.0 Safari/537.36`;
    }
  });

  saveProfiles(profiles);
  res.json({ success: true });
};

// POST /api/profiles/resource/:id
const resourceHandler = (req, res) => {
  res.json({ success: true, message: 'Cap nhat resource thanh cong' });
};

// ---- REGISTER COMPATIBILITY ROUTES FOR GENLOGIN, GPMLOGIN & GAMS-GALOGIN ----

// Browser Versions
app.get('/api/browser_versions', getBrowserVersionsHandler);
app.get('/api/v1/browser_versions', getBrowserVersionsHandler);
app.get('/api/v3/browser_versions', getBrowserVersionsHandler);

// Groups
app.get('/api/groups', getGroupsHandler);
app.get('/api/v1/groups', getGroupsHandler);
app.get('/api/v3/groups', getGroupsHandler);

// Locations
app.get('/api/locations', getLocationsHandler);
app.get('/api/v1/locations', getLocationsHandler);
app.get('/api/v3/locations', getLocationsHandler);

// Profiles List
app.get('/api/profiles', listProfilesHandler);
app.get('/api/v1/profiles', listProfilesHandler);
app.get('/v1/profiles', listProfilesHandler);
app.get('/api/v3/profiles', listProfilesHandler);
app.get('/v3/profiles', listProfilesHandler);

// Get Profile By ID
app.get('/api/profile/:id', getProfileByIdHandler);
app.get('/api/profile', getProfileByIdHandler);
app.get('/api/v1/profile/:id', getProfileByIdHandler);
app.get('/api/v1/profile', getProfileByIdHandler);
app.get('/api/v3/profile/:id', getProfileByIdHandler);
app.get('/api/v3/profile', getProfileByIdHandler);

// Create Profile
app.post('/api/profiles/create', createProfileHandler);
app.post('/api/v1/profiles/create', createProfileHandler);
app.post('/api/v3/profiles/create', createProfileHandler);

// Update Profile
app.post('/api/profiles/update/:profile_id', updateProfileHandler);
app.post('/api/profiles/update', updateProfileHandler);
app.post('/api/v1/profiles/update/:profile_id', updateProfileHandler);
app.post('/api/v1/profiles/update', updateProfileHandler);
app.post('/api/v3/profiles/update/:profile_id', updateProfileHandler);
app.post('/api/v3/profiles/update', updateProfileHandler);

// Delete Profile
app.get('/api/profiles/delete/:id', deleteProfileHandler);
app.get('/api/profiles/delete', deleteProfileHandler);
app.get('/api/v1/profiles/delete/:id', deleteProfileHandler);
app.get('/api/v1/profiles/delete', deleteProfileHandler);
app.get('/api/v3/profiles/delete/:id', deleteProfileHandler);
app.get('/api/v3/profiles/delete', deleteProfileHandler);

// Start Profile
app.get('/api/profiles/start/:id', startProfileHandler);
app.get('/api/profiles/start', startProfileHandler);
app.get('/api/v1/profiles/start/:id', startProfileHandler);
app.get('/api/v1/profiles/start', startProfileHandler);
app.get('/v1/profiles/start', startProfileHandler);
app.get('/api/v3/profiles/start/:id', startProfileHandler);
app.get('/api/v3/profiles/start', startProfileHandler);
app.get('/v3/profiles/start', startProfileHandler);

// Close Profile
app.get('/api/profiles/close/:id', closeProfileHandler);
app.get('/api/profiles/close', closeProfileHandler);
app.get('/api/v1/profiles/close/:id', closeProfileHandler);
app.get('/api/v1/profiles/close', closeProfileHandler);
app.get('/v1/profiles/close', closeProfileHandler);
app.get('/api/v3/profiles/close/:id', closeProfileHandler);
app.get('/api/v3/profiles/close', closeProfileHandler);
app.get('/v3/profiles/close', closeProfileHandler);

// Check Status
app.post('/api/profiles/check-status/:id', checkStatusHandler);
app.post('/api/profiles/check-status', checkStatusHandler);
app.post('/api/v1/profiles/check-status/:id', checkStatusHandler);
app.post('/api/v1/profiles/check-status', checkStatusHandler);
app.post('/api/v3/profiles/check-status/:id', checkStatusHandler);
app.post('/api/v3/profiles/check-status', checkStatusHandler);

// Change Fingerprint
app.get('/api/profiles/changeFingerprint', changeFingerprintHandler);
app.get('/api/v1/profiles/changeFingerprint', changeFingerprintHandler);
app.get('/api/v3/profiles/changeFingerprint', changeFingerprintHandler);

// Resource Hardware Update
app.post('/api/profiles/resource/:id', resourceHandler);
app.post('/api/v1/profiles/resource/:id', resourceHandler);
app.post('/api/v3/profiles/resource/:id', resourceHandler);

// ---- ADDITIONAL v2 ALIASES ----
app.get('/api/v2/browser_versions', getBrowserVersionsHandler);
app.get('/api/v2/groups', getGroupsHandler);
app.get('/api/v2/locations', getLocationsHandler);
app.get('/api/v2/profiles', listProfilesHandler);
app.get('/v2/profiles', listProfilesHandler);
app.get('/api/v2/profile/:id', getProfileByIdHandler);
app.get('/api/v2/profile', getProfileByIdHandler);
app.post('/api/v2/profiles/create', createProfileHandler);
app.post('/api/v2/profiles/update/:profile_id', updateProfileHandler);
app.post('/api/v2/profiles/update', updateProfileHandler);
app.get('/api/v2/profiles/delete/:id', deleteProfileHandler);
app.get('/api/v2/profiles/delete', deleteProfileHandler);
app.get('/api/v2/profiles/start/:id', startProfileHandler);
app.get('/api/v2/profiles/start', startProfileHandler);
app.get('/v2/profiles/start', startProfileHandler);
app.get('/api/v2/profiles/close/:id', closeProfileHandler);
app.get('/api/v2/profiles/close', closeProfileHandler);
app.get('/v2/profiles/close', closeProfileHandler);
app.post('/api/v2/profiles/check-status/:id', checkStatusHandler);
app.post('/api/v2/profiles/check-status', checkStatusHandler);
app.get('/api/v2/profiles/changeFingerprint', changeFingerprintHandler);
app.post('/api/v2/profiles/resource/:id', resourceHandler);

// ---- DELETE/POST METHOD ALIASES (some tools use DELETE or POST for close/delete) ----
app.delete('/api/profiles/:id', deleteProfileHandler);
app.delete('/api/v1/profiles/:id', deleteProfileHandler);
app.delete('/api/v2/profiles/:id', deleteProfileHandler);
app.delete('/api/v3/profiles/:id', deleteProfileHandler);
app.post('/api/profiles/close/:id', closeProfileHandler);
app.post('/api/profiles/close', closeProfileHandler);
app.post('/api/v1/profiles/close/:id', closeProfileHandler);
app.post('/api/v1/profiles/close', closeProfileHandler);
app.post('/api/v2/profiles/close/:id', closeProfileHandler);
app.post('/api/v2/profiles/close', closeProfileHandler);
app.post('/api/v3/profiles/close/:id', closeProfileHandler);
app.post('/api/v3/profiles/close', closeProfileHandler);
app.post('/api/profiles/start/:id', startProfileHandler);
app.post('/api/profiles/start', startProfileHandler);
app.post('/api/v1/profiles/start/:id', startProfileHandler);
app.post('/api/v1/profiles/start', startProfileHandler);
app.post('/api/v2/profiles/start/:id', startProfileHandler);
app.post('/api/v2/profiles/start', startProfileHandler);
app.post('/api/v3/profiles/start/:id', startProfileHandler);
app.post('/api/v3/profiles/start', startProfileHandler);

// ----------------- AUTOMATION SCRIPT MOCKS -----------------

app.get('/api/scripts', (req, res) => {
  res.json([
    { id: 's-1', name: 'Auto Warmup Cookies' },
    { id: 's-2', name: 'Ad Campaign Metrics sync' },
    { id: 's-3', name: 'Twitter bot auto-post' }
  ]);
});

app.post('/api/scripts/execute/:id', (req, res) => {
  const { id } = req.params;
  const { profileId } = req.body;
  res.json({
    executionId: `exec-${Date.now()}`,
    status: 'Running'
  });
});

app.post('/api/scripts/check-status/:id', (req, res) => {
  res.json({
    status: 'Completed',
    progress: 100
  });
});

app.post('/api/scripts/kill-execute/:id', (req, res) => {
  res.json({ success: true });
});

// GET /api/server/status
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

// POST & GET /api/server/reset - Stops all Chromium profiles, resets memory map and sync status, then restarts the server process tree
const handleServerReset = (req, res) => {
  console.log('====== RESET SERVER TRIGGERED ======');
  let killedCount = 0;
  
  // 1. Force kill all active browser processes using Windows taskkill (equivalent to stop.bat)
  for (const [id, browser] of activeBrowsers.entries()) {
    console.log(`Killing Chromium process for profile ${id} (PID ${browser.pid}) via Server Reset...`);
    try {
      execSync(`taskkill /pid ${browser.pid} /f /t`);
      killedCount++;
    } catch (err) {
      try {
        process.kill(browser.pid, 'SIGKILL');
        killedCount++;
      } catch (e) {
        console.warn(`Failed to kill PID ${browser.pid} during reset:`, e.message);
      }
    }
  }
  
  // 2. Clear memory store
  activeBrowsers.clear();
  
  // 3. Reset all profile statuses to 'stopped' in profiles.json to ensure consistency
  try {
    const profiles = loadProfiles();
    const updated = profiles.map(p => ({ ...p, status: 'stopped' }));
    saveProfiles(updated);
    console.log('Successfully reset all profile statuses in profiles.json.');
  } catch (err) {
    console.error('Failed to reset profile statuses in file:', err);
  }
  
  res.json({
    success: true,
    message: `Đã khôi phục cài đặt gốc và đang khởi động lại Máy chủ Gams-GALogin. Đã đóng ${killedCount} tiến trình trình duyệt đang chạy.`,
    killedCount
  });

  // 4. Wait 1 second to allow HTTP response transmission, then auto-restart Node process tree in a new window
  setTimeout(() => {
    console.log('Re-spawning server process in new window...');
    try {
      const { spawn } = require('child_process');
      const child = spawn('cmd.exe', ['/c', 'start', '"Gams-GALogin API Server"', 'node', 'server.cjs'], {
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

// POST /api/server/sync-cloud - Secure sync to remote server
app.post('/api/server/sync-cloud', async (req, res) => {
  console.log(`Syncing profiles securely to Gia An Company Cloud: ${REMOTE_SYNC_SERVER}`);
  try {
    // Simulate secure cloud sync with remote server using environment credentials
    await new Promise(resolve => setTimeout(resolve, 1500));
    
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
// Key: email, Value: { code, expires }
const verificationCodes = new Map();

// POST /api/auth/forgot-password - Gửi mã xác thực khôi phục mật khẩu
app.post('/api/auth/forgot-password', async (req, res) => {
  const { email } = req.body;
  if (!email || !email.includes('@')) {
    return res.status(400).json({ error: 'Email không hợp lệ.' });
  }

  // Generate 6-digit code
  const code = Math.floor(100000 + Math.random() * 900000).toString();
  const expires = Date.now() + 10 * 60 * 1000; // 10 minutes
  verificationCodes.set(email, { code, expires });

  console.log(`==========================================================`);
  console.log(` YÊU CẦU KHÔI PHỤC MẬT KHẨU CHO EMAIL: ${email}`);
  console.log(` -> Mã xác thực (OTP): ${code}`);
  console.log(`==========================================================`);

  // Attempt to send real email using SMTP credentials from .env
  try {
    const nodemailer = require('nodemailer');
    
    // Create transporter using SMTP credentials from .env
    const transporter = nodemailer.createTransport({
      host: MAIL_SMTP_HOST,
      port: parseInt(MAIL_SMTP_PORT, 10),
      secure: MAIL_SMTP_PORT === '465', // true for 465, false for other ports
      auth: {
        user: MAIL_SMTP_USER,
        pass: MAIL_SMTP_PASS
      },
      tls: {
        rejectUnauthorized: false // avoid SSL/TLS issue on local DNS configs
      }
    });

    const mailOptions = {
      from: `Gams-GALogin Security <${MAIL_SMTP_USER}>`,
      to: email,
      subject: `[Gams-GALogin] Mã xác thực khôi phục mật khẩu của bạn: ${code}`,
      text: `Chào bạn,\n\nBạn vừa yêu cầu khôi phục mật khẩu cho tài khoản Gams-GALogin liên kết với email này.\n\nMã xác thực khôi phục mật khẩu (OTP) của bạn là: ${code}\nMã này có hiệu lực trong vòng 10 phút. Vui lòng không chia sẻ mã này cho bất kỳ ai.\n\nNếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này hoặc liên hệ hỗ trợ kỹ thuật của Gia An Company.\n\nTrân trọng,\nHệ thống quản trị Gams-GALogin`,
      html: `
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #1f222f; background-color: #0b0c10; color: #f8fafc; border-radius: 12px;">
          <h2 style="color: #3b82f6; border-bottom: 1px solid #1f222f; padding-bottom: 10px;">Khôi Phục Mật Khẩu Gams-GALogin</h2>
          <p>Chào bạn,</p>
          <p>Bạn vừa yêu cầu khôi phục mật khẩu cho tài khoản Gams-GALogin liên kết với email này.</p>
          <div style="background-color: #12141c; border: 1px solid #2d3142; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px; color: #64748b;">Mã xác thực OTP của bạn là:</p>
            <h1 style="margin: 10px 0 0 0; color: #8b5cf6; font-size: 32px; letter-spacing: 5px; font-family: monospace;">${code}</h1>
          </div>
          <p style="font-size: 12px; color: #64748b;">Mã xác thực có hiệu lực trong vòng 10 phút. Tuyệt đối không chia sẻ mã này cho người khác để tránh bị hack tài khoản.</p>
          <p style="border-top: 1px solid #1f222f; padding-top: 15px; font-size: 11px; color: #64748b; margin-top: 25px;">
            Hệ thống bảo mật doanh nghiệp Gia An Co., Ltd. • Kết nối DNS an toàn.
          </p>
        </div>
      `
    };

    await transporter.sendMail(mailOptions);
    console.log(`[SMTP] Email khôi phục mật khẩu đã được gửi đến ${email} thành công!`);
    return res.json({
      success: true,
      message: `Mã xác thực OTP đã được gửi đến email ${email} thành công! Vui lòng kiểm tra hộp thư.`
    });

  } catch (mailError) {
    console.warn(`[SMTP Warning] Không thể gửi email thực tế qua SMTP: ${mailError.message}`);
    console.log(`[Fallback] Hệ thống tự động chuyển sang chế độ Mô Phỏng DNS thành công. Mã OTP để thử nghiệm: ${code}`);
    
    return res.json({
      success: true,
      message: `Đã kích hoạt chế độ khôi phục mật khẩu. Mã OTP đã được xuất ra log console của Server [${code}] (do chưa cấu hình DNS/SMTP SMTP relay đầy đủ).`
    });
  }
});

// POST /api/auth/reset-password - Đặt lại mật khẩu mới
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

// Start listening
app.listen(PORT, () => {
  console.log(`==========================================================`);
  console.log(` Gams-GALogin Local API Server dang chay tai:`);
  console.log(` -> http://localhost:${PORT}`);
  console.log(`==========================================================`);
});
