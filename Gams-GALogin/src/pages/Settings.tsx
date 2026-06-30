import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import {
  FolderOpen,
  CloudLightning,
  Sliders,
  ShieldAlert,
  Save,
  CheckCircle2
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { addLog, serverStatus, syncCloud } = useStore();

  const [browserPath, setBrowserPath] = useState('C:\\Program Files\\Gams-GALogin\\bin\\chromium\\chrome.exe');
  const [syncEnabled, setSyncEnabled] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState('');
  
  const [clearCacheOnClose, setClearCacheOnClose] = useState(true);
  const [syncHistory, setSyncHistory] = useState(false);
  const [startMinimized, setStartMinimized] = useState(false);

  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(true);
    addLog('Đã lưu thành công cấu hình hệ thống Gams-GALogin.', 'success');

    setTimeout(() => {
      setSaveSuccess(false);
    }, 2000);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-200">Cấu Hình Hệ Thống</h2>
        <p className="text-xs text-slate-500">Thiết lập các tùy chọn hoạt động mặc định, đường dẫn thư mục và đồng bộ hóa đám mây.</p>
      </div>

      <form onSubmit={handleSave} className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        
        {/* Left Columns: Core settings */}
        <div className="lg:col-span-2 space-y-5">
          
          {/* Path Settings Card */}
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
            <div className="flex items-center gap-2">
              <FolderOpen className="w-5 h-5 text-brand-blue" />
              <h4 className="text-sm font-bold text-slate-300">Đường dẫn trình duyệt & Thư mục Profile</h4>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 block">Đường dẫn Chromium Executable (chrome.exe)</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={browserPath}
                  onChange={(e) => setBrowserPath(e.target.value)}
                  className="flex-1 px-4 py-2.5 rounded-xl border border-dark-border bg-slate-950/40 text-xs text-slate-300 font-mono focus:bg-slate-900"
                />
                <button
                  type="button"
                  onClick={() => alert('Chọn file chrome.exe từ ổ cứng')}
                  className="px-4 py-2 text-xs font-semibold rounded-xl border border-dark-border bg-slate-900/40 hover:bg-slate-900 text-slate-300 transition-all cursor-pointer"
                >
                  Chọn tệp
                </button>
              </div>
              <span className="text-xxs text-slate-500 block leading-normal">
                ⚠️ Gams-GALogin tự động tải xuống phiên bản Chromium tối ưu. Bạn chỉ nên thay đổi đường dẫn này nếu muốn sử dụng phiên bản Chromium tùy chỉnh.
              </span>
            </div>
          </div>

          {/* Sync Settings Card */}
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <CloudLightning className="w-5 h-5 text-brand-purple" />
                <h4 className="text-sm font-bold text-slate-300">Đồng bộ hóa đám mây (Cloud Synchronization)</h4>
              </div>
              {/* Toggle Sync */}
              <button
                type="button"
                onClick={() => setSyncEnabled(!syncEnabled)}
                className={`w-9 h-5 rounded-full p-0.5 transition-colors duration-300 cursor-pointer ${
                  syncEnabled ? 'bg-brand-blue' : 'bg-slate-800'
                }`}
              >
                <div className={`w-4 h-4 rounded-full bg-white transition-transform duration-300 ${
                  syncEnabled ? 'translate-x-4' : 'translate-x-0'
                }`}></div>
              </button>
            </div>

            {syncEnabled && (
              <div className="space-y-4 animate-fade-in">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Đồng bộ Server Endpoint</label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      readOnly
                      value={serverStatus?.remoteSyncServer || 'http://giaancompany.io.vn'}
                      className="flex-1 px-4 py-2.5 rounded-xl border border-dark-border bg-slate-950/40 text-xs text-slate-400 font-mono cursor-not-allowed focus:outline-none"
                    />
                    <button
                      type="button"
                      disabled={isSyncing}
                      onClick={async () => {
                        setIsSyncing(true);
                        setSyncMessage('');
                        const res = await syncCloud();
                        setIsSyncing(false);
                        if (res.success) {
                          setSyncMessage(res.message);
                          setTimeout(() => setSyncMessage(''), 6000);
                        }
                      }}
                      className="px-4 py-2 text-xs font-semibold rounded-xl bg-brand-purple text-white hover:bg-brand-purple-hover transition-all cursor-pointer disabled:opacity-50"
                    >
                      {isSyncing ? 'Đang đồng bộ...' : 'Đồng bộ ngay'}
                    </button>
                  </div>
                  <span className="text-xxs text-slate-500 block leading-normal">
                    Đồng bộ hóa đám mây lưu trữ an toàn cookie, dấu trang, mật khẩu và dữ liệu biểu mẫu để truy cập từ các thiết bị khác thông qua kết nối an toàn đến website Gia An Company.
                  </span>
                </div>

                {syncMessage && (
                  <div className="p-3 rounded-xl bg-brand-emerald/10 border border-brand-emerald/20 text-xxs text-brand-emerald leading-relaxed">
                    {syncMessage}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Policy Settings Card */}
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
            <div className="flex items-center gap-2">
              <Sliders className="w-5 h-5 text-brand-cyan" />
              <h4 className="text-sm font-bold text-slate-300">Tùy chọn hoạt động & Dọn dẹp dữ liệu</h4>
            </div>

            <div className="space-y-3.5 pt-2">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={clearCacheOnClose}
                  onChange={(e) => setClearCacheOnClose(e.target.checked)}
                  className="rounded border-slate-700 text-brand-blue focus:ring-0 w-4 h-4 bg-slate-950/40"
                />
                <div>
                  <span className="text-xs font-semibold text-slate-200 block">Xóa cache trình duyệt khi đóng profile</span>
                  <span className="text-xxs text-slate-500">Tiết kiệm bộ nhớ ổ cứng, tránh bám đuôi theo dấu cookie lưu tạm.</span>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={syncHistory}
                  onChange={(e) => setSyncHistory(e.target.checked)}
                  className="rounded border-slate-700 text-brand-blue focus:ring-0 w-4 h-4 bg-slate-950/40"
                />
                <div>
                  <span className="text-xs font-semibold text-slate-200 block">Đồng bộ lịch sử duyệt web</span>
                  <span className="text-xxs text-slate-500">Giữ lịch sử truy cập của bạn trên đám mây để mở lại dễ dàng.</span>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={startMinimized}
                  onChange={(e) => setStartMinimized(e.target.checked)}
                  className="rounded border-slate-700 text-brand-blue focus:ring-0 w-4 h-4 bg-slate-950/40"
                />
                <div>
                  <span className="text-xs font-semibold text-slate-200 block">Khởi chạy thu nhỏ dưới khay hệ thống (System Tray)</span>
                  <span className="text-xxs text-slate-500">Giúp ứng dụng chạy ngầm, tiết kiệm diện tích màn hình desktop.</span>
                </div>
              </label>
            </div>
          </div>

        </div>

        {/* Right Column: Security Alert & Save action */}
        <div className="space-y-5">
          
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-brand-rose" />
              <h4 className="text-sm font-bold text-slate-300">Tình trạng bảo mật</h4>
            </div>

            <div className="p-3.5 rounded-xl border border-brand-emerald/20 bg-brand-emerald/5 text-brand-emerald text-xxs leading-relaxed">
              🔒 <strong>Đã bật bảo mật vân tay Canvas/WebGL:</strong> Phần mềm đang chặn rò rỉ WebGL Vendor & Font fingerprinting thành công.
            </div>

            <div className="p-3.5 rounded-xl border border-brand-blue/20 bg-brand-blue/5 text-brand-blue text-xxs leading-relaxed">
              📡 <strong>Cập nhật phiên bản:</strong> Bạn đang sử dụng Gams-GALogin v2.4.1 (Mới nhất).
            </div>
          </div>

          {/* SMTP Security Card */}
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-brand-purple" />
              <h4 className="text-sm font-bold text-slate-300">Bảo mật SMTP & Mail Domain</h4>
            </div>
            
            <div className="space-y-2 text-xxs text-slate-400">
              <p>Các thông tin cấu hình nhạy cảm được cô lập hoàn toàn tại file cục bộ <code className="text-brand-blue font-mono bg-slate-950 px-1 py-0.5 rounded">.env</code> và được cấu hình trong <code className="text-brand-purple font-mono bg-slate-950 px-1 py-0.5 rounded">.gitignore</code> nhằm tránh bị rò rỉ dữ liệu hoặc hack hệ thống.</p>
              
              <div className="border-t border-dark-border/40 pt-2.5 space-y-1">
                <div><strong>Mail Domain:</strong> <span className="text-slate-200">{serverStatus?.mailDomain || 'giaancompany.io.vn'}</span></div>
                <div><strong>SMTP Host:</strong> <span className="text-slate-200">{serverStatus?.mailSecurity?.smtpHost || 'smtp.gmail.com'}</span></div>
                <div><strong>SMTP Port:</strong> <span className="text-slate-200">{serverStatus?.mailSecurity?.smtpPort || '587'}</span></div>
                <div><strong>SMTP User:</strong> <span className="text-slate-200">{serverStatus?.mailSecurity?.smtpUser || 'no-reply@giaancompany.io.vn'}</span></div>
                <div>
                  <strong>Mật khẩu & JWT:</strong>{' '}
                  <span className={serverStatus?.mailSecurity?.isPasswordConfigured ? 'text-brand-emerald font-semibold' : 'text-brand-amber font-semibold'}>
                    {serverStatus?.mailSecurity?.isPasswordConfigured ? '✅ Đã bảo mật (Ẩn)' : '⚠️ Chưa cấu hình'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Save Button */}
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
            <button
              type="submit"
              className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl bg-gradient-to-r from-brand-blue to-brand-purple hover:from-brand-blue-hover hover:to-brand-purple-hover text-white text-sm font-semibold shadow-lg shadow-brand-blue/20 transition-all cursor-pointer"
            >
              <Save className="w-4 h-4" />
              <span>Lưu tất cả thay đổi</span>
            </button>

            {saveSuccess && (
              <div className="flex items-center gap-2 justify-center text-xs text-brand-emerald bg-brand-emerald/5 border border-brand-emerald/10 p-2.5 rounded-xl animate-fade-in">
                <CheckCircle2 className="w-4 h-4" />
                <span>Đã lưu thành công!</span>
              </div>
            )}
          </div>

        </div>

      </form>

    </div>
  );
};
