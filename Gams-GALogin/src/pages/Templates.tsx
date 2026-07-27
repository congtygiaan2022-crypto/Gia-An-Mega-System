import React, { useState, useEffect } from 'react';
import { useStore } from '../store/useStore';
import { 
  Plus, 
  Trash2, 
  Edit2, 
  FileCode,
  Layout,
  Globe,
  Clock,
  Shuffle,
  Network
} from 'lucide-react';

export const Templates: React.FC = () => {
  const { 
    templates, 
    fetchTemplates, 
    createTemplate, 
    updateTemplate, 
    deleteTemplate 
  } = useStore();

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  // Form State
  const [name, setName] = useState('');
  const [browserType, setBrowserType] = useState<'chromium' | 'chrome' | 'edge' | 'custom'>('chromium');
  const [width, setWidth] = useState('1280');
  const [height, setHeight] = useState('720');
  const [language, setLanguage] = useState('vi-VN');
  const [timezone, setTimezone] = useState('Asia/Ho_Chi_Minh');
  const [userAgentPolicy, setUserAgentPolicy] = useState<'Fixed' | 'Random' | 'Sequential'>('Random');
  const [startupMode, setStartupMode] = useState<'blank' | 'last_session' | 'urls'>('blank');
  const [startupUrls, setStartupUrls] = useState('');
  const [customArgs, setCustomArgs] = useState('--no-first-run\n--no-default-browser-check');

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const payload = {
      name,
      browserType,
      windowSize: {
        width: parseInt(width) || 1280,
        height: parseInt(height) || 720,
        x: 50,
        y: 50
      },
      language,
      timezone,
      userAgentPolicy,
      startupConfig: {
        mode: startupMode,
        urls: startupUrls.split('\n').map(u => u.trim()).filter(Boolean)
      },
      browserArguments: customArgs.split('\n').map(a => a.trim()).filter(Boolean),
      proxyConfig: { type: 'Direct' as const, host: '', port: '', username: '', password: '', pacUrl: '' },
      extensions: []
    };

    if (editingId) {
      await updateTemplate(editingId, payload);
      setEditingId(null);
    } else {
      await createTemplate(payload);
    }

    // Reset Form
    setName('');
    setIsFormOpen(false);
  };

  const startEdit = (tpl: any) => {
    setEditingId(tpl.id);
    setName(tpl.name);
    setBrowserType(tpl.browserType);
    setWidth(tpl.windowSize?.width?.toString() || '1280');
    setHeight(tpl.windowSize?.height?.toString() || '720');
    setLanguage(tpl.language || 'vi-VN');
    setTimezone(tpl.timezone || 'Asia/Ho_Chi_Minh');
    setUserAgentPolicy(tpl.userAgentPolicy || 'Random');
    setStartupMode(tpl.startupConfig?.mode || 'blank');
    setStartupUrls(tpl.startupConfig?.urls?.join('\n') || '');
    setCustomArgs(tpl.browserArguments?.join('\n') || '');
    setIsFormOpen(true);
  };

  return (
    <div className="space-y-6 animate-fade-in relative">
      
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-slate-200">Quản Lý Template Profile</h2>
          <p className="text-xs text-slate-500 font-medium">
            Tạo cấu hình mẫu để khởi tạo hàng loạt profile nhanh chóng.
          </p>
        </div>
        <button
          onClick={() => {
            setEditingId(null);
            setIsFormOpen(true);
          }}
          className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-blue to-brand-purple text-white text-xs font-semibold shadow-lg shadow-brand-blue/20 hover:shadow-brand-blue/30 transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Thêm Template Mới</span>
        </button>
      </div>

      {/* Grid List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map(tpl => (
          <div key={tpl.id} className="glass-panel border border-dark-border bg-dark-card/30 rounded-2xl p-5 hover:border-slate-800 transition-all relative overflow-hidden group">
            
            {/* Template Header */}
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-slate-900 border border-dark-border text-brand-purple">
                  <FileCode className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-slate-200 text-sm">{tpl.name}</h4>
                  <span className="text-[10px] text-slate-500 uppercase font-semibold">
                    Browser: {tpl.browserType}
                  </span>
                </div>
              </div>
              
              <div className="flex gap-1.5">
                <button
                  onClick={() => startEdit(tpl)}
                  className="p-1.5 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-white transition-all cursor-pointer"
                  title="Sửa"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => {
                    if (confirm('Xóa template này?')) deleteTemplate(tpl.id);
                  }}
                  className="p-1.5 rounded-lg border border-brand-rose/20 bg-brand-rose/5 text-brand-rose hover:bg-brand-rose/10 transition-all cursor-pointer"
                  title="Xóa"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Template Details */}
            <div className="space-y-3.5 text-xs text-slate-400 border-t border-dark-border pt-4">
              <div className="flex items-center gap-2">
                <Layout className="w-3.5 h-3.5 text-slate-500" />
                <span>Kích thước cửa sổ: </span>
                <span className="font-semibold text-slate-300 font-mono ml-auto">
                  {tpl.windowSize?.width}x{tpl.windowSize?.height}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Globe className="w-3.5 h-3.5 text-slate-500" />
                <span>Ngôn ngữ: </span>
                <span className="font-semibold text-slate-300 ml-auto">{tpl.language}</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-3.5 h-3.5 text-slate-500" />
                <span>Múi giờ: </span>
                <span className="font-semibold text-slate-300 ml-auto truncate max-w-[150px] text-right">
                  {tpl.timezone}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Shuffle className="w-3.5 h-3.5 text-slate-500" />
                <span>Chính sách User Agent: </span>
                <span className="font-semibold text-slate-300 ml-auto">{tpl.userAgentPolicy}</span>
              </div>
              <div className="flex items-center gap-2">
                <Network className="w-3.5 h-3.5 text-slate-500" />
                <span>Mạng Proxy mặc định: </span>
                <span className="font-semibold text-slate-300 ml-auto">Direct (Direct)</span>
              </div>
            </div>

          </div>
        ))}
      </div>

      {/* Create / Edit Form Modal Dialog */}
      {isFormOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
          <div className="w-full max-w-2xl rounded-2xl border border-dark-border bg-dark-card p-6 shadow-2xl space-y-4 my-8 animate-fade-in">
            
            <div className="flex justify-between items-center border-b border-dark-border pb-3">
              <h3 className="text-md font-bold text-slate-200">
                {editingId ? 'Cập Nhật Template' : 'Tạo Template Mới'}
              </h3>
              <button 
                onClick={() => setIsFormOpen(false)}
                className="text-slate-500 hover:text-white text-xs cursor-pointer"
              >
                Đóng
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Tên Template</label>
                  <input
                    type="text"
                    required
                    placeholder="Ví dụ: Template Checkout US"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-200"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Browser Type</label>
                  <select
                    value={browserType}
                    onChange={(e) => setBrowserType(e.target.value as any)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-200 focus:bg-slate-900"
                  >
                    <option value="chromium">Chromium (Built-in)</option>
                    <option value="chrome">Google Chrome (System)</option>
                    <option value="edge">Microsoft Edge (System)</option>
                    <option value="custom">Custom Application Path</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Chiều rộng cửa sổ</label>
                  <input
                    type="number"
                    value={width}
                    onChange={(e) => setWidth(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-200"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Chiều cao cửa sổ</label>
                  <input
                    type="number"
                    value={height}
                    onChange={(e) => setHeight(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-200"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Chính sách User Agent</label>
                  <select
                    value={userAgentPolicy}
                    onChange={(e) => setUserAgentPolicy(e.target.value as any)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-200 focus:bg-slate-900"
                  >
                    <option value="Random">Random (Lấy ngẫu nhiên theo OS)</option>
                    <option value="Sequential">Sequential (Lần lượt xoay vòng)</option>
                    <option value="Fixed">Fixed (Mặc định cố định)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Ngôn ngữ mặc định</label>
                  <input
                    type="text"
                    placeholder="vi-VN"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-200"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Múi giờ mặc định</label>
                  <input
                    type="text"
                    placeholder="Asia/Ho_Chi_Minh"
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-200"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Chế độ trang khởi động</label>
                  <select
                    value={startupMode}
                    onChange={(e) => setStartupMode(e.target.value as any)}
                    className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-200 focus:bg-slate-900"
                  >
                    <option value="blank">Mở trang trống (about:blank)</option>
                    <option value="last_session">Khôi phục phiên làm việc trước</option>
                    <option value="urls">Mở các URL chỉ định</option>
                  </select>
                </div>
                {startupMode === 'urls' && (
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-slate-400 block">Danh sách URLs (Mỗi dòng một trang)</label>
                    <textarea
                      rows={2}
                      placeholder="https://google.com&#10;https://whoer.net"
                      value={startupUrls}
                      onChange={(e) => setStartupUrls(e.target.value)}
                      className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-200"
                    ></textarea>
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 block">Command Line Arguments mặc định (Mỗi dòng một tham số)</label>
                <textarea
                  rows={3}
                  value={customArgs}
                  onChange={(e) => setCustomArgs(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-200 font-mono"
                ></textarea>
              </div>

              <div className="flex justify-end gap-3 pt-3 border-t border-dark-border">
                <button
                  type="button"
                  onClick={() => setIsFormOpen(false)}
                  className="px-4 py-2.5 rounded-xl border border-dark-border text-slate-400 hover:text-white text-xs font-semibold transition-all cursor-pointer"
                >
                  Hủy bỏ
                </button>
                <button
                  type="submit"
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-blue to-brand-purple hover:from-brand-blue-hover hover:to-brand-purple-hover text-white text-xs font-semibold transition-all cursor-pointer"
                >
                  Lưu Template
                </button>
              </div>

            </form>
          </div>
        </div>
      )}

    </div>
  );
};
