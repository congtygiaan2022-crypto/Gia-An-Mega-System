import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import {
  Cookie,
  Upload,
  Copy,
  CheckCircle,
  Database,
  History,
  AlertCircle
} from 'lucide-react';

export const Cookies: React.FC = () => {
  const { profiles, importCookies, addLog } = useStore();
  
  const [selectedProfileId, setSelectedProfileId] = useState(profiles[0]?.id || '');
  const [cookieInput, setCookieInput] = useState('');
  const [clearExisting, setClearExisting] = useState(false);
  const [importStatus, setImportStatus] = useState<{ success: boolean; msg: string } | null>(null);
  const [copied, setCopied] = useState(false);

  // Simulated backups
  const [backups, setBackups] = useState<Array<{ id: string; timestamp: string; count: number; name: string }>>([
    { id: 'b-1', timestamp: '2026-06-10 18:46', count: 142, name: 'Facebook Ad Account 01' },
    { id: 'b-2', timestamp: '2026-06-11 04:30', count: 89, name: 'Google Ads Agency Profile' }
  ]);

  const activeProfile = profiles.find(p => p.id === selectedProfileId);

  const handleImport = (e: React.FormEvent) => {
    e.preventDefault();
    setImportStatus(null);
    
    if (!selectedProfileId) {
      setImportStatus({ success: false, msg: 'Vui lòng chọn profile cần nhập cookie!' });
      return;
    }

    if (!cookieInput.trim()) {
      setImportStatus({ success: false, msg: 'Vui lòng dán dữ liệu cookie!' });
      return;
    }

    const res = importCookies(selectedProfileId, cookieInput);
    if (res.success) {
      setImportStatus({ success: true, msg: `Đã nhập thành công ${res.count} cookies vào profile "${activeProfile?.name}".` });
      setCookieInput('');
    } else {
      setImportStatus({ success: false, msg: res.error || 'Lỗi nhập cookie. Định dạng không hợp lệ.' });
    }
  };

  const handleExport = () => {
    if (!activeProfile) return;
    
    // Mock exporting cookies to clipboard
    const mockCookies = [
      { domain: ".facebook.com", expirationDate: 1781254300, name: "c_user", path: "/", value: "1000185963254" },
      { domain: ".facebook.com", expirationDate: 1781254300, name: "xs", path: "/", value: "48%3Aacb123%3A2%3A171802" }
    ];
    
    navigator.clipboard.writeText(JSON.stringify(mockCookies, null, 2));
    setCopied(true);
    addLog(`Đã xuất cookie của profile "${activeProfile.name}" ra Clipboard.`, 'success');
    
    setTimeout(() => {
      setCopied(false);
    }, 2000);
  };

  const handleCreateBackup = () => {
    if (!activeProfile) return;
    
    const now = new Date();
    const timeString = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    
    const newBackup = {
      id: `b-${Date.now()}`,
      timestamp: timeString,
      count: activeProfile.cookiesCount,
      name: activeProfile.name
    };

    setBackups([newBackup, ...backups]);
    addLog(`Đã tạo sao lưu cookie cho Profile "${activeProfile.name}" thành công.`, 'success');
  };

  const handleRestoreBackup = (backupName: string, count: number) => {
    if (!selectedProfileId) return;
    
    // Simulate restore
    addLog(`Khôi phục ${count} cookies từ bản sao lưu cho profile "${backupName}".`, 'success');
    alert(`Đã khôi phục thành công ${count} cookies từ bản sao lưu!`);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-200">Cookie Manager</h2>
        <p className="text-xs text-slate-500">Đồng bộ, sao lưu và quản lý cookies phiên duyệt của các tài khoản Chromium.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        
        {/* Left Column: Import / Export forms */}
        <div className="lg:col-span-2 space-y-5">
          
          {/* Main Card */}
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
            
            <div className="flex items-center gap-2">
              <Cookie className="w-5 h-5 text-brand-blue" />
              <h4 className="text-sm font-bold text-slate-300">Nhập & Xuất Cookies Trình Duyệt</h4>
            </div>

            <div className="space-y-3">
              <label className="text-xs font-semibold text-slate-400 block">Chọn Profile Thao Tác</label>
              <select
                value={selectedProfileId}
                onChange={(e) => setSelectedProfileId(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-dark-border bg-slate-950/40 text-sm text-slate-200 focus:bg-slate-900 cursor-pointer"
              >
                <option value="" disabled>-- Chọn một profile --</option>
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.cookiesCount} cookies)
                  </option>
                ))}
              </select>
            </div>

            {activeProfile && (
              <div className="flex items-center justify-between p-3 rounded-xl border border-dark-border bg-slate-900/10 text-xs">
                <div>
                  <span className="text-slate-400">Profile: </span>
                  <span className="font-semibold text-slate-200">{activeProfile.name}</span>
                </div>
                <button
                  onClick={handleExport}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-brand-blue/30 bg-brand-blue/5 text-brand-blue hover:bg-brand-blue/15 text-xxs font-semibold transition-all cursor-pointer"
                >
                  {copied ? (
                    <>
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>Đã sao chép JSON</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Xuất Cookies hoạt động</span>
                    </>
                  )}
                </button>
              </div>
            )}

            <form onSubmit={handleImport} className="space-y-4 pt-2">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 block">Nhập mới Cookie</label>
                <textarea
                  placeholder="Dán JSON Cookie hoặc định dạng dòng Netscape vào đây..."
                  value={cookieInput}
                  onChange={(e) => setCookieInput(e.target.value)}
                  rows={6}
                  className="w-full px-4 py-3 rounded-xl border border-dark-border bg-slate-950/40 text-xs text-slate-200 font-mono focus:bg-slate-900"
                ></textarea>
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={clearExisting}
                    onChange={(e) => setClearExisting(e.target.checked)}
                    className="rounded border-slate-700 text-brand-blue focus:ring-0 w-4 h-4 bg-slate-950/40"
                  />
                  <span>Xóa toàn bộ cookie cũ của profile trước khi nạp</span>
                </label>

                <button
                  type="submit"
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand-blue hover:bg-brand-blue-hover text-white text-xs font-semibold shadow-xs transition-all cursor-pointer"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>Nạp Cookies</span>
                </button>
              </div>

              {importStatus && (
                <div className={`p-3 rounded-xl border flex items-start gap-2 text-xs ${
                  importStatus.success
                    ? 'border-brand-emerald/20 bg-brand-emerald/5 text-brand-emerald'
                    : 'border-brand-rose/20 bg-brand-rose/5 text-brand-rose'
                } animate-fade-in`}>
                  {importStatus.success ? (
                    <CheckCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  )}
                  <p>{importStatus.msg}</p>
                </div>
              )}

            </form>

          </div>

        </div>

        {/* Right Column: Backup & Restore */}
        <div className="space-y-5">
          
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-brand-purple" />
                <h4 className="text-sm font-bold text-slate-300">Sao Lưu Vân Tay Cookie</h4>
              </div>
              {activeProfile && (
                <button
                  onClick={handleCreateBackup}
                  className="text-xxs font-bold text-brand-purple hover:underline cursor-pointer"
                >
                  Tạo bản sao lưu
                </button>
              )}
            </div>

            <p className="text-xxs text-slate-500 leading-relaxed">
              Dữ liệu Cookies được mã hóa đầu cuối và đồng bộ hóa tự động lên đám mây. Bạn có thể khôi phục các mốc lịch sử phiên duyệt dưới đây.
            </p>

            {/* Backups List */}
            <div className="space-y-3 pt-2">
              <span className="text-xxs font-bold tracking-widest text-slate-600 uppercase flex items-center gap-1">
                <History className="w-3.5 h-3.5" />
                <span>Bản sao lưu lưu trữ</span>
              </span>

              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {backups.map((bk) => (
                  <div
                    key={bk.id}
                    className="p-3 rounded-xl border border-dark-border bg-slate-950/40 hover:bg-slate-900/20 transition-all flex items-center justify-between text-xxs group"
                  >
                    <div>
                      <span className="font-semibold text-slate-300 block truncate max-w-[130px]">{bk.name}</span>
                      <span className="text-slate-500 font-mono mt-0.5 block">{bk.timestamp}</span>
                    </div>
                    <div className="text-right flex items-center gap-2">
                      <span className="font-semibold text-brand-purple font-mono block bg-brand-purple/5 border border-brand-purple/10 px-1.5 py-0.5 rounded-sm shrink-0">
                        {bk.count} cookies
                      </span>
                      <button
                        onClick={() => handleRestoreBackup(bk.name, bk.count)}
                        className="opacity-0 group-hover:opacity-100 px-2 py-1 bg-slate-900 border border-dark-border hover:border-slate-700 text-slate-300 rounded-lg font-bold transition-all shrink-0 cursor-pointer"
                      >
                        Khôi phục
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>

        </div>

      </div>

    </div>
  );
};
