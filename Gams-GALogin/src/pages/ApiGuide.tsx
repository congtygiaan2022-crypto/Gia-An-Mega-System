import React, { useState, useEffect } from 'react';
import {
  Code,
  Copy,
  Check,
  BookOpen,
  Cpu,
  Sparkles,
  RefreshCw,
  Play,
  Square,
  Wifi,
  WifiOff,
  Terminal,
  Globe,
  CircleDot,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ChevronRight
} from 'lucide-react';

const API_BASE = 'http://localhost:1020';

interface Profile {
  id: string;
  name: string;
  group: string;
  status: string;
  port?: number;
  proxy?: string;
}

interface StartResult {
  success: boolean;
  port?: number;
  pid?: number;
  wsUrl?: string;
  wsEndpoint?: string;
  error?: string;
}

interface ServerStatus {
  status: string;
  name?: string;
  version?: string;
  port?: number;
  profilesCount?: number;
}

export const ApiGuide: React.FC = () => {
  const [activeLangTab, setActiveLangTab] = useState<'curl' | 'nodejs' | 'python'>('nodejs');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Live tester state
  const [serverStatus, setServerStatus] = useState<ServerStatus | null>(null);
  const [serverOnline, setServerOnline] = useState<boolean | null>(null);
  const [serverChecking, setServerChecking] = useState(false);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [profilesLoading, setProfilesLoading] = useState(false);
  const [runningMap, setRunningMap] = useState<Record<string, StartResult>>({});
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (msg: string) => {
    const now = new Date().toLocaleTimeString('vi-VN');
    setLogs(prev => [`[${now}] ${msg}`, ...prev].slice(0, 50));
  };

  const checkServer = async () => {
    setServerChecking(true);
    addLog('Đang kiểm tra kết nối đến API Server...');
    try {
      const res = await fetch(`${API_BASE}/`, { signal: AbortSignal.timeout(4000) });
      if (res.ok) {
        const data = await res.json();
        setServerStatus(data);
        setServerOnline(true);
        addLog(`✅ Kết nối thành công! Server: ${data.name || 'Gams-GALogin'} v${data.version || '?'} | ${data.profilesCount ?? '?'} profiles`);
      } else {
        setServerOnline(false);
        addLog(`❌ Server phản hồi lỗi HTTP ${res.status}`);
      }
    } catch (e: unknown) {
      setServerOnline(false);
      const msg = e instanceof Error ? e.message : String(e);
      addLog(`❌ Không thể kết nối: ${msg}`);
    } finally {
      setServerChecking(false);
    }
  };

  const loadProfiles = async () => {
    setProfilesLoading(true);
    addLog('Đang tải danh sách profiles...');
    try {
      const res = await fetch(`${API_BASE}/api/profiles`, { signal: AbortSignal.timeout(5000) });
      if (res.ok) {
        const data = await res.json();
        setProfiles(data);
        addLog(`✅ Đã tải ${data.length} profile(s) thành công.`);
      } else {
        addLog(`❌ Lỗi tải profiles: HTTP ${res.status}`);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      addLog(`❌ Không thể tải profiles: ${msg}`);
    } finally {
      setProfilesLoading(false);
    }
  };

  const startProfile = async (profileId: string, profileName: string) => {
    setActionLoading(prev => ({ ...prev, [profileId]: true }));
    addLog(`▶ Đang khởi chạy profile [${profileName}]...`);
    try {
      const res = await fetch(`${API_BASE}/api/profiles/start/${profileId}`, { signal: AbortSignal.timeout(15000) });
      const data = await res.json();
      if (data.success) {
        setRunningMap(prev => ({ ...prev, [profileId]: data }));
        addLog(`✅ Profile [${profileName}] đã mở! Cổng debug: ${data.port} | PID: ${data.pid}`);
        addLog(`   wsUrl: ${data.wsUrl}`);
        // Update profile status
        setProfiles(prev => prev.map(p => p.id === profileId ? { ...p, status: 'running' } : p));
      } else {
        addLog(`❌ Không thể mở profile [${profileName}]: ${data.error || 'Lỗi không xác định'}`);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      addLog(`❌ Lỗi khi mở profile [${profileName}]: ${msg}`);
    } finally {
      setActionLoading(prev => ({ ...prev, [profileId]: false }));
    }
  };

  const closeProfile = async (profileId: string, profileName: string) => {
    setActionLoading(prev => ({ ...prev, [profileId]: true }));
    addLog(`⏹ Đang đóng profile [${profileName}]...`);
    try {
      const res = await fetch(`${API_BASE}/api/profiles/close/${profileId}`, { signal: AbortSignal.timeout(10000) });
      const data = await res.json();
      if (data.success) {
        setRunningMap(prev => {
          const newMap = { ...prev };
          delete newMap[profileId];
          return newMap;
        });
        setProfiles(prev => prev.map(p => p.id === profileId ? { ...p, status: 'stopped' } : p));
        addLog(`✅ Profile [${profileName}] đã đóng thành công.`);
      } else {
        addLog(`❌ Không thể đóng profile [${profileName}].`);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      addLog(`❌ Lỗi khi đóng profile [${profileName}]: ${msg}`);
    } finally {
      setActionLoading(prev => ({ ...prev, [profileId]: false }));
    }
  };

  useEffect(() => {
    checkServer();
  }, []);

  const apiPort = '1020';

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const curlCode = `# 1. Kiểm tra server đang hoạt động
curl http://localhost:${apiPort}/

# 2. Lấy danh sách profiles (bao gồm port debug cố định của từng profile)
curl http://localhost:${apiPort}/api/profiles

# 3. Mở trình duyệt cho profile có ID p-1 (port debug là cố định, không thay đổi)
curl http://localhost:${apiPort}/api/profiles/start/p-1

# Phản hồi:
# {
#   "success": true,
#   "port": 15001,          <- Cổng debug cố định của profile này
#   "pid": 5824,
#   "wsUrl": "ws://127.0.0.1:15001/devtools/browser",
#   "wsEndpoint": "ws://127.0.0.1:15001/devtools/browser"
# }

# 4. Đóng trình duyệt profile sau khi tự động hóa xong
curl http://localhost:${apiPort}/api/profiles/close/p-1`;

  const nodejsCode = `const puppeteer = require('puppeteer');

async function runAutomation() {
  const profileId = 'p-1'; // ID của profile (xem trong /api/profiles)
  const apiBase = 'http://localhost:${apiPort}';

  try {
    // 1. Gọi API mở trình duyệt - port debug là CỐ ĐỊNH cho mỗi profile
    console.log(\`[Gams-GA] Đang mở profile \${profileId}...\`);
    const response = await fetch(\`\${apiBase}/api/profiles/start/\${profileId}\`);
    const data = await response.json();

    if (!data.success) {
      throw new Error(\`Không thể mở profile: \${data.error}\`);
    }

    const wsUrl = data.wsUrl;
    console.log(\`[Gams-GA] Đã mở! Cổng debug: \${data.port} - PID: \${data.pid}\`);
    console.log(\`[Gams-GA] WebSocket URL: \${wsUrl}\`);

    // 2. Kết nối Puppeteer qua cổng CDP (Chrome DevTools Protocol)
    const browser = await puppeteer.connect({
      browserWSEndpoint: wsUrl
    });

    const pages = await browser.pages();
    const page = pages[0] || await browser.newPage();

    // 3. Thực hiện tự động hóa
    await page.goto('https://facebook.com', { waitUntil: 'domcontentloaded' });
    console.log('[Gams-GA] Trang đã tải:', await page.title());

    await new Promise(r => setTimeout(r, 3000));
    await browser.disconnect();

    // 4. Đóng trình duyệt an toàn
    await fetch(\`\${apiBase}/api/profiles/close/\${profileId}\`);
    console.log('[Gams-GA] Đã đóng profile thành công.');

  } catch (error) {
    console.error('[Error]', error.message);
  }
}

runAutomation();`;

  const pythonCode = `import requests
import asyncio
from playwright.async_api import async_playwright

async def run_automation():
    profile_id = "p-1"  # ID của profile (xem trong /api/profiles)
    api_base = "http://localhost:${apiPort}"

    try:
        # 1. Gọi API mở trình duyệt
        print(f"[Gams-GA] Đang mở profile {profile_id}...")
        res = requests.get(f"{api_base}/api/profiles/start/{profile_id}")
        data = res.json()

        if not data.get("success"):
            raise Exception(f"Không thể mở profile: {data.get('error')}")

        debug_port = data.get("port")   # Cổng debug CỐ ĐỊNH của profile này
        ws_url = data.get("wsUrl")
        print(f"[Gams-GA] Đã mở! Cổng debug: {debug_port}")
        print(f"[Gams-GA] WebSocket URL: {ws_url}")

        # 2. Kết nối Playwright qua CDP
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(ws_url)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()

            await page.goto("https://google.com")
            title = await page.title()
            print(f"[Gams-GA] Tiêu đề: {title}")
            
            await asyncio.sleep(3)
            await browser.close()

        # 3. Đóng trình duyệt qua API
        requests.get(f"{api_base}/api/profiles/close/{profile_id}")
        print("[Gams-GA] Đã đóng profile thành công.")

    except Exception as e:
        print(f"[Error] {e}")

asyncio.run(run_automation())`;

  const getCodeSnippet = () => {
    switch (activeLangTab) {
      case 'curl': return curlCode;
      case 'python': return pythonCode;
      case 'nodejs': default: return nodejsCode;
    }
  };

  const getLangLabel = () => {
    switch (activeLangTab) {
      case 'curl': return 'Shell / cURL';
      case 'python': return 'Python (Playwright)';
      case 'nodejs': return 'Node.js (Puppeteer)';
    }
  };

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-brand-blue/10 text-brand-blue border border-brand-blue/20">
              CỔNG KẾT NỐI {apiPort}
            </div>
            <span className="flex items-center gap-1 text-xs text-brand-purple font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              Sẵn sàng tích hợp
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-200 mt-1">Kết Nối API & Điều Khiển Trình Duyệt</h2>
          <p className="text-xs text-slate-500">Tích hợp phần mềm tự động hóa (Puppeteer, Playwright, Selenium, Python) với Gams-GALogin qua API.</p>
        </div>
      </div>

      {/* ======== LIVE SERVER STATUS CARD ======== */}
      <div className={`p-4 rounded-2xl border flex items-center gap-4 ${
        serverOnline === true
          ? 'bg-emerald-950/20 border-emerald-800/30'
          : serverOnline === false
          ? 'bg-red-950/20 border-red-800/30'
          : 'bg-slate-900/30 border-dark-border'
      }`}>
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${
          serverOnline === true ? 'bg-emerald-900/40' : serverOnline === false ? 'bg-red-900/40' : 'bg-slate-800/40'
        }`}>
          {serverOnline === true ? (
            <Wifi className="w-6 h-6 text-brand-emerald" />
          ) : serverOnline === false ? (
            <WifiOff className="w-6 h-6 text-brand-rose" />
          ) : (
            <Globe className="w-6 h-6 text-slate-500 animate-pulse" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-slate-200">API Server</span>
            <code className="text-xs font-mono text-slate-400 bg-slate-950/60 px-2 py-0.5 rounded">
              {API_BASE}
            </code>
            {serverOnline === true && (
              <span className="flex items-center gap-1 text-xs text-brand-emerald font-semibold">
                <CircleDot className="w-3 h-3 animate-pulse" /> Online
              </span>
            )}
            {serverOnline === false && (
              <span className="flex items-center gap-1 text-xs text-brand-rose font-semibold">
                <XCircle className="w-3 h-3" /> Offline
              </span>
            )}
          </div>
          {serverStatus && serverOnline && (
            <p className="text-xs text-slate-400 mt-0.5">
              {serverStatus.name} v{serverStatus.version} &bull; {serverStatus.profilesCount} profile(s) đang được quản lý
            </p>
          )}
          {serverOnline === false && (
            <p className="text-xs text-red-400 mt-0.5">
              Không thể kết nối đến server. Hãy đảm bảo file <code className="font-mono">server.cjs</code> đang chạy.
            </p>
          )}
        </div>
        <button
          onClick={checkServer}
          disabled={serverChecking}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 border border-dark-border hover:border-slate-600 text-slate-300 text-xs font-semibold transition-all cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${serverChecking ? 'animate-spin' : ''}`} />
          {serverChecking ? 'Đang kiểm tra...' : 'Kiểm tra kết nối'}
        </button>
      </div>

      {/* Notice Card - Updated with FIXED port info */}
      <div className="p-4 rounded-xl border border-brand-blue/20 bg-brand-blue/5 flex items-start gap-3">
        <CheckCircle2 className="w-5 h-5 text-brand-blue shrink-0 mt-0.5" />
        <div className="text-xs space-y-1">
          <p className="font-semibold text-slate-200">Kiến trúc cổng kết nối (Port Architecture):</p>
          <p className="text-slate-400 leading-relaxed">
            API Server lắng nghe tại cổng cố định <code className="text-brand-blue font-bold">http://localhost:{apiPort}</code>.
            Mỗi profile Chromium được gán một cổng debug <code className="text-slate-200">remote-debugging-port</code> cố định và duy nhất trong phạm vi{' '}
            <code className="text-brand-purple font-bold">15001 - 15999</code>.
            Cổng này <strong className="text-white">không thay đổi</strong> mỗi lần khởi động — bạn có thể lưu trữ và dùng lại mà không cần gọi API Start trước.
          </p>
        </div>
      </div>

      {/* ======== LIVE PROFILE TESTER ======== */}
      <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
        <div className="flex items-center justify-between border-b border-dark-border/60 pb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-brand-purple" />
            <h3 className="text-sm font-bold text-slate-300">Kiểm Tra Kết Nối Trực Tiếp (Live Tester)</h3>
          </div>
          <button
            onClick={loadProfiles}
            disabled={profilesLoading || serverOnline === false}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-blue/10 border border-brand-blue/25 text-brand-blue text-xs font-semibold hover:bg-brand-blue/20 transition-all cursor-pointer disabled:opacity-40"
          >
            <RefreshCw className={`w-3 h-3 ${profilesLoading ? 'animate-spin' : ''}`} />
            {profilesLoading ? 'Đang tải...' : 'Tải danh sách profiles'}
          </button>
        </div>

        {profiles.length === 0 ? (
          <div className="text-center py-8 text-slate-600 text-xs space-y-2">
            {serverOnline === false ? (
              <>
                <AlertTriangle className="w-8 h-8 mx-auto text-brand-rose/40" />
                <p>Server chưa kết nối. Hãy khởi động <code>server.cjs</code> trước.</p>
              </>
            ) : (
              <>
                <CircleDot className="w-8 h-8 mx-auto text-slate-700" />
                <p>Nhấn &quot;Tải danh sách profiles&quot; để xem và kiểm tra các profile</p>
              </>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {profiles.map(profile => {
              const isRunning = profile.status === 'running' || !!runningMap[profile.id];
              const result = runningMap[profile.id];
              const isLoading = actionLoading[profile.id];
              return (
                <div
                  key={profile.id}
                  className={`p-3 rounded-xl border transition-all ${
                    isRunning
                      ? 'border-brand-emerald/30 bg-emerald-950/10'
                      : 'border-dark-border/60 bg-slate-950/30'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className={`w-2 h-2 rounded-full shrink-0 ${isRunning ? 'bg-brand-emerald animate-pulse' : 'bg-slate-700'}`} />
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-slate-200 truncate">{profile.name}</p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[10px] text-slate-500">{profile.id}</span>
                          {profile.port && (
                            <span className="text-[10px] text-brand-purple font-mono">
                              Debug Port: {profile.port}
                            </span>
                          )}
                          {profile.group && (
                            <span className="text-[10px] text-slate-600 border border-slate-800 px-1.5 rounded">
                              {profile.group}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {isRunning && result && (
                        <button
                          onClick={() => copyToClipboard(result.wsUrl || '', `ws-${profile.id}`)}
                          className="flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-900 border border-dark-border text-[10px] text-slate-400 hover:text-slate-200 transition-all cursor-pointer"
                          title="Copy WebSocket URL"
                        >
                          {copiedId === `ws-${profile.id}` ? (
                            <><Check className="w-3 h-3 text-brand-emerald" /><span className="text-brand-emerald">Đã copy</span></>
                          ) : (
                            <><Copy className="w-3 h-3" /><span className="font-mono">ws:{result.port}</span></>
                          )}
                        </button>
                      )}
                      {isRunning ? (
                        <button
                          onClick={() => closeProfile(profile.id, profile.name)}
                          disabled={isLoading}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-950/30 border border-brand-rose/30 text-brand-rose text-xs font-semibold hover:bg-red-950/50 transition-all cursor-pointer disabled:opacity-50"
                        >
                          {isLoading ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Square className="w-3 h-3" />}
                          Đóng
                        </button>
                      ) : (
                        <button
                          onClick={() => startProfile(profile.id, profile.name)}
                          disabled={isLoading || serverOnline === false}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-blue/10 border border-brand-blue/30 text-brand-blue text-xs font-semibold hover:bg-brand-blue/20 transition-all cursor-pointer disabled:opacity-50"
                        >
                          {isLoading ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                          Mở trình duyệt
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Running details */}
                  {isRunning && result && (
                    <div className="mt-2 p-2 rounded-lg bg-slate-950/60 border border-dark-border/40 space-y-1">
                      <div className="flex items-center gap-2 text-[10px]">
                        <span className="text-slate-500">Debug Port:</span>
                        <code className="text-brand-purple font-bold">{result.port}</code>
                        <span className="text-slate-600">|</span>
                        <span className="text-slate-500">PID:</span>
                        <code className="text-slate-300">{result.pid}</code>
                      </div>
                      <div className="flex items-start gap-2 text-[10px]">
                        <span className="text-slate-500 shrink-0">wsUrl:</span>
                        <code className="text-brand-blue break-all font-mono">{result.wsUrl}</code>
                        <button
                          onClick={() => copyToClipboard(result.wsUrl || '', `wsurl-${profile.id}`)}
                          className="shrink-0 cursor-pointer"
                        >
                          {copiedId === `wsurl-${profile.id}` ? (
                            <Check className="w-3 h-3 text-brand-emerald" />
                          ) : (
                            <Copy className="w-3 h-3 text-slate-500 hover:text-slate-300" />
                          )}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Activity Logs */}
        {logs.length > 0 && (
          <div className="mt-2 space-y-1">
            <p className="text-[10px] text-slate-600 font-semibold uppercase tracking-wider flex items-center gap-1">
              <ChevronRight className="w-3 h-3" /> Nhật ký hoạt động
            </p>
            <div className="bg-slate-950 rounded-xl border border-dark-border p-3 font-mono text-[10px] max-h-36 overflow-y-auto space-y-0.5">
              {logs.map((log, i) => (
                <div key={i} className={`${
                  log.includes('✅') ? 'text-brand-emerald' :
                  log.includes('❌') ? 'text-brand-rose' :
                  log.includes('wsUrl') || log.includes('ws:') ? 'text-brand-blue' :
                  'text-slate-400'
                }`}>
                  {log}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Main Grid: Docs + Code Examples */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: API Endpoints */}
        <div className="lg:col-span-1 space-y-5">
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
            <div className="flex items-center gap-2 border-b border-dark-border/60 pb-3">
              <BookOpen className="w-4 h-4 text-brand-blue" />
              <h3 className="text-sm font-bold text-slate-300">API Endpoints Cốt Lõi</h3>
            </div>

            <div className="space-y-3">
              {[
                { method: 'GET', path: '/', desc: 'Kiểm tra trạng thái server, thông tin phiên bản.' },
                { method: 'GET', path: '/api/profiles', desc: 'Lấy toàn bộ danh sách profiles và cổng debug cố định của từng profile.' },
                { method: 'GET', path: '/api/profiles/start/:id', desc: 'Mở trình duyệt. Trả về cổng debug cố định, PID và wsUrl.' },
                { method: 'GET', path: '/api/profiles/close/:id', desc: 'Đóng tiến trình trình duyệt an toàn và đồng bộ dữ liệu.' },
                { method: 'POST', path: '/api/profiles/create', desc: 'Tạo profile mới, tự động gán cổng debug cố định.' },
                { method: 'POST', path: '/api/profiles/update/:id', desc: 'Cập nhật thông tin proxy, user-agent, ghi chú của profile.' },
                { method: 'GET', path: '/api/profiles/delete/:id', desc: 'Xóa profile (cũng hỗ trợ DELETE method).' },
              ].map((ep, i) => (
                <div key={i} className="space-y-1 p-3 rounded-xl bg-slate-950/40 border border-dark-border/40">
                  <div className="flex items-center gap-2">
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border ${
                      ep.method === 'GET'
                        ? 'bg-brand-emerald/10 text-brand-emerald border-brand-emerald/20'
                        : 'bg-brand-blue/10 text-brand-blue border-brand-blue/20'
                    }`}>
                      {ep.method}
                    </span>
                    <span className="font-mono text-xs font-semibold text-slate-300">{ep.path}</span>
                  </div>
                  <p className="text-[11px] text-slate-500">{ep.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Flow Steps */}
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
            <div className="flex items-center gap-2 border-b border-dark-border/60 pb-3">
              <Cpu className="w-4 h-4 text-brand-purple" />
              <h3 className="text-sm font-bold text-slate-300">Quy Trình Tích Hợp</h3>
            </div>
            <div className="space-y-3 relative">
              {[
                { title: 'Gọi API Start', desc: 'Mở profile và nhận wsUrl kết nối CDP (cổng debug cố định).' },
                { title: 'Kết nối Automation', desc: 'Dùng Puppeteer/Playwright kết nối vào trình duyệt qua wsUrl.' },
                { title: 'Thực hiện tự động hóa', desc: 'Điều khiển trang web, điền form, click, lấy dữ liệu...' },
                { title: 'Đóng Profile', desc: 'Gọi API close để lưu cookie và giải phóng tài nguyên hệ thống.' },
              ].map((step, i) => (
                <div key={i} className="flex gap-3 relative z-10">
                  <div className="w-6 h-6 rounded-full bg-slate-950 border border-dark-border flex items-center justify-center shrink-0 font-bold text-xs text-brand-blue">
                    {i + 1}
                  </div>
                  <div className="text-xxs text-slate-400">
                    <strong className="text-slate-300 block mb-0.5">{step.title}</strong>
                    {step.desc}
                  </div>
                </div>
              ))}
              <div className="absolute left-3 top-3 bottom-3 w-0.5 bg-slate-800 -z-10" />
            </div>
          </div>
        </div>

        {/* Right: Code Examples */}
        <div className="lg:col-span-2 space-y-5">
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-dark-border/60 pb-3">
              <div className="flex items-center gap-2">
                <Code className="w-4 h-4 text-brand-blue" />
                <h3 className="text-sm font-bold text-slate-300">Ví Dụ Code Tích Hợp</h3>
              </div>
              <div className="flex p-0.5 rounded-lg bg-slate-950 border border-dark-border self-start">
                {(['nodejs', 'python', 'curl'] as const).map(lang => (
                  <button
                    key={lang}
                    onClick={() => setActiveLangTab(lang)}
                    className={`px-3 py-1 rounded-md text-xxs font-semibold transition-all cursor-pointer ${
                      activeLangTab === lang
                        ? 'bg-brand-blue/10 text-brand-blue font-bold border border-brand-blue/25'
                        : 'text-slate-500 hover:text-slate-300 border border-transparent'
                    }`}
                  >
                    {lang === 'nodejs' ? 'Node.js' : lang === 'python' ? 'Python' : 'cURL'}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center bg-slate-950 px-4 py-2 rounded-t-xl border border-dark-border border-b-0">
                <span className="text-[10px] font-mono text-slate-500 font-semibold">{getLangLabel()}</span>
                <button
                  onClick={() => copyToClipboard(getCodeSnippet(), 'code-snippet')}
                  className="flex items-center gap-1.5 text-[10px] text-slate-500 hover:text-slate-200 transition-colors cursor-pointer bg-transparent border-0"
                >
                  {copiedId === 'code-snippet' ? (
                    <><Check className="w-3.5 h-3.5 text-brand-emerald" /><span className="text-brand-emerald font-bold">Đã sao chép!</span></>
                  ) : (
                    <><Copy className="w-3.5 h-3.5" /><span>Sao chép code</span></>
                  )}
                </button>
              </div>
              <pre className="p-4 rounded-b-xl border border-dark-border bg-slate-950 text-slate-300 font-mono text-xs overflow-x-auto leading-relaxed max-h-[500px]">
                <code>{getCodeSnippet()}</code>
              </pre>
            </div>

            <p className="text-[10px] text-slate-600 leading-normal">
              * Đảm bảo máy chủ API (server.cjs) đang chạy trên cổng {apiPort} trước khi thực thi code trên. Sử dụng Live Tester ở trên để kiểm tra kết nối ngay trong Dashboard.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
