import { create } from 'zustand';

const API_BASE = 'http://localhost:1020';

const PROXIES_STORAGE_KEY = 'gams_proxies_v1';

export interface ProxyConfig {
  type: 'Direct' | 'HTTP' | 'HTTPS' | 'SOCKS5' | 'PAC';
  host: string;
  port: string;
  username?: string;
  password?: string;
  pacUrl?: string;
}

export interface WindowSize {
  width: number;
  height: number;
  x: number;
  y: number;
}

export interface StartupConfig {
  mode: 'blank' | 'last_session' | 'urls';
  urls: string[];
}

export interface ExtensionItem {
  id: string;
  name: string;
  path?: string;
  enabled: boolean;
}

export interface BrowserProfile {
  id: string;
  name: string;
  status: 'running' | 'stopped' | 'starting' | 'error';
  proxy: string; // compatibility flat string
  proxyConfig: ProxyConfig;
  browserType: 'chromium' | 'chrome' | 'edge' | 'custom';
  executablePath: string;
  userAgent: string;
  windowSize: WindowSize;
  language: string;
  timezone: string;
  startupConfig: StartupConfig;
  downloadDir: string;
  extensions: ExtensionItem[];
  browserArguments: string[];
  notes: string;
  group: string;
  cookiesCount: number;
  platform: 'Windows' | 'macOS' | 'Linux';
  lastOpened: string;
  port?: number;
  pid?: number;
  hardwareConcurrency?: number;
  deviceMemory?: number;
  spoofFingerprints?: boolean;
  fallbackProxies?: ProxyConfig[];
}

export interface ProxyItem {
  id: string;
  host: string;
  port: number;
  type: 'HTTP' | 'SOCKS5';
  status: 'active' | 'inactive' | 'testing' | 'failed';
  speed?: number;
  group: string;
  username?: string;
  password?: string;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

export interface UserAgentItem {
  id: string;
  ua: string;
  platform: 'Windows' | 'macOS' | 'Linux';
}

export interface ProfileTemplate {
  id: string;
  name: string;
  browserType: 'chromium' | 'chrome' | 'edge' | 'custom';
  windowSize: WindowSize;
  language: string;
  timezone: string;
  proxyConfig: ProxyConfig;
  userAgentPolicy: 'Fixed' | 'Random' | 'Sequential';
  startupConfig: StartupConfig;
  extensions: ExtensionItem[];
  browserArguments: string[];
  hardwareConcurrency?: number;
  deviceMemory?: number;
  spoofFingerprints?: boolean;
}

interface AppState {
  // Navigation / Session
  activeTab: 'dashboard' | 'profiles' | 'proxies' | 'cookies' | 'automation' | 'settings' | 'account' | 'api-guide' | 'user-agents' | 'templates';
  isAuthenticated: boolean;
}

interface AppState {
  // Navigation / Session
  activeTab: 'dashboard' | 'profiles' | 'proxies' | 'cookies' | 'automation' | 'settings' | 'account' | 'api-guide' | 'user-agents' | 'templates';
  isAuthenticated: boolean;
  user: {
    name: string;
    email: string;
    avatar: string;
    role: string;
  } | null;
  
  // Search & Modals
  searchTerm: string;
  isCreateModalOpen: boolean;
  
  // App Data
  profiles: BrowserProfile[];
  proxies: ProxyItem[];
  userAgents: UserAgentItem[];
  templates: ProfileTemplate[];
  logs: LogEntry[];
  customGroups: string[];
  
  // System Monitor (Simulated global metrics)
  systemMetrics: {
    cpu: number;
    ram: number;
    networkSpeed: number;
    totalTraffic: string;
  };

  // Real-time resource metrics per running profile
  profileResources: Record<string, { cpu: number; ramBytes: number }>;

  // Server security status configuration
  serverStatus: {
    status: string;
    remoteSyncServer: string;
    mailDomain: string;
    mailSecurity: {
      smtpHost: string;
      smtpPort: string;
      smtpUser: string;
      isPasswordConfigured: boolean;
      isJwtConfigured: boolean;
      envIsolated: boolean;
    };
  } | null;
  
  // Actions
  setActiveTab: (tab: AppState['activeTab']) => void;
  setSearchTerm: (term: string) => void;
  setIsCreateModalOpen: (isOpen: boolean) => void;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<boolean>;
  logout: () => void;
  syncProfiles: () => Promise<void>;
  fetchServerStatus: () => Promise<void>;
  resetServer: () => Promise<{ success: boolean; message: string }>;
  syncCloud: () => Promise<{ success: boolean; message: string }>;
  forgotPassword: (email: string) => Promise<{ success: boolean; message: string }>;
  resetPassword: (email: string, code: string, newPassword: string) => Promise<{ success: boolean; message: string }>;
  
  // Profile Actions
  addProfile: (profile: Partial<BrowserProfile>) => Promise<void>;
  updateProfile: (id: string, updates: Partial<BrowserProfile>) => Promise<void>;
  deleteProfile: (id: string) => Promise<void>;
  launchProfile: (id: string, layoutOptions?: any) => Promise<void>;
  stopProfile: (id: string) => Promise<void>;
  cloneProfile: (id: string) => Promise<void>;
  startGroup: (groupName: string) => Promise<void>;
  stopGroup: (groupName: string) => Promise<void>;
  exportProfile: (id: string) => Promise<void>;
  importProfile: (base64Zip: string) => Promise<boolean>;

  // Profile Logs
  fetchProfileLogs: (id: string) => Promise<string>;
  clearProfileLogs: (id: string) => Promise<void>;

  // User Agent Manager Actions
  fetchUserAgents: () => Promise<void>;
  addUserAgent: (ua: string, platform: 'Windows' | 'macOS' | 'Linux') => Promise<void>;
  updateUserAgent: (id: string, ua: string, platform: 'Windows' | 'macOS' | 'Linux') => Promise<void>;
  deleteUserAgent: (id: string) => Promise<void>;
  importUserAgents: (type: 'text' | 'json', payload: string, platform?: 'Windows' | 'macOS' | 'Linux') => Promise<number>;

  // Template Manager Actions
  fetchTemplates: () => Promise<void>;
  createTemplate: (template: Partial<ProfileTemplate>) => Promise<void>;
  updateTemplate: (id: string, updates: Partial<ProfileTemplate>) => Promise<void>;
  deleteTemplate: (id: string) => Promise<void>;

  // Window Manager Actions
  arrangeWindows: (ids: string[], layoutMode: string) => Promise<void>;
  
  // Proxy Actions
  fetchProxies: () => void;
  addProxy: (proxy: Omit<ProxyItem, 'id' | 'status'>) => void;
  deleteProxy: (id: string) => void;
  testProxy: (id: string) => Promise<void>;
  testAllProxies: () => Promise<void>;

  bulkCreateProfiles: (opts: {
    prefix: string;
    count: number;
    group: string;
    templateId?: string;
    proxyIds: string[];
    startIndex?: number;
  }) => Promise<number>;
  bulkCloneProfiles: (ids: string[]) => Promise<void>;
  bulkAssignProxies: (profileIds: string[], proxyIds: string[], assignMode: 'single' | 'round-robin' | 'all-fallback') => Promise<void>;
  bulkRenameProfiles: (ids: string[], prefix: string, startIndex: number) => Promise<void>;
  
  // Group Actions
  addCustomGroup: (name: string) => void;
  deleteCustomGroup: (name: string) => void;
  bulkAssignGroup: (profileIds: string[], groupName: string) => Promise<void>;
  
  // Cookie Actions
  importCookies: (profileId: string, cookiesText: string) => { success: boolean; count: number; error?: string };
  
  // Logging
  addLog: (message: string, type?: LogEntry['type']) => void;
  clearLogs: () => void;
  
  // Metrics Tick
  updateMetrics: () => void;
}

// Proxy persistence helpers
const loadProxiesFromStorage = (): ProxyItem[] => {
  try {
    const raw = localStorage.getItem(PROXIES_STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch (e) {}
  // Default mock proxies (only shown on first run)
  return [
    { id: 'pr-1', host: '45.138.22.112', port: 8000, type: 'HTTP', status: 'active', speed: 85, group: 'Proxy Dân cư US' },
    { id: 'pr-2', host: '185.220.101.5', port: 9050, type: 'SOCKS5', status: 'active', speed: 120, group: 'Proxy Châu Âu' },
    { id: 'pr-3', host: '88.198.50.22', port: 3128, type: 'HTTP', status: 'active', speed: 95, group: 'Proxy Dân cư UK' },
    { id: 'pr-4', host: '194.67.212.87', port: 1080, type: 'SOCKS5', status: 'inactive', speed: 0, group: 'Khu vực SNG' }
  ];
};

const saveProxiesToStorage = (proxies: ProxyItem[]) => {
  try {
    localStorage.setItem(PROXIES_STORAGE_KEY, JSON.stringify(proxies));
  } catch (e) {}
};

const loadCustomGroupsFromStorage = (): string[] => {
  try {
    const raw = localStorage.getItem('gams_custom_groups');
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch (e) {}
  return ['Facebook Ads', 'Google Accounts', 'TikTok Accounts'];
};

// Initial Mock Proxies — loaded from localStorage or defaults
const initialProxies: ProxyItem[] = loadProxiesFromStorage();

// Initial Logs
const initialLogs: LogEntry[] = [
  { id: 'l-1', timestamp: '05:00:12', message: 'Hệ thống Gams-GALogin khởi động thành công.', type: 'info' },
  { id: 'l-2', timestamp: '05:01:45', message: 'Tải thành công các module OOP của Gams-GALogin API.', type: 'success' }
];

// Cookie Helpers
function setCookie(name: string, value: string, days: number) {
  const expires = new Date();
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
  document.cookie = `${name}=${encodeURIComponent(value)};expires=${expires.toUTCString()};path=/;SameSite=Strict`;
}

function getCookie(name: string): string | null {
  const nameEQ = name + "=";
  const ca = document.cookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) return decodeURIComponent(c.substring(nameEQ.length, c.length));
  }
  return null;
}

function eraseCookie(name: string) {
  document.cookie = `${name}=; Max-Age=-99999999;path=/;SameSite=Strict`;
}

const getInitialSession = (): { isAuthenticated: boolean; user: AppState['user'] } => {
  try {
    const sessionStr = getCookie('gams_session');
    if (sessionStr) {
      const user = JSON.parse(sessionStr);
      if (user && user.email) {
        return { isAuthenticated: true, user };
      }
    }
  } catch (e) {
    console.error('Failed to parse initial session', e);
  }
  return { isAuthenticated: false, user: null };
};

const initialSession = getInitialSession();

export const useStore = create<AppState>((set, get) => ({
  // Navigation / Session
  activeTab: 'dashboard',
  isAuthenticated: initialSession.isAuthenticated,
  user: initialSession.user,
  searchTerm: '',
  isCreateModalOpen: false,
  
  // App Data
  profiles: [],
  proxies: initialProxies,
  userAgents: [],
  templates: [],
  logs: initialLogs,
  customGroups: loadCustomGroupsFromStorage(),
  profileResources: {},
  
  // System Metrics
  systemMetrics: {
    cpu: 18,
    ram: 34,
    networkSpeed: 10,
    totalTraffic: '1.2 GB'
  },

  serverStatus: null,
  
  // Navigation & Auth Actions
  setActiveTab: (tab) => set({ activeTab: tab }),
  setSearchTerm: (term) => set({ searchTerm: term }),
  setIsCreateModalOpen: (isOpen) => set({ isCreateModalOpen: isOpen }),
  
  syncProfiles: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/profiles`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          // Normalize proxy and userAgent for legacy displays
          const normalized = data.map((p: any) => ({
            ...p,
            proxy: p.proxy || (p.proxyConfig && p.proxyConfig.type !== 'Direct'
              ? `${p.proxyConfig.host}:${p.proxyConfig.port} (${p.proxyConfig.type})`
              : 'No Proxy (Direct)')
          }));
          set({ profiles: normalized });
        }
      }
    } catch (e) {
      console.warn('API server offline.');
    }
  },

  fetchServerStatus: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/server/status`);
      if (res.ok) {
        const data = await res.json();
        set({ serverStatus: data });
      }
    } catch (e) {
      console.warn('API Offline, using local status.');
    }
  },

  resetServer: async () => {
    get().addLog('Bắt đầu đặt lại Server (Reset Server)...', 'warning');
    try {
      const res = await fetch(`${API_BASE}/api/server/reset`, { method: 'POST' });
      const data = await res.json();
      if (res.ok && data.success) {
        get().addLog(data.message, 'success');
        await get().syncProfiles();
        return { success: true, message: data.message };
      }
      return { success: false, message: data.message || 'Lỗi không xác định khi đặt lại Server.' };
    } catch (e: any) {
      get().addLog(`Lỗi khi đặt lại Server: ${e.message}`, 'error');
      return { success: false, message: e.message };
    }
  },

  syncCloud: async () => {
    get().addLog('Bắt đầu đồng bộ hóa dữ liệu với Cloud...', 'info');
    try {
      const res = await fetch(`${API_BASE}/api/server/sync-cloud`, { method: 'POST' });
      const data = await res.json();
      if (res.ok && data.success) {
        get().addLog(data.message, 'success');
        return { success: true, message: data.message };
      }
      return { success: false, message: data.message || 'Lỗi không xác định khi đồng bộ Cloud.' };
    } catch (e: any) {
      get().addLog(`Lỗi đồng bộ Cloud: ${e.message}`, 'error');
      return { success: false, message: `Lỗi đồng bộ: ${e.message}` };
    }
  },

  forgotPassword: async (email) => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        return { success: true, message: data.message };
      }
      return { success: false, message: data.error || 'Lỗi không xác định.' };
    } catch (e: any) {
      return { success: false, message: `Lỗi kết nối server: ${e.message}` };
    }
  },

  resetPassword: async (email, code, newPassword) => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code, newPassword })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        return { success: true, message: data.message };
      }
      return { success: false, message: data.error || 'Lỗi không xác định.' };
    } catch (e: any) {
      return { success: false, message: `Lỗi kết nối server: ${e.message}` };
    }
  },
  
  login: async (email, password, rememberMe = true) => {
    await new Promise((resolve) => setTimeout(resolve, 600));
    if (email && password.length >= 4) {
      const name = email.split('@')[0];
      const capitalized = name.charAt(0).toUpperCase() + name.slice(1);
      const userObj = {
        name: capitalized,
        email: email,
        avatar: `https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80`,
        role: 'Quản trị viên doanh nghiệp'
      };
      set({ isAuthenticated: true, user: userObj });
      
      if (rememberMe) {
        setCookie('gams_session', JSON.stringify(userObj), 7);
      } else {
        document.cookie = `gams_session=${encodeURIComponent(JSON.stringify(userObj))};path=/;SameSite=Strict`;
      }
      
      get().addLog(`Đăng nhập tài khoản ${email} thành công.`, 'success');
      await get().syncProfiles();
      await get().fetchServerStatus();
      await get().fetchUserAgents();
      await get().fetchTemplates();
      return true;
    }
    return false;
  },
  
  logout: () => {
    const email = get().user?.email || 'admin';
    eraseCookie('gams_session');
    set({ isAuthenticated: false, user: null, activeTab: 'dashboard' });
    get().addLog(`Tài khoản ${email} đã đăng xuất.`, 'info');
  },
  
  // Profile Actions
  addProfile: async (profileData) => {
    try {
      const res = await fetch(`${API_BASE}/api/profiles/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileData)
      });
      if (res.ok) {
        const p = await res.json();
        get().addLog(`Đã tạo mới Profile: "${p.name}".`, 'success');
        await get().syncProfiles();
      }
    } catch (e: any) {
      get().addLog(`Lỗi tạo profile: ${e.message}`, 'error');
    }
  },
  
  updateProfile: async (id, updates) => {
    try {
      const res = await fetch(`${API_BASE}/api/profiles/update/${id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      if (res.ok) {
        get().addLog(`Đã cập nhật Profile ID: ${id}.`, 'info');
        await get().syncProfiles();
      }
    } catch (e: any) {
      get().addLog(`Lỗi cập nhật profile: ${e.message}`, 'error');
    }
  },
  
  deleteProfile: async (id) => {
    const profileName = get().profiles.find((p) => p.id === id)?.name || id;
    try {
      const res = await fetch(`${API_BASE}/api/profiles/delete/${id}`);
      if (res.ok) {
        get().addLog(`Đã xóa Profile: "${profileName}".`, 'warning');
        await get().syncProfiles();
      }
    } catch (e: any) {
      get().addLog(`Lỗi xóa profile: ${e.message}`, 'error');
    }
  },
  
  launchProfile: async (id, layoutOptions = {}) => {
    const profile = get().profiles.find((p) => p.id === id);
    get().addLog(`Đang khởi chạy Profile: "${profile?.name}"...`, 'info');
    
    // Optimistic status starting
    set(state => ({
      profiles: state.profiles.map(p => p.id === id ? { ...p, status: 'starting' } : p)
    }));

    try {
      const res = await fetch(`${API_BASE}/api/profiles/start/${id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(layoutOptions)
      });
      const data = await res.json();
      if (res.ok && data.success) {
        get().addLog(`Profile "${profile?.name}" mở thành công (PID: ${data.pid}, Cổng Debug: ${data.port}).`, 'success');
        await get().syncProfiles();
      } else {
        get().addLog(`Mở Profile thất bại: ${data.error || 'Lỗi không xác định.'}`, 'error');
        set(state => ({
          profiles: state.profiles.map(p => p.id === id ? { ...p, status: 'error' } : p)
        }));
      }
    } catch (e: any) {
      get().addLog(`Lỗi kết nối server: ${e.message}`, 'error');
      set(state => ({
        profiles: state.profiles.map(p => p.id === id ? { ...p, status: 'error' } : p)
      }));
    }
  },
  
  stopProfile: async (id) => {
    const profile = get().profiles.find((p) => p.id === id);
    get().addLog(`Đang dừng Profile: "${profile?.name}"...`, 'info');
    
    try {
      const res = await fetch(`${API_BASE}/api/profiles/close/${id}`);
      if (res.ok) {
        get().addLog(`Đã đóng Profile: "${profile?.name}".`, 'success');
        await get().syncProfiles();
      }
    } catch (e: any) {
      get().addLog(`Lỗi đóng profile: ${e.message}`, 'error');
    }
  },
  
  cloneProfile: async (id) => {
    const source = get().profiles.find((p) => p.id === id);
    if (!source) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/profiles/clone/${id}`, { method: 'POST' });
      if (res.ok) {
        get().addLog(`Đã nhân bản Profile "${source.name}".`, 'success');
        await get().syncProfiles();
      }
    } catch (e: any) {
      get().addLog(`Lỗi nhân bản: ${e.message}`, 'error');
    }
  },

  startGroup: async (groupName: string) => {
    get().addLog(`Bắt đầu chạy đồng loạt Nhóm Profile: "${groupName}"...`, 'info');
    try {
      const res = await fetch(`${API_BASE}/api/profiles/start-group/${encodeURIComponent(groupName)}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        get().addLog(`Đã gửi lệnh chạy nhóm "${groupName}". Mở thành công ${data.started.length} Profiles.`, 'success');
        await get().syncProfiles();
      }
    } catch (e: any) {
      get().addLog(`Lỗi chạy nhóm: ${e.message}`, 'error');
    }
  },

  stopGroup: async (groupName: string) => {
    get().addLog(`Đang dừng toàn bộ Profiles trong Nhóm: "${groupName}"...`, 'info');
    try {
      const res = await fetch(`${API_BASE}/api/profiles/stop-group/${encodeURIComponent(groupName)}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        get().addLog(`Đã dừng ${data.stoppedCount} Profiles trong nhóm.`, 'success');
        await get().syncProfiles();
      }
    } catch (e: any) {
      get().addLog(`Lỗi dừng nhóm: ${e.message}`, 'error');
    }
  },

  exportProfile: async (id) => {
    const profile = get().profiles.find(p => p.id === id);
    get().addLog(`Đang trích xuất backup file cho Profile: "${profile?.name}"...`, 'info');
    try {
      window.open(`${API_BASE}/api/profiles/export/${id}`, '_blank');
      get().addLog(`Tải tệp backup zip thành công.`, 'success');
    } catch (e: any) {
      get().addLog(`Lỗi trích xuất: ${e.message}`, 'error');
    }
  },

  importProfile: async (base64Zip) => {
    get().addLog(`Đang nạp profile từ tệp backup zip...`, 'info');
    try {
      const res = await fetch(`${API_BASE}/api/profiles/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zipData: base64Zip })
      });
      if (res.ok) {
        const data = await res.json();
        get().addLog(`Đã phục hồi Profile: "${data.profile.name}" thành công.`, 'success');
        await get().syncProfiles();
        return true;
      }
      return false;
    } catch (e: any) {
      get().addLog(`Lỗi nạp tệp zip: ${e.message}`, 'error');
      return false;
    }
  },

  fetchProfileLogs: async (id) => {
    try {
      const res = await fetch(`${API_BASE}/api/profiles/logs/${id}`);
      if (res.ok) {
        const data = await res.json();
        return data.logs;
      }
    } catch (e) {
      // Offline fallback
    }
    return '[System] offline. Cannot fetch logs.';
  },

  clearProfileLogs: async (id) => {
    try {
      await fetch(`${API_BASE}/api/profiles/logs/${id}`, { method: 'DELETE' });
      get().addLog('Đã dọn dẹp nhật ký log của profile.', 'success');
    } catch (e) {}
  },

  // User Agent Actions
  fetchUserAgents: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/user-agents`);
      if (res.ok) {
        const data = await res.json();
        set({ userAgents: data });
      }
    } catch (e) {}
  },

  addUserAgent: async (ua, platform) => {
    try {
      const res = await fetch(`${API_BASE}/api/user-agents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ua, platform })
      });
      if (res.ok) {
        get().addLog('Đã thêm mới User Agent.', 'success');
        await get().fetchUserAgents();
      }
    } catch (e) {}
  },

  updateUserAgent: async (id, ua, platform) => {
    try {
      const res = await fetch(`${API_BASE}/api/user-agents/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ua, platform })
      });
      if (res.ok) {
        get().addLog('Đã cập nhật User Agent.', 'info');
        await get().fetchUserAgents();
      }
    } catch (e) {}
  },

  deleteUserAgent: async (id) => {
    try {
      const res = await fetch(`${API_BASE}/api/user-agents/${id}`, { method: 'DELETE' });
      if (res.ok) {
        get().addLog('Đã xóa User Agent.', 'warning');
        await get().fetchUserAgents();
      }
    } catch (e) {}
  },

  importUserAgents: async (type, payload, platform) => {
    try {
      const res = await fetch(`${API_BASE}/api/user-agents/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, txt: type === 'text' ? payload : undefined, json: type === 'json' ? payload : undefined, platform })
      });
      if (res.ok) {
        const data = await res.json();
        get().addLog(`Đã nạp ${data.count} User Agents mới.`, 'success');
        await get().fetchUserAgents();
        return data.count;
      }
    } catch (e) {}
    return 0;
  },

  // Template Manager Actions
  fetchTemplates: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/templates`);
      if (res.ok) {
        const data = await res.json();
        set({ templates: data });
      }
    } catch (e) {}
  },

  createTemplate: async (tpl) => {
    try {
      const res = await fetch(`${API_BASE}/api/templates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tpl)
      });
      if (res.ok) {
        get().addLog(`Đã tạo Template mới: "${tpl.name}".`, 'success');
        await get().fetchTemplates();
      }
    } catch (e) {}
  },

  updateTemplate: async (id, updates) => {
    try {
      const res = await fetch(`${API_BASE}/api/templates/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      if (res.ok) {
        get().addLog(`Đã cập nhật Template: ID ${id}.`, 'info');
        await get().fetchTemplates();
      }
    } catch (e) {}
  },

  deleteTemplate: async (id) => {
    try {
      const res = await fetch(`${API_BASE}/api/templates/${id}`, { method: 'DELETE' });
      if (res.ok) {
        get().addLog('Đã xóa Template.', 'warning');
        await get().fetchTemplates();
      }
    } catch (e) {}
  },

  // Window Arrangement Action
  arrangeWindows: async (ids, layoutMode) => {
    get().addLog(`Đang sắp xếp ${ids.length} Profiles theo layout "${layoutMode}"...`, 'info');
    try {
      const res = await fetch(`${API_BASE}/api/profiles/arrange`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ids,
          layoutMode,
          screenWidth: window.screen.width,
          screenHeight: window.screen.height
        })
      });
      if (res.ok) {
        get().addLog('Sắp xếp màn hình hoàn tất.', 'success');
      }
    } catch (e) {}
  },
  
  // Proxy Actions
  fetchProxies: () => {
    const saved = loadProxiesFromStorage();
    set({ proxies: saved });
  },

  addProxy: (proxyData) => {
    const newProxy: ProxyItem = {
      ...proxyData,
      id: `pr-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      status: 'inactive',
    };
    const updatedProxies = [newProxy, ...get().proxies];
    set({ proxies: updatedProxies });
    saveProxiesToStorage(updatedProxies);
    get().addLog(`Đã import proxy mới: ${newProxy.host}:${newProxy.port}`, 'success');
  },
  
  deleteProxy: (id) => {
    const proxy = get().proxies.find((pr) => pr.id === id);
    const updatedProxies = get().proxies.filter((pr) => pr.id !== id);
    set({ proxies: updatedProxies });
    saveProxiesToStorage(updatedProxies);
    if (proxy) {
      get().addLog(`Đã xóa proxy: ${proxy.host}:${proxy.port}`, 'warning');
    }
  },
  
  testProxy: async (id) => {
    const proxy = get().proxies.find((p) => p.id === id);
    if (!proxy) return;

    set((state) => ({
      proxies: state.proxies.map((p) => (p.id === id ? { ...p, status: 'testing' } : p))
    }));
    
    get().addLog(`Đang kiểm tra kết nối proxy: ${proxy.host}:${proxy.port}...`, 'info');

    try {
      const res = await fetch(`${API_BASE}/api/proxies/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: proxy.type,
          host: proxy.host,
          port: proxy.port,
          username: proxy.username,
          password: proxy.password
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          const updatedProxies = get().proxies.map((p) =>
            p.id === id
              ? {
                  ...p,
                  status: 'active' as const,
                  speed: data.latency,
                  group: `IP: ${data.ip} - ${data.country} (${data.timezone})`
                }
              : p
          );
          set({ proxies: updatedProxies });
          saveProxiesToStorage(updatedProxies);
          get().addLog(`Proxy ${proxy.host}:${proxy.port} hoạt động! IP: ${data.ip} (${data.country}), Latency: ${data.latency}ms. Múi giờ: ${data.timezone}`, 'success');
          return;
        } else {
          get().addLog(`Proxy ${proxy.host}:${proxy.port} hỏng (Die): ${data.error}`, 'error');
        }
      }
    } catch (e: any) {
      get().addLog(`Lỗi kiểm tra proxy: ${e.message}`, 'error');
    }

    const failedProxies = get().proxies.map((p) =>
      p.id === id ? { ...p, status: 'failed' as const, speed: 0 } : p
    );
    set({ proxies: failedProxies });
    saveProxiesToStorage(failedProxies);
  },
  
  testAllProxies: async () => {
    const proxyIds = get().proxies.map((p) => p.id);
    await Promise.all(proxyIds.map((id) => get().testProxy(id)));
  },

  bulkCreateProfiles: async (opts) => {
    const { prefix, count, group, templateId, proxyIds, startIndex = 1 } = opts;
    const proxies = get().proxies;
    let created = 0;
    for (let i = 0; i < count; i++) {
      const paddedNum = String(startIndex + i).padStart(3, '0');
      const name = `${prefix.trim()} ${paddedNum}`;
      // Cycle through provided proxyIds round-robin
      let proxyConfig: any = { type: 'Direct', host: '', port: '' };
      let proxyStr = 'No Proxy (Direct)';
      if (proxyIds.length > 0) {
        const proxyId = proxyIds[i % proxyIds.length];
        const pr = proxies.find((p) => p.id === proxyId);
        if (pr) {
          proxyConfig = {
            type: pr.type,
            host: pr.host,
            port: String(pr.port),
            username: pr.username || '',
            password: pr.password || ''
          };
          proxyStr = `${pr.host}:${pr.port} (${pr.type})`;
        }
      }
      try {
        const payload: any = {
          name,
          group,
          platform: 'Windows',
          browserType: 'chromium',
          proxyConfig,
          proxy: proxyStr,
          notes: '',
          language: 'vi-VN,vi;q=0.9',
          timezone: 'Asia/Ho_Chi_Minh',
          windowSize: { width: 1280, height: 720, x: 50, y: 50 },
          startupConfig: { mode: 'blank', urls: [] },
          hardwareConcurrency: 8,
          deviceMemory: 8,
          spoofFingerprints: true
        };
        if (templateId && templateId !== 'none') payload.templateId = templateId;
        const res = await fetch(`${API_BASE}/api/profiles/create`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) created++;
      } catch (e) {}
    }
    get().addLog(`Đã tạo hàng loạt ${created}/${count} profiles với prefix "${prefix}".`, 'success');
    await get().syncProfiles();
    return created;
  },

  // Bulk clone selected profiles one by one
  bulkCloneProfiles: async (ids) => {
    let cloned = 0;
    for (const id of ids) {
      try {
        const res = await fetch(`${API_BASE}/api/profiles/clone/${id}`, { method: 'POST' });
        if (res.ok) cloned++;
      } catch (e) {}
    }
    get().addLog(`Đã nhân bản ${cloned}/${ids.length} profiles.`, 'success');
    await get().syncProfiles();
  },

  bulkAssignProxies: async (profileIds, proxyIds, assignMode) => {
    const proxies = get().proxies;
    let updatedCount = 0;
    for (let i = 0; i < profileIds.length; i++) {
      const profileId = profileIds[i];
      let proxyConfig: ProxyConfig = { type: 'Direct', host: '', port: '' };
      let fallbackProxies: ProxyConfig[] = [];
      let proxyStr = 'No Proxy (Direct)';

      if (assignMode === 'all-fallback' && proxyIds.length > 0) {
        const selectedProxies = proxyIds.map(id => proxies.find(p => p.id === id)).filter(Boolean) as ProxyItem[];
        if (selectedProxies.length > 0) {
          const first = selectedProxies[0];
          proxyConfig = {
            type: first.type,
            host: first.host,
            port: String(first.port),
            username: first.username || '',
            password: first.password || ''
          };
          proxyStr = `${first.host}:${first.port} (${first.type}) + ${selectedProxies.length - 1} dự phòng`;
          fallbackProxies = selectedProxies.slice(1).map(p => ({
            type: p.type,
            host: p.host,
            port: String(p.port),
            username: p.username || '',
            password: p.password || ''
          }));
        }
      } else {
        let selectedProxy: ProxyItem | undefined;
        if (assignMode === 'single' && proxyIds.length > 0) {
          selectedProxy = proxies.find(p => p.id === proxyIds[0]);
        } else if (assignMode === 'round-robin' && proxyIds.length > 0) {
          const proxyId = proxyIds[i % proxyIds.length];
          selectedProxy = proxies.find(p => p.id === proxyId);
        }

        if (selectedProxy) {
          proxyConfig = {
            type: selectedProxy.type,
            host: selectedProxy.host,
            port: String(selectedProxy.port),
            username: selectedProxy.username || '',
            password: selectedProxy.password || ''
          };
          proxyStr = `${selectedProxy.host}:${selectedProxy.port} (${selectedProxy.type})`;
        }
      }

      try {
        const res = await fetch(`${API_BASE}/api/profiles/update/${profileId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ proxyConfig, fallbackProxies, proxy: proxyStr })
        });
        if (res.ok) updatedCount++;
      } catch (e) {}
    }
    get().addLog(`Đã gán proxy cho ${updatedCount}/${profileIds.length} profiles.`, 'success');
    await get().syncProfiles();
  },

  // Bulk rename selected profiles with prefix and start number
  bulkRenameProfiles: async (ids, prefix, startIndex) => {
    let updated = 0;
    for (let i = 0; i < ids.length; i++) {
      const id = ids[i];
      const paddedNum = String(startIndex + i).padStart(3, '0');
      const newName = `${prefix.trim()} ${paddedNum}`;
      try {
        const res = await fetch(`${API_BASE}/api/profiles/update/${id}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: newName })
        });
        if (res.ok) updated++;
      } catch (e) {}
    }
    get().addLog(`Đã đổi tên hàng loạt ${updated}/${ids.length} profiles.`, 'success');
    await get().syncProfiles();
  },
  
  // Cookie Actions
  importCookies: (profileId, cookiesText) => {
    const profile = get().profiles.find((p) => p.id === profileId);
    if (!profile) return { success: false, count: 0, error: 'Không tìm thấy profile.' };
    
    try {
      let parsedCookiesCount = 0;
      if (cookiesText.trim().startsWith('[') || cookiesText.trim().startsWith('{')) {
        const obj = JSON.parse(cookiesText);
        parsedCookiesCount = Array.isArray(obj) ? obj.length : 1;
      } else {
        const lines = cookiesText.split('\n').filter((l) => l.trim() !== '' && !l.startsWith('#'));
        parsedCookiesCount = lines.length;
      }
      
      if (parsedCookiesCount === 0) {
        return { success: false, count: 0, error: 'Không tìm thấy cookie hợp lệ.' };
      }
      
      set((state) => ({
        profiles: state.profiles.map((p) =>
          p.id === profileId
            ? { ...p, cookiesCount: p.cookiesCount + parsedCookiesCount }
            : p
        )
      }));
      
      get().addLog(`Nhập thành công ${parsedCookiesCount} cookies vào profile "${profile.name}".`, 'success');
      return { success: true, count: parsedCookiesCount };
    } catch (e: any) {
      return { success: false, count: 0, error: `Lỗi parse dữ liệu: ${e.message}` };
    }
  },
  
  // Logs
  addLog: (message, type = 'info') => {
    const now = new Date();
    const timestamp = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
    const newEntry: LogEntry = {
      id: `l-${Date.now()}`,
      timestamp,
      message,
      type
    };
    set((state) => ({
      logs: [newEntry, ...state.logs.slice(0, 99)]
    }));
  },
  
  clearLogs: () => set({ logs: [] }),
  
  // Real resource monitor & Metrics ticker combined
  updateMetrics: async () => {
    const state = get();
    const runningProfiles = state.profiles.filter((p) => p.status === 'running');
    const runningCount = runningProfiles.length;
    
    // Poll real resource stats from backend if running
    let realStats: Record<string, { cpu: number; ramBytes: number }> = {};
    if (runningCount > 0) {
      try {
        const res = await fetch(`${API_BASE}/api/profiles/monitor`);
        if (res.ok) {
          realStats = await res.json();
          set({ profileResources: realStats });
        }
      } catch (e) {
        // Fallback to empty if offline
      }
    } else {
      set({ profileResources: {} });
    }

    // Fluctuating total system metrics
    let totalCpu = 10;
    let totalRamBytes = 2.4 * 1024 * 1024 * 1024; // Base 2.4 GB

    runningProfiles.forEach(p => {
      const stat = realStats[p.id] || { cpu: 3, ramBytes: 150 * 1024 * 1024 };
      totalCpu += stat.cpu;
      totalRamBytes += stat.ramBytes;
    });

    const newCpu = Math.max(5, Math.min(98, totalCpu + Math.floor(Math.random() * 6) - 3));
    const newRam = Math.max(10, Math.min(95, Math.floor((totalRamBytes / (8 * 1024 * 1024 * 1024)) * 100))); // relative to 8GB total RAM

    const newSpeed = runningCount > 0 
      ? Math.floor(Math.random() * 300) + 100 * runningCount 
      : Math.floor(Math.random() * 10) + 2;

    const currentTrafficGb = parseFloat(state.systemMetrics.totalTraffic.replace(' GB', ''));
    const addedTrafficGb = (newSpeed / 1024 / 1024) * 3;
    const newTraffic = `${(currentTrafficGb + addedTrafficGb).toFixed(4)} GB`;
    
    set({
      systemMetrics: {
        cpu: newCpu,
        ram: newRam,
        networkSpeed: newSpeed,
        totalTraffic: newTraffic
      }
    });
  },

  addCustomGroup: (name: string) => {
    const trimmed = name.trim();
    if (!trimmed) return;
    const current = get().customGroups;
    if (current.includes(trimmed)) return;
    const updated = [...current, trimmed];
    localStorage.setItem('gams_custom_groups', JSON.stringify(updated));
    set({ customGroups: updated });
    get().addLog(`Đã thêm nhóm mới: "${trimmed}"`, 'success');
  },
  deleteCustomGroup: (name: string) => {
    const current = get().customGroups;
    const updated = current.filter(g => g !== name);
    localStorage.setItem('gams_custom_groups', JSON.stringify(updated));
    set({ customGroups: updated });
    get().addLog(`Đã xóa nhóm: "${name}"`, 'warning');
  },
  bulkAssignGroup: async (profileIds: string[], groupName: string) => {
    const updatedCount = profileIds.length;
    if (updatedCount === 0) return;
    
    get().addLog(`Đang gán nhóm "${groupName}" cho ${updatedCount} profiles...`, 'info');
    
    let successCount = 0;
    for (const id of profileIds) {
      try {
        const res = await fetch(`${API_BASE}/api/profiles/update/${id}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ group: groupName })
        });
        if (res.ok) {
          successCount++;
        }
      } catch (e) {}
    }
    
    await get().syncProfiles();
    get().addLog(`Đã gán nhóm "${groupName}" thành công cho ${successCount}/${updatedCount} profiles.`, 'success');
  }
}));
