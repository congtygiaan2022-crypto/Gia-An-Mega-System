import { create } from 'zustand';

const API_BASE = 'http://localhost:1020';

export interface BrowserProfile {
  id: string;
  name: string;
  status: 'running' | 'stopped';
  proxy: string;
  browserVersion: string;
  lastOpened: string;
  notes: string;
  group: string;
  cookiesCount: number;
  platform: 'Windows' | 'macOS' | 'Linux';
  userAgent: string;
  port?: number;
}

export interface ProxyItem {
  id: string;
  host: string;
  port: number;
  type: 'HTTP' | 'SOCKS5';
  status: 'active' | 'inactive' | 'testing' | 'failed';
  speed?: number; // ms
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

interface AppState {
  // Navigation / Session
  activeTab: 'dashboard' | 'profiles' | 'proxies' | 'cookies' | 'automation' | 'settings' | 'account' | 'api-guide';
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
  logs: LogEntry[];
  
  // System Monitor (Simulated)
  systemMetrics: {
    cpu: number;
    ram: number;
    networkSpeed: number; // in KB/s
    totalTraffic: string; // e.g., "1.2 GB"
  };

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
  addProfile: (profile: Omit<BrowserProfile, 'id' | 'status' | 'lastOpened' | 'browserVersion'>) => void;
  updateProfile: (id: string, updates: Partial<BrowserProfile>) => void;
  deleteProfile: (id: string) => void;
  launchProfile: (id: string) => void;
  stopProfile: (id: string) => void;
  cloneProfile: (id: string) => void;
  
  // Proxy Actions
  addProxy: (proxy: Omit<ProxyItem, 'id' | 'status'>) => void;
  deleteProxy: (id: string) => void;
  testProxy: (id: string) => Promise<void>;
  testAllProxies: () => Promise<void>;
  
  // Cookie Actions
  importCookies: (profileId: string, cookiesText: string) => { success: boolean; count: number; error?: string };
  
  // Logging
  addLog: (message: string, type?: LogEntry['type']) => void;
  clearLogs: () => void;
  
  // Metrics Tick
  updateMetrics: () => void;
}

// Initial Mock Profiles
const initialProfiles: BrowserProfile[] = [
  {
    id: 'p-1',
    name: 'Facebook Ad Account 01',
    status: 'stopped',
    proxy: '45.138.22.112:8000 (US-HTTP)',
    browserVersion: 'Chromium 122.0',
    lastOpened: '2026-06-10 18:45',
    notes: 'Tài khoản quảng cáo chính cho chiến dịch Thương mại điện tử',
    group: 'Facebook Ads',
    cookiesCount: 142,
    platform: 'Windows',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
  },
  {
    id: 'p-2',
    name: 'Google Ads Agency Profile',
    status: 'running',
    proxy: '185.220.101.5:9050 (DE-SOCKS5)',
    browserVersion: 'Chromium 122.0',
    lastOpened: '2026-06-11 04:30',
    notes: 'Tài khoản Agency cho Khách hàng Alpha',
    group: 'Google Ads',
    cookiesCount: 89,
    platform: 'macOS',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
  },
  {
    id: 'p-3',
    name: 'TikTok Creator Hub - Beta',
    status: 'stopped',
    proxy: 'Không dùng Proxy (Direct)',
    browserVersion: 'Chromium 120.0',
    lastOpened: '2026-06-08 11:20',
    notes: 'Bảng điều khiển nhà sáng tạo để tải lên nội dung lan truyền',
    group: 'TikTok',
    cookiesCount: 204,
    platform: 'Linux',
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  },
  {
    id: 'p-4',
    name: 'Ebay Seller Account - UK Store',
    status: 'stopped',
    proxy: '88.198.50.22:3128 (UK-HTTP)',
    browserVersion: 'Chromium 122.0',
    lastOpened: '2026-06-09 23:12',
    notes: 'Profile thử nghiệm drop-shipping cho cửa hàng tại Anh',
    group: 'Ecommerce',
    cookiesCount: 67,
    platform: 'Windows',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
  },
  {
    id: 'p-5',
    name: 'Twitter/X Automation Bot 09',
    status: 'running',
    proxy: '194.67.212.87:1080 (RU-SOCKS5)',
    browserVersion: 'Chromium 122.0',
    lastOpened: '2026-06-11 05:00',
    notes: 'Profile lên lịch bài viết tự động',
    group: 'Social Bots',
    cookiesCount: 12,
    platform: 'Windows',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
  }
];

// Initial Mock Proxies
const initialProxies: ProxyItem[] = [
  { id: 'pr-1', host: '45.138.22.112', port: 8000, type: 'HTTP', status: 'active', speed: 85, group: 'Proxy Dân cư US' },
  { id: 'pr-2', host: '185.220.101.5', port: 9050, type: 'SOCKS5', status: 'active', speed: 120, group: 'Proxy Châu Âu' },
  { id: 'pr-3', host: '88.198.50.22', port: 3128, type: 'HTTP', status: 'active', speed: 95, group: 'Proxy Dân cư UK' },
  { id: 'pr-4', host: '194.67.212.87', port: 1080, type: 'SOCKS5', status: 'inactive', speed: 0, group: 'Khu vực SNG' },
  { id: 'pr-5', host: '172.56.21.99', port: 8080, type: 'HTTP', status: 'failed', speed: 0, group: 'Proxy Di động' }
];

// Initial Logs
const initialLogs: LogEntry[] = [
  { id: 'l-1', timestamp: '05:00:12', message: 'Hệ thống Gams-GALogin khởi động thành công.', type: 'info' },
  { id: 'l-2', timestamp: '05:01:45', message: 'Tải thành công 5 profiles trình duyệt và 5 cấu hình proxy.', type: 'success' },
  { id: 'l-3', timestamp: '05:02:10', message: 'Kết nối đồng bộ hóa đám mây được xác thực.', type: 'success' }
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

// Initial Session Check from Cookie
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
    console.error('Failed to parse initial session from cookie', e);
  }
  return { isAuthenticated: false, user: null };
};

const initialSession = getInitialSession();

export const useStore = create<AppState>((set, get) => ({
  // Navigation / Session
  activeTab: 'dashboard',
  isAuthenticated: initialSession.isAuthenticated, // Load session from cookie
  user: initialSession.user,
  searchTerm: '',
  isCreateModalOpen: false,
  
  // App Data
  profiles: initialProfiles,
  proxies: initialProxies,
  logs: initialLogs,
  
  // System Metrics
  systemMetrics: {
    cpu: 24,
    ram: 42,
    networkSpeed: 380,
    totalTraffic: '3.4 GB'
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
          set({ profiles: data });
        } else {
          console.warn('API returned non-array profiles data, keeping current state:', data);
        }
      }
    } catch (e) {
      console.warn('API Offline, using local state.');
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
      const res = await fetch(`${API_BASE}/api/server/reset`, {
        method: 'POST'
      });
      const data = await res.json();
      if (res.ok && data.success) {
        get().addLog(data.message, 'success');
        await get().syncProfiles();
        return { success: true, message: data.message };
      }
      return { success: false, message: data.message || 'Lỗi không xác định khi đặt lại Server.' };
    } catch (e: any) {
      get().addLog(`Lỗi khi đặt lại Server: ${e.message}`, 'error');
      // Fallback mock reset
      set((state) => ({
        profiles: state.profiles.map((p) => ({ ...p, status: 'stopped' }))
      }));
      get().addLog('Đã giả lập đặt lại Server cục bộ thành công.', 'success');
      return { success: true, message: 'Đã giả lập đặt lại Server cục bộ thành công.' };
    }
  },

  syncCloud: async () => {
    get().addLog('Bắt đầu đồng bộ hóa dữ liệu với Cloud...', 'info');
    try {
      const res = await fetch(`${API_BASE}/api/server/sync-cloud`, {
        method: 'POST'
      });
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
    // Simulate API login latency
    await new Promise((resolve) => setTimeout(resolve, 800));
    
    // Accept any credentials for mockup/prototype purposes
    if (email && password.length >= 4) {
      const name = email.split('@')[0];
      const capitalized = name.charAt(0).toUpperCase() + name.slice(1);
      const userObj = {
        name: capitalized,
        email: email,
        avatar: `https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80`,
        role: 'Quản trị viên chuyên nghiệp'
      };
      set({
        isAuthenticated: true,
        user: userObj
      });
      
      // Save cookie if rememberMe is true, otherwise session cookie
      if (rememberMe) {
        setCookie('gams_session', JSON.stringify(userObj), 7);
      } else {
        document.cookie = `gams_session=${encodeURIComponent(JSON.stringify(userObj))};path=/;SameSite=Strict`;
      }
      
      get().addLog(`Người dùng ${email} đăng nhập thành công.`, 'success');
      await get().syncProfiles(); // Fetch profiles from local server upon login
      await get().fetchServerStatus(); // Fetch server status & environment settings
      return true;
    }
    return false;
  },
  
  logout: () => {
    const email = get().user?.email || 'admin';
    eraseCookie('gams_session');
    set({ isAuthenticated: false, user: null, activeTab: 'dashboard' });
    get().addLog(`Người dùng ${email} đã đăng xuất khỏi hệ thống.`, 'info');
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
        get().addLog(`Đã tạo mới profile trên server: "${profileData.name}".`, 'success');
        await get().syncProfiles();
        return;
      }
    } catch (e) {
      // Ignore and fallback
    }

    const newProfile: BrowserProfile = {
      ...profileData,
      id: `p-${Date.now()}`,
      status: 'stopped',
      browserVersion: 'Chromium 122.0',
      lastOpened: 'Chưa sử dụng'
    };
    
    set((state) => ({
      profiles: [newProfile, ...state.profiles]
    }));
    get().addLog(`Đã tạo mới profile cục bộ: "${newProfile.name}".`, 'success');
  },
  
  updateProfile: async (id, updates) => {
    try {
      const res = await fetch(`${API_BASE}/api/profiles/update/${id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      if (res.ok) {
        get().addLog(`Đã cập nhật profile trên server: ID ${id}.`, 'info');
        await get().syncProfiles();
        return;
      }
    } catch (e) {
      // Ignore and fallback
    }

    set((state) => ({
      profiles: state.profiles.map((p) => (p.id === id ? { ...p, ...updates } : p))
    }));
    get().addLog(`Đã cập nhật thông tin profile cục bộ ID: ${id}.`, 'info');
  },
  
  deleteProfile: async (id) => {
    const profileName = get().profiles.find((p) => p.id === id)?.name || id;
    try {
      const res = await fetch(`${API_BASE}/api/profiles/delete/${id}`);
      if (res.ok) {
        get().addLog(`Đã xóa profile trên server: "${profileName}".`, 'warning');
        await get().syncProfiles();
        return;
      }
    } catch (e) {
      // Ignore and fallback
    }

    set((state) => ({
      profiles: state.profiles.filter((p) => p.id !== id)
    }));
    get().addLog(`Đã xóa profile cục bộ: "${profileName}".`, 'warning');
  },
  
  launchProfile: async (id) => {
    const profile = get().profiles.find((p) => p.id === id);
    get().addLog(`Khởi chạy trình duyệt Chromium cho Profile: "${profile?.name}"...`, 'info');
    
    try {
      const res = await fetch(`${API_BASE}/api/profiles/start/${id}`);
      const data = await res.json();
      if (res.ok && data.success) {
        get().addLog(`Trình duyệt Chromium của Profile "${profile?.name}" đã mở thành công (PID ${data.pid}, Cổng debug: ${data.port}).`, 'success');
        await get().syncProfiles();
        return;
      } else if (data.error) {
        get().addLog(`Không thể mở trình duyệt: ${data.error}`, 'error');
        return;
      }
    } catch (e) {
      // Ignore and fallback to mock
    }

    const now = new Date();
    const timeString = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    
    set((state) => ({
      profiles: state.profiles.map((p) =>
        p.id === id ? { ...p, status: 'running', lastOpened: timeString } : p
      )
    }));
    
    // Simulate Chrome startup success after 1.5 seconds
    setTimeout(() => {
      get().addLog(`Trình duyệt Chromium của Profile "${profile?.name}" đã mở thành công (Giả lập).`, 'success');
    }, 1500);
  },
  
  stopProfile: async (id) => {
    const profile = get().profiles.find((p) => p.id === id);
    get().addLog(`Đang dừng hoạt động trình duyệt cho Profile: "${profile?.name}"...`, 'info');
    
    try {
      const res = await fetch(`${API_BASE}/api/profiles/close/${id}`);
      if (res.ok) {
        get().addLog(`Đã đóng trình duyệt Chromium của Profile "${profile?.name}" thành công.`, 'success');
        await get().syncProfiles();
        return;
      }
    } catch (e) {
      // Ignore and fallback to mock
    }

    set((state) => ({
      profiles: state.profiles.map((p) =>
        p.id === id ? { ...p, status: 'stopped' } : p
      )
    }));
    
    setTimeout(() => {
      get().addLog(`Đã đóng trình duyệt Chromium và đồng bộ dữ liệu cho Profile "${profile?.name}" (Giả lập).`, 'success');
    }, 1000);
  },
  
  cloneProfile: async (id) => {
    const source = get().profiles.find((p) => p.id === id);
    if (!source) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/profiles/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `${source.name} (Bản sao)`,
          group: source.group,
          proxy: source.proxy,
          platform: source.platform,
          userAgent: source.userAgent,
          notes: source.notes
        })
      });
      if (res.ok) {
        get().addLog(`Đã nhân bản profile "${source.name}" thành công trên server.`, 'success');
        await get().syncProfiles();
        return;
      }
    } catch (e) {
      // Ignore and fallback
    }

    const cloned: BrowserProfile = {
      ...source,
      id: `p-${Date.now()}`,
      name: `${source.name} (Bản sao)`,
      status: 'stopped',
      lastOpened: 'Chưa sử dụng'
    };
    
    set((state) => ({
      profiles: [cloned, ...state.profiles]
    }));
    get().addLog(`Đã nhân bản profile cục bộ "${source.name}" thành "${cloned.name}".`, 'success');
  },
  
  // Proxy Actions
  addProxy: (proxyData) => {
    const newProxy: ProxyItem = {
      ...proxyData,
      id: `pr-${Date.now()}`,
      status: 'active',
      speed: Math.floor(Math.random() * 150) + 40
    };
    set((state) => ({
      proxies: [newProxy, ...state.proxies]
    }));
    get().addLog(`Đã import proxy mới: ${newProxy.host}:${newProxy.port}`, 'success');
  },
  
  deleteProxy: (id) => {
    const proxy = get().proxies.find((pr) => pr.id === id);
    set((state) => ({
      proxies: state.proxies.filter((pr) => pr.id !== id)
    }));
    if (proxy) {
      get().addLog(`Đã xóa proxy: ${proxy.host}:${proxy.port}`, 'warning');
    }
  },
  
  testProxy: async (id) => {
    set((state) => ({
      proxies: state.proxies.map((p) => (p.id === id ? { ...p, status: 'testing' } : p))
    }));
    get().addLog(`Đang kiểm tra kết nối proxy ID: ${id}...`, 'info');
    
    await new Promise((resolve) => setTimeout(resolve, 1200));
    
    const isSuccess = Math.random() > 0.15; // 85% success chance
    const speed = isSuccess ? Math.floor(Math.random() * 180) + 30 : 0;
    
    set((state) => ({
      proxies: state.proxies.map((p) =>
        p.id === id
          ? {
              ...p,
              status: isSuccess ? 'active' : 'failed',
              speed: speed
            }
          : p
      )
    }));
    
    const proxy = get().proxies.find((p) => p.id === id);
    if (isSuccess) {
      get().addLog(`Kiểm tra proxy ${proxy?.host}:${proxy?.port} thành công. Trễ: ${speed}ms`, 'success');
    } else {
      get().addLog(`Kiểm tra proxy ${proxy?.host}:${proxy?.port} thất bại! Không thể kết nối.`, 'error');
    }
  },
  
  testAllProxies: async () => {
    get().addLog(`Bắt đầu kiểm tra hàng loạt tất cả các proxy...`, 'info');
    const proxyIds = get().proxies.map((p) => p.id);
    await Promise.all(proxyIds.map((id) => get().testProxy(id)));
    get().addLog(`Đã hoàn tất kiểm tra kết nối tất cả proxy.`, 'success');
  },
  
  // Cookie Actions
  importCookies: (profileId, cookiesText) => {
    const profile = get().profiles.find((p) => p.id === profileId);
    if (!profile) return { success: false, count: 0, error: 'Không tìm thấy profile.' };
    
    try {
      // Basic simulation of cookie parsing
      let parsedCookiesCount = 0;
      if (cookiesText.trim().startsWith('[') || cookiesText.trim().startsWith('{')) {
        const obj = JSON.parse(cookiesText);
        parsedCookiesCount = Array.isArray(obj) ? obj.length : 1;
      } else {
        // Try line-by-line Netscape parser mock
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
      logs: [newEntry, ...state.logs.slice(0, 99)] // Limit to last 100 logs
    }));
  },
  
  clearLogs: () => set({ logs: [] }),
  
  // System Metrics fluctuation
  updateMetrics: () => {
    const state = get();
    const runningCount = state.profiles.filter((p) => p.status === 'running').length;
    
    // CPU fluctuates based on running profiles
    const baseCpu = 10 + runningCount * 12;
    const cpuFluctuation = Math.floor(Math.random() * 8) - 4;
    const newCpu = Math.max(5, Math.min(98, baseCpu + cpuFluctuation));
    
    // RAM is more stable but increases with running profiles
    const baseRam = 30 + runningCount * 6;
    const ramFluctuation = Math.floor(Math.random() * 2) - 1;
    const newRam = Math.max(15, Math.min(95, baseRam + ramFluctuation));
    
    // Network traffic speed
    const newSpeed = runningCount > 0 ? Math.floor(Math.random() * 400) + 120 * runningCount : Math.floor(Math.random() * 15) + 5;
    
    // Incremental Traffic calculation
    const currentTrafficGb = parseFloat(state.systemMetrics.totalTraffic.replace(' GB', ''));
    const addedTrafficGb = (newSpeed / 1024 / 1024) * 2; // Simulated traffic accumulated per tick
    const newTraffic = `${(currentTrafficGb + addedTrafficGb).toFixed(4)} GB`;
    
    set({
      systemMetrics: {
        cpu: newCpu,
        ram: newRam,
        networkSpeed: newSpeed,
        totalTraffic: newTraffic
      }
    });
  }
}));
