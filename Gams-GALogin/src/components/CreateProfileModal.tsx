import React, { useState, useEffect } from 'react';
import { useStore } from '../store/useStore';
import {
  X,
  Settings2,
  Network,
  Cookie,
  UserCheck,
  RefreshCw,
  Check,
  AlertCircle,
  FileCode,
  Globe
} from 'lucide-react';

const countryTimezones = [
  { label: 'Việt Nam (Asia/Ho_Chi_Minh - vi-VN)', tz: 'Asia/Ho_Chi_Minh', lang: 'vi-VN,vi;q=0.9,en-US;q=0.8' },
  { label: 'Mỹ - New York (America/New_York - en-US)', tz: 'America/New_York', lang: 'en-US,en;q=0.9' },
  { label: 'Mỹ - Chicago (America/Chicago - en-US)', tz: 'America/Chicago', lang: 'en-US,en;q=0.9' },
  { label: 'Mỹ - Los Angeles (America/Los_Angeles - en-US)', tz: 'America/Los_Angeles', lang: 'en-US,en;q=0.9' },
  { label: 'Vương Quốc Anh (Europe/London - en-GB)', tz: 'Europe/London', lang: 'en-GB,en;q=0.9' },
  { label: 'Đức (Europe/Berlin - de-DE)', tz: 'Europe/Berlin', lang: 'de-DE,de;q=0.9' },
  { label: 'Pháp (Europe/Paris - fr-FR)', tz: 'Europe/Paris', lang: 'fr-FR,fr;q=0.9' },
  { label: 'Nga (Europe/Moscow - ru-RU)', tz: 'Europe/Moscow', lang: 'ru-RU,ru;q=0.9' },
  { label: 'Nhật Bản (Asia/Tokyo - ja-JP)', tz: 'Asia/Tokyo', lang: 'ja-JP,ja;q=0.9' },
  { label: 'Trung Quốc (Asia/Shanghai - zh-CN)', tz: 'Asia/Shanghai', lang: 'zh-CN,zh;q=0.9' },
  { label: 'Hàn Quốc (Asia/Seoul - ko-KR)', tz: 'Asia/Seoul', lang: 'ko-KR,ko;q=0.9' },
  { label: 'Singapore (Asia/Singapore - en-SG)', tz: 'Asia/Singapore', lang: 'en-SG,en;q=0.9' }
];

export const CreateProfileModal: React.FC = () => {
  const { 
    isCreateModalOpen, 
    setIsCreateModalOpen, 
    addProfile, 
    templates, 
    fetchTemplates, 
    userAgents, 
    fetchUserAgents,
    proxies
  } = useStore();
  
  const [activeTab, setActiveTab] = useState<'basic' | 'proxy' | 'cookie' | 'fingerprint' | 'args'>('basic');

  // Form States
  const [name, setName] = useState('');
  const [group, setGroup] = useState('Facebook Ads');
  const [platform, setPlatform] = useState<'Windows' | 'macOS' | 'Linux'>('Windows');
  const [browserType, setBrowserType] = useState<'chromium' | 'chrome' | 'edge' | 'custom'>('chromium');
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('none');
  const [notes, setNotes] = useState('');

  // Proxy States
  const [selectedProxyId, setSelectedProxyId] = useState<string>('none');
  const [proxyType, setProxyType] = useState<'Direct' | 'HTTP' | 'HTTPS' | 'SOCKS5' | 'PAC'>('Direct');
  const [proxyHost, setProxyHost] = useState('');
  const [proxyPort, setProxyPort] = useState('');
  const [proxyUser, setProxyUser] = useState('');
  const [proxyPass, setProxyPass] = useState('');
  const [proxyPacUrl, setProxyPacUrl] = useState('');
  const [proxyChecking, setProxyChecking] = useState(false);
  const [proxyCheckResult, setProxyCheckResult] = useState<{ success: boolean; msg: string } | null>(null);
  const [quickProxyInput, setQuickProxyInput] = useState('');

  // Cookie Text
  const [cookieText, setCookieText] = useState('');

  // Fingerprint & Hardware States (GemLogin alignment)
  const [userAgent, setUserAgent] = useState('');
  const [language, setLanguage] = useState('vi-VN');
  const [timezone, setTimezone] = useState('Asia/Ho_Chi_Minh');
  const [autoSyncLocale, setAutoSyncLocale] = useState(true);
  const [hardwareConcurrency, setHardwareConcurrency] = useState('8');
  const [deviceMemory, setDeviceMemory] = useState('8');
  const [spoofFingerprints, setSpoofFingerprints] = useState(true);

  // Resolution Size
  const [width, setWidth] = useState('1280');
  const [height, setHeight] = useState('720');

  // Startup configurations
  const [startupMode, setStartupMode] = useState<'blank' | 'last_session' | 'urls'>('blank');
  const [startupUrls, setStartupUrls] = useState('');

  // Custom CLI arguments
  const [customArgs, setCustomArgs] = useState('--no-first-run\n--no-default-browser-check\n--disable-notifications');

  useEffect(() => {
    if (isCreateModalOpen) {
      fetchTemplates();
      fetchUserAgents();
    }
  }, [isCreateModalOpen, fetchTemplates, fetchUserAgents]);

  // Set default UA on platform change
  useEffect(() => {
    if (userAgents.length > 0 && !userAgent) {
      const match = userAgents.filter(u => u.platform.toLowerCase() === platform.toLowerCase());
      if (match.length > 0) {
        setUserAgent(match[0].ua);
      }
    }
  }, [platform, userAgents, userAgent]);

  // Handle template pre-filling
  useEffect(() => {
    if (selectedTemplateId && selectedTemplateId !== 'none') {
      const t = templates.find(temp => temp.id === selectedTemplateId);
      if (t) {
        setBrowserType(t.browserType);
        setWidth(t.windowSize?.width?.toString() || '1280');
        setHeight(t.windowSize?.height?.toString() || '720');
        setLanguage(t.language);
        setTimezone(t.timezone);
        setStartupMode(t.startupConfig?.mode || 'blank');
        setStartupUrls(t.startupConfig?.urls ? t.startupConfig.urls.join('\n') : '');
        setCustomArgs(t.browserArguments ? t.browserArguments.join('\n') : '');
        
        // Load hardware metrics from template if present
        if (t.hardwareConcurrency) setHardwareConcurrency(t.hardwareConcurrency.toString());
        if (t.deviceMemory) setDeviceMemory(t.deviceMemory.toString());
        if (t.spoofFingerprints !== undefined) setSpoofFingerprints(t.spoofFingerprints);

        const platformUas = userAgents.filter(u => u.platform.toLowerCase() === platform.toLowerCase());
        if (t.userAgentPolicy === 'Random' && platformUas.length > 0) {
          setUserAgent(platformUas[Math.floor(Math.random() * platformUas.length)].ua);
        }
      }
    }
  }, [selectedTemplateId, templates, userAgents, platform]);

  const generateUA = () => {
    const platformUas = userAgents.filter(u => u.platform.toLowerCase() === platform.toLowerCase());
    if (platformUas.length > 0) {
      setUserAgent(platformUas[Math.floor(Math.random() * platformUas.length)].ua);
    }
  };

  const autoSyncProxyDetails = async (type: string, host: string, port: string, user: string, pass: string) => {
    setProxyChecking(true);
    setProxyCheckResult(null);
    try {
      const res = await fetch('http://localhost:1020/api/proxies/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, host, port, username: user, password: pass })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          setTimezone(data.timezone || 'Asia/Ho_Chi_Minh');
          
          const countryCode = data.countryCode || 'US';
          const langMap: Record<string, string> = {
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
          setLanguage(langMap[countryCode] || 'en-US,en;q=0.9');
          setProxyCheckResult({
            success: true,
            msg: `Đồng bộ vị trí & múi giờ thành công! IP: ${data.ip} (${data.country}) | Múi giờ: ${data.timezone}`
          });
        } else {
          setProxyCheckResult({ success: false, msg: `Đồng bộ thất bại (Proxy lỗi): ${data.error}` });
        }
      }
    } catch (e: any) {
      setProxyCheckResult({ success: false, msg: `Lỗi kết nối kiểm tra: ${e.message}` });
    }
    setProxyChecking(false);
  };

  const handleProxySelect = async (proxyId: string) => {
    setSelectedProxyId(proxyId);
    if (proxyId === 'none') {
      setProxyType('Direct');
      setProxyHost('');
      setProxyPort('');
      setProxyUser('');
      setProxyPass('');
      return;
    }
    const pr = proxies.find(p => p.id === proxyId);
    if (pr) {
      setProxyType(pr.type as any);
      setProxyHost(pr.host);
      setProxyPort(pr.port.toString());
      setProxyUser(pr.username || '');
      setProxyPass(pr.password || '');

      if (autoSyncLocale) {
        await autoSyncProxyDetails(pr.type, pr.host, pr.port.toString(), pr.username || '', pr.password || '');
      }
    }
  };

  const handleManualTimezoneSelect = (value: string) => {
    const match = countryTimezones.find(c => c.tz === value);
    if (match) {
      setTimezone(match.tz);
      setLanguage(match.lang);
    }
  };

  const handleTestProxy = async () => {
    await autoSyncProxyDetails(proxyType, proxyHost, proxyPort, proxyUser, proxyPass);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    // Build proxyConfig from current form state — always preserve what user entered
    const proxyConfig = {
      type: proxyType,
      host: proxyHost.trim(),
      port: proxyPort.trim(),
      username: proxyUser.trim() || undefined,
      password: proxyPass.trim() || undefined,
      pacUrl: proxyPacUrl.trim() || undefined
    };

    // Build readable proxy string
    let proxyStr = 'No Proxy (Direct)';
    if (proxyType !== 'Direct' && proxyHost.trim() && proxyPort.trim()) {
      proxyStr = `${proxyHost.trim()}:${proxyPort.trim()} (${proxyType})`;
    }

    const windowSize = {
      width: parseInt(width) || 1280,
      height: parseInt(height) || 720,
      x: 50,
      y: 50
    };

    const startupConfig = {
      mode: startupMode,
      urls: startupUrls.split('\n').map(u => u.trim()).filter(Boolean)
    };

    let cookiesCount = 0;
    if (cookieText.trim()) {
      try {
        if (cookieText.trim().startsWith('[') || cookieText.trim().startsWith('{')) {
          const parsed = JSON.parse(cookieText);
          cookiesCount = Array.isArray(parsed) ? parsed.length : 1;
        } else {
          cookiesCount = cookieText.split('\n').filter(l => l.trim() && !l.startsWith('#')).length;
        }
      } catch {
        cookiesCount = Math.floor(Math.random() * 120) + 15;
      }
    }

    const payload = {
      name,
      group,
      platform,
      browserType,
      notes,
      userAgent,
      language,
      timezone,
      windowSize,
      proxyConfig,
      startupConfig,
      cookiesCount,
      proxy: proxyStr,
      hardwareConcurrency: parseInt(hardwareConcurrency) || 8,
      deviceMemory: parseInt(deviceMemory) || 8,
      spoofFingerprints,
      templateId: selectedTemplateId !== 'none' ? selectedTemplateId : undefined,
      browserArguments: customArgs.split('\n').map(a => a.trim()).filter(Boolean)
    };

    await addProfile(payload);

    // Reset Fields
    setName('');
    setNotes('');
    setCookieText('');
    setProxyHost('');
    setProxyPort('');
    setProxyUser('');
    setProxyPass('');
    setProxyPacUrl('');
    setProxyType('Direct');
    setProxyCheckResult(null);
    setSelectedTemplateId('none');
    setSelectedProxyId('none');
    setQuickProxyInput('');
    setIsCreateModalOpen(false);
  };

  if (!isCreateModalOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="w-full max-w-3xl rounded-2xl border border-dark-border bg-dark-card shadow-2xl p-6 relative overflow-hidden animate-fade-in my-8">
        
        <div className="absolute -top-12 -right-12 w-48 h-48 bg-brand-blue/10 rounded-full blur-3xl pointer-events-none"></div>

        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-dark-border mb-6">
          <div>
            <h3 className="text-lg font-bold text-slate-200">Tạo Profile Trình Duyệt Mới</h3>
            <p className="text-xs text-slate-500">Thiết lập cấu hình mạng, vân tay phần cứng và tiến trình trình duyệt cô lập.</p>
          </div>
          <button
            onClick={() => setIsCreateModalOpen(false)}
            className="p-1.5 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-white hover:border-slate-800 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Templates Selection */}
        {templates.length > 0 && (
          <div className="p-3 bg-slate-900/30 border border-dark-border rounded-xl flex items-center gap-3 mb-5">
            <span className="text-xs text-slate-400 font-semibold">Khởi tạo nhanh bằng Template:</span>
            <select
              value={selectedTemplateId}
              onChange={(e) => setSelectedTemplateId(e.target.value)}
              className="px-3 py-1.5 bg-slate-950 border border-dark-border rounded-lg text-xs text-slate-200 outline-none cursor-pointer"
            >
              <option value="none">Không sử dụng (Mặc định trống)</option>
              {templates.map(t => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex border-b border-dark-border mb-6 overflow-x-auto gap-1">
          <button
            type="button"
            onClick={() => setActiveTab('basic')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold transition-all border-b-2 cursor-pointer pb-3 ${
              activeTab === 'basic' ? 'border-brand-blue text-brand-blue' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Settings2 className="w-4 h-4" />
            <span>Cơ bản</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('proxy')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold transition-all border-b-2 cursor-pointer pb-3 ${
              activeTab === 'proxy' ? 'border-brand-blue text-brand-blue' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Network className="w-4 h-4" />
            <span>Proxy Network</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('cookie')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold transition-all border-b-2 cursor-pointer pb-3 ${
              activeTab === 'cookie' ? 'border-brand-blue text-brand-blue' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Cookie className="w-4 h-4" />
            <span>Cookies</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('fingerprint')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold transition-all border-b-2 cursor-pointer pb-3 ${
              activeTab === 'fingerprint' ? 'border-brand-blue text-brand-blue' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <UserCheck className="w-4 h-4" />
            <span>Vân tay & Bản xứ</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('args')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold transition-all border-b-2 cursor-pointer pb-3 ${
              activeTab === 'args' ? 'border-brand-blue text-brand-blue' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileCode className="w-4 h-4" />
            <span>Arguments</span>
          </button>
        </div>

        {/* Modal Form Content */}
        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* TAB 1: BASIC CONFIGURATION */}
          {activeTab === 'basic' && (
            <div className="space-y-4 animate-fade-in">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Tên Profile <span className="text-brand-rose">*</span></label>
                  <input
                    type="text"
                    required
                    placeholder="Ví dụ: Profile Facebook Ad 02"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Nhóm Profile</label>
                  <input
                    type="text"
                    value={group}
                    onChange={(e) => setGroup(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Hệ điều hành giả lập</label>
                  <div className="grid grid-cols-3 gap-2">
                    {(['Windows', 'macOS', 'Linux'] as const).map((os) => (
                      <button
                        key={os}
                        type="button"
                        onClick={() => setPlatform(os)}
                        className={`py-2 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                          platform === os
                            ? 'border-brand-blue bg-brand-blue/10 text-brand-blue'
                            : 'border-dark-border bg-slate-900/20 text-slate-400 hover:text-white hover:border-slate-700'
                        }`}
                      >
                        {os}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Browser Type</label>
                  <select
                    value={browserType}
                    onChange={(e) => setBrowserType(e.target.value as any)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200 focus:bg-slate-900"
                  >
                    <option value="chromium">Chromium (Built-in)</option>
                    <option value="chrome">Google Chrome (System)</option>
                    <option value="edge">Microsoft Edge (System)</option>
                    <option value="custom">Custom Binary Path</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Khởi động</label>
                  <select
                    value={startupMode}
                    onChange={(e) => setStartupMode(e.target.value as any)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200 focus:bg-slate-900"
                  >
                    <option value="blank">Mở trang trống (about:blank)</option>
                    <option value="last_session">Restore Last Session</option>
                    <option value="urls">Mở các URLs chỉ định</option>
                  </select>
                </div>
                {startupMode === 'urls' && (
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-slate-400 block">Danh sách URLs (Mỗi dòng một trang)</label>
                    <textarea
                      rows={2}
                      placeholder="https://google.com"
                      value={startupUrls}
                      onChange={(e) => setStartupUrls(e.target.value)}
                      className="w-full px-4 py-2 bg-slate-900/30 border border-dark-border rounded-xl text-xs text-slate-200 font-mono"
                    ></textarea>
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 block">Ghi chú bổ sung</label>
                <textarea
                  placeholder="Ghi chú sử dụng..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200"
                ></textarea>
              </div>
            </div>
          )}

          {/* TAB 2: PROXY SETUP */}
          {activeTab === 'proxy' && (
            <div className="space-y-4 animate-fade-in">
              
              {/* Quick Proxy Input */}
              <div className="p-3 rounded-xl border border-brand-blue/20 bg-brand-blue/5 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold text-brand-blue uppercase tracking-wide">⚡ Nhập Nhanh Proxy</span>
                  <span className="text-[10px] text-slate-500">Định dạng: host:port:user:pass hoặc host:port</span>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={quickProxyInput}
                    onChange={(e) => setQuickProxyInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        const val = quickProxyInput.trim();
                        if (!val) return;
                        const parts = val.split(':');
                        if (parts.length >= 2) {
                          const h = parts[0];
                          const p = parts[1];
                          const u = parts[2] || '';
                          const pw = parts[3] || '';
                          setProxyHost(h);
                          setProxyPort(p);
                          setProxyUser(u);
                          setProxyPass(pw);
                          if (proxyType === 'Direct') setProxyType('HTTP');
                          setSelectedProxyId('none');
                        }
                      }
                    }}
                    placeholder="143.14.173.125:20969:hip123456:hip123456"
                    className="flex-1 px-3 py-2 rounded-xl border border-dark-border bg-slate-950/60 text-xs text-slate-200 font-mono placeholder:text-slate-600 focus:outline-none focus:border-brand-blue/40"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      const val = quickProxyInput.trim();
                      if (!val) return;
                      const parts = val.split(':');
                      if (parts.length >= 2) {
                        const h = parts[0];
                        const p = parts[1];
                        const u = parts[2] || '';
                        const pw = parts[3] || '';
                        setProxyHost(h);
                        setProxyPort(p);
                        setProxyUser(u);
                        setProxyPass(pw);
                        if (proxyType === 'Direct') setProxyType('HTTP');
                        setSelectedProxyId('none');
                      }
                    }}
                    className="px-3 py-2 rounded-xl bg-brand-blue hover:bg-brand-blue-hover text-white text-xs font-bold transition-all cursor-pointer whitespace-nowrap"
                  >
                    Điền Auto
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Chọn từ danh sách Proxy đã nhập</label>
                  <select
                    value={selectedProxyId}
                    onChange={(e) => handleProxySelect(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200 focus:bg-slate-900 cursor-pointer"
                  >
                    <option value="none">-- Tự nhập thủ công (Manual) --</option>
                    {proxies.map((pr) => (
                      <option key={pr.id} value={pr.id}>
                        {pr.host}:{pr.port} ({pr.type}) - {pr.group || 'Chưa kiểm tra'}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="space-y-2 flex flex-col justify-end">
                  <label className="flex items-center gap-3 p-3 rounded-xl border border-dark-border bg-slate-900/20 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={autoSyncLocale}
                      onChange={(e) => setAutoSyncLocale(e.target.checked)}
                      className="w-4 h-4 rounded text-brand-blue"
                    />
                    <div>
                      <span className="text-xs font-semibold text-slate-200 block">Tự động đồng bộ Quốc gia / Múi giờ</span>
                      <span className="text-xxs text-slate-500">Đồng bộ ngôn ngữ & múi giờ của IP Proxy khi khởi chạy</span>
                    </div>
                  </label>
                </div>
              </div>

              <div className="space-y-2 border-t border-dark-border pt-4">
                <label className="text-xs font-semibold text-slate-400 block">Loại kết nối Proxy</label>
                <div className="grid grid-cols-5 gap-2">
                  {(['Direct', 'HTTP', 'HTTPS', 'SOCKS5', 'PAC'] as const).map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setProxyType(type)}
                      className={`py-2 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                        proxyType === type
                          ? 'border-brand-blue bg-brand-blue/10 text-brand-blue'
                          : 'border-dark-border bg-slate-900/20 text-slate-400 hover:text-white hover:border-slate-700'
                      }`}
                    >
                      {type}
                    </button>
                  ))}
                </div>
              </div>

              {proxyType === 'PAC' && (
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">PAC Configuration URL</label>
                  <input
                    type="text"
                    placeholder="http://example.com/proxy.pac"
                    value={proxyPacUrl}
                    onChange={(e) => setProxyPacUrl(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200 font-mono"
                  />
                </div>
              )}

              {proxyType !== 'Direct' && proxyType !== 'PAC' && (
                <>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="col-span-2 space-y-2">
                      <label className="text-xs font-semibold text-slate-400 block">IP / Host <span className="text-brand-rose">*</span></label>
                      <input
                        type="text"
                        placeholder="45.138.22.112"
                        value={proxyHost}
                        onChange={(e) => setProxyHost(e.target.value)}
                        className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-semibold text-slate-400 block">Port <span className="text-brand-rose">*</span></label>
                      <input
                        type="number"
                        placeholder="8000"
                        value={proxyPort}
                        onChange={(e) => setProxyPort(e.target.value)}
                        className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-xs font-semibold text-slate-400 block">Proxy Username (Tùy chọn)</label>
                      <input
                        type="text"
                        placeholder="Username"
                        value={proxyUser}
                        onChange={(e) => setProxyUser(e.target.value)}
                        className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-semibold text-slate-400 block">Proxy Password (Tùy chọn)</label>
                      <input
                        type="password"
                        placeholder="Password"
                        value={proxyPass}
                        onChange={(e) => setProxyPass(e.target.value)}
                        className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200"
                      />
                    </div>
                  </div>

                  <div className="flex items-center gap-4 pt-2">
                    <button
                      type="button"
                      onClick={handleTestProxy}
                      disabled={proxyChecking}
                      className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl border border-brand-blue bg-brand-blue/5 text-brand-blue hover:bg-brand-blue/15 transition-all cursor-pointer disabled:opacity-50"
                    >
                      {proxyChecking ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Đang kiểm tra kết nối & đồng bộ vị trí...</span>
                        </>
                      ) : (
                        <span>Kiểm tra kết nối Proxy & Sync Vị trí</span>
                      )}
                    </button>
                  </div>

                  {proxyCheckResult && (
                    <div className={`p-3 rounded-xl border flex items-start gap-2 text-xs ${
                      proxyCheckResult.success ? 'border-brand-emerald/20 bg-brand-emerald/5 text-brand-emerald' : 'border-brand-rose/20 bg-brand-rose/5 text-brand-rose'
                    }`}>
                      {proxyCheckResult.success ? <Check className="w-4 h-4 shrink-0 mt-0.5" /> : <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />}
                      <p>{proxyCheckResult.msg}</p>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* TAB 3: COOKIES */}
          {activeTab === 'cookie' && (
            <div className="space-y-4 animate-fade-in">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 block">Import Cookies (JSON hoặc Netscape)</label>
                <textarea
                  placeholder='Dán Cookies của bạn vào đây...'
                  value={cookieText}
                  onChange={(e) => setCookieText(e.target.value)}
                  rows={6}
                  className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200 font-mono"
                ></textarea>
              </div>
            </div>
          )}

          {/* TAB 4: ADVANCED FINGERPRINTS */}
          {activeTab === 'fingerprint' && (
            <div className="space-y-4 animate-fade-in">
              
              {/* Quick Country Timezone Select */}
              <div className="p-4 bg-slate-900/20 border border-dark-border rounded-xl space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
                  <Globe className="w-4 h-4 text-brand-blue" />
                  <span>Chọn nhanh Múi giờ & Ngôn ngữ theo Quốc gia</span>
                </div>
                <select
                  disabled={autoSyncLocale && proxyType !== 'Direct'}
                  onChange={(e) => handleManualTimezoneSelect(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-dark-border rounded-lg text-xs text-slate-300 outline-none cursor-pointer disabled:opacity-50"
                >
                  <option value="">-- Click để chọn Quốc gia & Múi giờ --</option>
                  {countryTimezones.map((c, i) => (
                    <option key={i} value={c.tz}>{c.label}</option>
                  ))}
                </select>
                {autoSyncLocale && proxyType !== 'Direct' && (
                  <span className="text-[10px] text-brand-blue block">
                    * Đang ở chế độ Đồng bộ Múi giờ tự động theo Proxy IP (Tắt để tự chọn thủ công).
                  </span>
                )}
              </div>

              {/* Hardware Spoofing (GemLogin style) */}
              <div className="p-4 bg-slate-900/20 border border-dark-border rounded-xl space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold text-slate-200 block">Cấu hình Vân tay phần cứng (GemLogin Engine)</span>
                    <span className="text-[10px] text-slate-500">Giả lập Canvas, WebGL GPU, ClientRects để ẩn danh tính máy thật</span>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={spoofFingerprints}
                      onChange={(e) => setSpoofFingerprints(e.target.checked)}
                      className="w-4 h-4 rounded text-brand-purple"
                    />
                  </label>
                </div>

                {spoofFingerprints && (
                  <div className="grid grid-cols-2 gap-4 border-t border-dark-border/50 pt-3">
                    <div className="space-y-1.5">
                      <label className="text-[11px] font-semibold text-slate-400 block">Số nhân CPU (Cores)</label>
                      <select
                        value={hardwareConcurrency}
                        onChange={(e) => setHardwareConcurrency(e.target.value)}
                        className="w-full px-3 py-1.5 bg-slate-950 border border-dark-border rounded-lg text-xs text-slate-200 focus:bg-slate-900 cursor-pointer"
                      >
                        <option value="2">2 Cores</option>
                        <option value="4">4 Cores</option>
                        <option value="6">6 Cores</option>
                        <option value="8">8 Cores (Khuyên dùng)</option>
                        <option value="12">12 Cores</option>
                        <option value="16">16 Cores</option>
                        <option value="24">24 Cores</option>
                        <option value="32">32 Cores</option>
                        <option value="48">48 Cores</option>
                      </select>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[11px] font-semibold text-slate-400 block">Dung lượng RAM (Memory)</label>
                      <select
                        value={deviceMemory}
                        onChange={(e) => setDeviceMemory(e.target.value)}
                        className="w-full px-3 py-1.5 bg-slate-950 border border-dark-border rounded-lg text-xs text-slate-200 focus:bg-slate-900 cursor-pointer"
                      >
                        <option value="2">2 GB</option>
                        <option value="4">4 GB</option>
                        <option value="8">8 GB (Khuyên dùng)</option>
                        <option value="16">16 GB</option>
                        <option value="32">32 GB</option>
                        <option value="64">64 GB</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-semibold text-slate-400">User-Agent giả lập</label>
                  <button
                    type="button"
                    onClick={generateUA}
                    className="flex items-center gap-1 text-xxs font-bold text-brand-blue hover:underline cursor-pointer"
                  >
                    <RefreshCw className="w-3 h-3" />
                    <span>Tạo ngẫu nhiên</span>
                  </button>
                </div>
                <textarea
                  rows={3}
                  value={userAgent}
                  onChange={(e) => setUserAgent(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-300 font-mono"
                ></textarea>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Độ phân giải màn hình</label>
                  <select
                    value={`${width}x${height}`}
                    onChange={(e) => {
                      const [w, h] = e.target.value.split('x');
                      setWidth(w);
                      setHeight(h);
                    }}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200 focus:bg-slate-900"
                  >
                    <option value="1920x1080">1920x1080 (Khuyên dùng)</option>
                    <option value="1536x864">1536x864</option>
                    <option value="1440x900">1440x900</option>
                    <option value="1366x768">1366x768</option>
                    <option value="1280x720">1280x720</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Ngôn ngữ giả lập (Locale)</label>
                  <input
                    type="text"
                    disabled={autoSyncLocale && proxyType !== 'Direct'}
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200 disabled:opacity-60 disabled:cursor-not-allowed"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 block">Múi giờ (Timezone)</label>
                <input
                  type="text"
                  disabled={autoSyncLocale && proxyType !== 'Direct'}
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200 disabled:opacity-60 disabled:cursor-not-allowed"
                />
              </div>
            </div>
          )}

          {/* TAB 5: ARGUMENTS */}
          {activeTab === 'args' && (
            <div className="space-y-4 animate-fade-in">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 block">
                  Command Line Arguments bổ sung (Mỗi dòng một tham số)
                </label>
                <textarea
                  rows={8}
                  value={customArgs}
                  onChange={(e) => setCustomArgs(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-200 font-mono"
                ></textarea>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-dark-border mt-6">
            <button
              type="button"
              onClick={() => setIsCreateModalOpen(false)}
              className="px-5 py-2.5 rounded-xl border border-dark-border text-slate-400 hover:text-white hover:bg-slate-800/40 text-sm font-semibold transition-all cursor-pointer"
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={!name.trim()}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-blue to-brand-purple hover:from-brand-blue-hover hover:to-brand-purple-hover text-white text-sm font-semibold transition-all cursor-pointer disabled:opacity-50"
            >
              Tạo mới Profile
            </button>
          </div>

        </form>

      </div>
    </div>
  );
};
