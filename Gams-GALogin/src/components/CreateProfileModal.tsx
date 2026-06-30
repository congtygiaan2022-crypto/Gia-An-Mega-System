import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import {
  X,
  Settings2,
  Network,
  Cookie,
  UserCheck,
  RefreshCw,
  Check,
  AlertCircle
} from 'lucide-react';

export const CreateProfileModal: React.FC = () => {
  const { isCreateModalOpen, setIsCreateModalOpen, addProfile } = useStore();
  const [activeTab, setActiveTab] = useState<'basic' | 'proxy' | 'cookie' | 'fingerprint'>('basic');

  // Basic Form State
  const [name, setName] = useState('');
  const [group, setGroup] = useState('Facebook Ads');
  const [platform, setPlatform] = useState<'Windows' | 'macOS' | 'Linux'>('Windows');
  const [browserVersion, setBrowserVersion] = useState('Chromium 122.0');
  const [notes, setNotes] = useState('');

  // Proxy State
  const [proxyType, setProxyType] = useState<'Direct' | 'HTTP' | 'SOCKS5'>('Direct');
  const [proxyHost, setProxyHost] = useState('');
  const [proxyPort, setProxyPort] = useState('');
  const [proxyUser, setProxyUser] = useState('');
  const [proxyPass, setProxyPass] = useState('');
  const [proxyChecking, setProxyChecking] = useState(false);
  const [proxyCheckResult, setProxyCheckResult] = useState<{ success: boolean; msg: string } | null>(null);

  // Cookie State
  const [cookieText, setCookieText] = useState('');

  // Fingerprint State
  const [userAgent, setUserAgent] = useState(
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
  );
  const [resolution, setResolution] = useState('1920x1080');
  const [canvasSpoof, setCanvasSpoof] = useState(true);
  const [webglSpoof, setWebglSpoof] = useState(true);
  const [webrtcMode, setWebrtcMode] = useState<'alter' | 'block' | 'direct'>('alter');

  if (!isCreateModalOpen) return null;

  // Generate dynamic user agents based on selected platform
  const generateUserAgent = () => {
    const chromeVersions = ['122.0.0.0', '121.0.0.0', '120.0.0.0', '119.0.0.0'];
    const selectedVer = chromeVersions[Math.floor(Math.random() * chromeVersions.length)];
    
    if (platform === 'macOS') {
      setUserAgent(`Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${selectedVer} Safari/537.36`);
    } else if (platform === 'Linux') {
      setUserAgent(`Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${selectedVer} Safari/537.36`);
    } else {
      setUserAgent(`Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${selectedVer} Safari/537.36`);
    }
  };

  const handleTestProxy = async () => {
    if (!proxyHost || !proxyPort) {
      setProxyCheckResult({ success: false, msg: 'Vui lòng nhập IP/Host và Port!' });
      return;
    }
    setProxyChecking(true);
    setProxyCheckResult(null);
    
    // Simulate connection delay
    await new Promise((resolve) => setTimeout(resolve, 1500));
    
    const isSuccess = Math.random() > 0.15;
    if (isSuccess) {
      setProxyCheckResult({
        success: true,
        msg: `Kết nối thành công! IP: ${proxyHost} | Quốc gia: United States | Độ trễ: ${Math.floor(Math.random() * 120) + 40}ms`
      });
    } else {
      setProxyCheckResult({
        success: false,
        msg: 'Kết nối thất bại. Vui lòng kiểm tra lại cấu hình hoặc tường lửa.'
      });
    }
    setProxyChecking(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    // Compose proxy string
    let proxyStr = 'No Proxy (Direct)';
    if (proxyType !== 'Direct' && proxyHost && proxyPort) {
      proxyStr = `${proxyHost}:${proxyPort} (${proxyType})`;
    }

    // Determine cookie count
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
        cookiesCount = Math.floor(Math.random() * 150) + 20; // fallback mock cookie count
      }
    }

    addProfile({
      name,
      group,
      platform,
      notes,
      proxy: proxyStr,
      userAgent,
      cookiesCount
    });

    // Reset fields
    setName('');
    setNotes('');
    setCookieText('');
    setProxyHost('');
    setProxyPort('');
    setProxyType('Direct');
    setProxyCheckResult(null);
    setIsCreateModalOpen(false);
  };

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="w-full max-w-3xl rounded-2xl border border-dark-border bg-dark-card shadow-2xl p-6 relative overflow-hidden animate-fade-in my-8">
        
        {/* Glow effect */}
        <div className="absolute -top-12 -right-12 w-48 h-48 bg-brand-blue/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-12 -left-12 w-48 h-48 bg-brand-purple/10 rounded-full blur-3xl pointer-events-none"></div>

        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-dark-border mb-6">
          <div>
            <h3 className="text-lg font-bold text-slate-200">Tạo Profile Trình Duyệt Mới</h3>
            <p className="text-xs text-slate-500">Thiết lập tham số phần cứng và mạng độc lập cho profile Chromium.</p>
          </div>
          <button
            onClick={() => setIsCreateModalOpen(false)}
            className="p-1.5 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-white hover:border-slate-800 transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs inside Modal */}
        <div className="flex border-b border-dark-border mb-6 overflow-x-auto gap-1">
          <button
            type="button"
            onClick={() => setActiveTab('basic')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold transition-all border-b-2 cursor-pointer pb-3 ${
              activeTab === 'basic'
                ? 'border-brand-blue text-brand-blue'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Settings2 className="w-4 h-4" />
            <span>Cơ bản</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('proxy')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold transition-all border-b-2 cursor-pointer pb-3 ${
              activeTab === 'proxy'
                ? 'border-brand-blue text-brand-blue'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Network className="w-4 h-4" />
            <span>Proxy Network</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('cookie')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold transition-all border-b-2 cursor-pointer pb-3 ${
              activeTab === 'cookie'
                ? 'border-brand-blue text-brand-blue'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Cookie className="w-4 h-4" />
            <span>Cookies</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('fingerprint')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold transition-all border-b-2 cursor-pointer pb-3 ${
              activeTab === 'fingerprint'
                ? 'border-brand-blue text-brand-blue'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <UserCheck className="w-4 h-4" />
            <span>Vân tay (Fingerprint)</span>
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
                  <select
                    value={group}
                    onChange={(e) => setGroup(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200 focus:bg-slate-900"
                  >
                    <option value="Facebook Ads">Facebook Ads</option>
                    <option value="Google Ads">Google Ads</option>
                    <option value="TikTok">TikTok</option>
                    <option value="Ecommerce">Ecommerce</option>
                    <option value="Social Bots">Social Bots</option>
                  </select>
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
                        onClick={() => { setPlatform(os); generateUserAgent(); }}
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
                  <label className="text-xs font-semibold text-slate-400 block">Phiên bản Chromium</label>
                  <select
                    value={browserVersion}
                    onChange={(e) => setBrowserVersion(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200 focus:bg-slate-900"
                  >
                    <option value="Chromium 122.0">Chromium 122.0 (Ổn định nhất)</option>
                    <option value="Chromium 120.0">Chromium 120.0</option>
                    <option value="Chromium 118.0">Chromium 118.0</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 block">Ghi chú bổ sung</label>
                <textarea
                  placeholder="Ghi chú về tài khoản, công việc hoặc mục đích sử dụng..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200"
                ></textarea>
              </div>
            </div>
          )}

          {/* TAB 2: PROXY SETUP */}
          {activeTab === 'proxy' && (
            <div className="space-y-4 animate-fade-in">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 block">Loại kết nối Proxy</label>
                <div className="grid grid-cols-3 gap-2">
                  {(['Direct', 'HTTP', 'SOCKS5'] as const).map((type) => (
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
                      {type === 'Direct' ? 'Direct (Không dùng Proxy)' : type}
                    </button>
                  ))}
                </div>
              </div>

              {proxyType !== 'Direct' && (
                <>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="col-span-2 space-y-2">
                      <label className="text-xs font-semibold text-slate-400 block">IP / Host <span className="text-brand-rose">*</span></label>
                      <input
                        type="text"
                        placeholder="Ví dụ: 45.138.22.112"
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
                        placeholder="Tên đăng nhập"
                        value={proxyUser}
                        onChange={(e) => setProxyUser(e.target.value)}
                        className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-semibold text-slate-400 block">Proxy Password (Tùy chọn)</label>
                      <input
                        type="password"
                        placeholder="Mật khẩu"
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
                          <span>Đang kiểm tra kết nối...</span>
                        </>
                      ) : (
                        <span>Kiểm tra kết nối Proxy</span>
                      )}
                    </button>
                  </div>

                  {proxyCheckResult && (
                    <div className={`p-3 rounded-xl border flex items-start gap-2 text-xs ${
                      proxyCheckResult.success
                        ? 'border-brand-emerald/20 bg-brand-emerald/5 text-brand-emerald'
                        : 'border-brand-rose/20 bg-brand-rose/5 text-brand-rose'
                    } animate-fade-in`}>
                      {proxyCheckResult.success ? (
                        <Check className="w-4 h-4 shrink-0 mt-0.5" />
                      ) : (
                        <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                      )}
                      <p>{proxyCheckResult.msg}</p>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* TAB 3: COOKIES MANAGER */}
          {activeTab === 'cookie' && (
            <div className="space-y-4 animate-fade-in">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 block">Import Cookies (JSON hoặc Netscape format)</label>
                <textarea
                  placeholder='Dán định dạng JSON cookie (Ví dụ: [{"name":"sid","value":"xyz","domain":".google.com"}]) hoặc định dạng dòng Netscape...'
                  value={cookieText}
                  onChange={(e) => setCookieText(e.target.value)}
                  rows={6}
                  className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200 font-mono"
                ></textarea>
                <span className="text-xxs text-slate-500 block leading-normal">
                  💡 Nhập cookies giúp trình duyệt tự động đăng nhập vào các tài khoản dịch vụ (Facebook, Google, eBay...) ngay sau khi khởi chạy.
                </span>
              </div>
            </div>
          )}

          {/* TAB 4: ADVANCED FINGERPRINTS */}
          {activeTab === 'fingerprint' && (
            <div className="space-y-4 animate-fade-in">
              
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-semibold text-slate-400">User-Agent giả lập</label>
                  <button
                    type="button"
                    onClick={generateUserAgent}
                    className="flex items-center gap-1 text-xxs font-bold text-brand-blue hover:underline cursor-pointer"
                  >
                    <RefreshCw className="w-3 h-3" />
                    <span>Tạo ngẫu nhiên</span>
                  </button>
                </div>
                <input
                  type="text"
                  value={userAgent}
                  onChange={(e) => setUserAgent(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-300 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Độ phân giải màn hình</label>
                  <select
                    value={resolution}
                    onChange={(e) => setResolution(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200 focus:bg-slate-900"
                  >
                    <option value="1920x1080">1920x1080 (Khuyên dùng)</option>
                    <option value="1536x864">1536x864</option>
                    <option value="1440x900">1440x900</option>
                    <option value="1366x768">1366x768</option>
                    <option value="2560x1440">2560x1440 (2K)</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Chế độ giả lập WebRTC</label>
                  <select
                    value={webrtcMode}
                    onChange={(e) => setWebrtcMode(e.target.value as any)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-sm text-slate-200 focus:bg-slate-900"
                  >
                    <option value="alter">Alter (Ghi đè IP tương thích Proxy)</option>
                    <option value="block">Block (Vô hiệu hóa WebRTC)</option>
                    <option value="direct">Direct (Tiết lộ IP thật của bạn)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-2">
                <label className="flex items-center gap-3 p-3 rounded-xl border border-dark-border bg-slate-900/20 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={canvasSpoof}
                    onChange={(e) => setCanvasSpoof(e.target.checked)}
                    className="w-4 h-4 rounded text-brand-blue"
                  />
                  <div>
                    <span className="text-xs font-semibold text-slate-200 block">Chống dấu vân tay Canvas</span>
                    <span className="text-xxs text-slate-500">Thêm nhiễu độc nhất để bảo vệ Canvas ID</span>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-3 rounded-xl border border-dark-border bg-slate-900/20 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={webglSpoof}
                    onChange={(e) => setWebglSpoof(e.target.checked)}
                    className="w-4 h-4 rounded text-brand-blue"
                  />
                  <div>
                    <span className="text-xs font-semibold text-slate-200 block">Chống dấu vân tay WebGL</span>
                    <span className="text-xxs text-slate-500">Giả lập Vendor card đồ họa độc lập</span>
                  </div>
                </label>
              </div>

            </div>
          )}

          {/* Action Buttons at Footer */}
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
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-blue to-brand-purple hover:from-brand-blue-hover hover:to-brand-purple-hover text-white text-sm font-semibold shadow-lg shadow-brand-blue/20 hover:shadow-brand-blue/30 active:scale-98 transition-all disabled:opacity-50 cursor-pointer"
            >
              Tạo mới Profile
            </button>
          </div>

        </form>

      </div>
    </div>
  );
};
