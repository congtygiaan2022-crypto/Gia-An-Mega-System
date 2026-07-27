import React, { useState, useEffect } from 'react';
import { useStore } from '../store/useStore';
import { 
  Trash2, 
  Edit2, 
  Download, 
  Upload, 
  Search, 
  Laptop, 
  Check, 
  Copy,
  AlertCircle
} from 'lucide-react';

export const UserAgents: React.FC = () => {
  const { 
    userAgents, 
    fetchUserAgents, 
    addUserAgent, 
    updateUserAgent, 
    deleteUserAgent, 
    importUserAgents
  } = useStore();

  const [search, setSearch] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [uaString, setUaString] = useState('');
  const [platform, setPlatform] = useState<'Windows' | 'macOS' | 'Linux'>('Windows');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  
  // Importer states
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [importType, setImportType] = useState<'text' | 'json'>('text');
  const [importText, setImportText] = useState('');
  const [importPlatform, setImportPlatform] = useState<'Windows' | 'macOS' | 'Linux'>('Windows');
  const [importResult, setImportResult] = useState<string | null>(null);

  useEffect(() => {
    fetchUserAgents();
  }, [fetchUserAgents]);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uaString.trim()) return;

    if (editingId) {
      await updateUserAgent(editingId, uaString, platform);
      setEditingId(null);
    } else {
      await addUserAgent(uaString, platform);
    }

    setUaString('');
  };

  const startEdit = (item: any) => {
    setEditingId(item.id);
    setUaString(item.ua);
    setPlatform(item.platform);
  };

  const handleImportSubmit = async () => {
    if (!importText.trim()) return;
    const count = await importUserAgents(importType, importText, importPlatform);
    if (count > 0) {
      setImportResult(`Nạp thành công ${count} User Agents mới!`);
      setImportText('');
      setTimeout(() => {
        setImportResult(null);
        setIsImportOpen(false);
      }, 2500);
    } else {
      setImportResult('Nhập thất bại. Vui lòng kiểm tra lại định dạng dữ liệu.');
    }
  };

  const filteredUas = userAgents.filter(u => 
    u.ua.toLowerCase().includes(search.toLowerCase()) ||
    u.platform.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in relative">
      
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-slate-200">Quản Lý User Agent</h2>
          <p className="text-xs text-slate-500">
            Tổng số User Agent khả dụng: <span className="font-semibold text-slate-400">{userAgents.length}</span>
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setIsImportOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-xl border border-dark-border bg-slate-900/60 text-slate-300 hover:text-white transition-all cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Batch Import</span>
          </button>
          <a
            href="http://localhost:1020/api/user-agents/export"
            download
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-xl border border-dark-border bg-slate-900/60 text-slate-300 hover:text-white transition-all cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export JSON</span>
          </a>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Form Add / Edit */}
        <div className="glass-panel p-5 border border-dark-border rounded-2xl bg-dark-card/30 h-fit space-y-4">
          <h3 className="text-sm font-bold text-slate-200">
            {editingId ? 'Cập Nhật User Agent' : 'Thêm User Agent Mới'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 block">Chuỗi User Agent</label>
              <textarea
                required
                rows={4}
                placeholder="Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
                value={uaString}
                onChange={(e) => setUaString(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-200 font-mono"
              ></textarea>
            </div>
            
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

            <div className="flex gap-2 pt-2">
              {editingId && (
                <button
                  type="button"
                  onClick={() => {
                    setEditingId(null);
                    setUaString('');
                  }}
                  className="w-1/3 py-2.5 rounded-xl border border-dark-border text-slate-400 hover:text-white text-xs font-semibold transition-all cursor-pointer"
                >
                  Hủy
                </button>
              )}
              <button
                type="submit"
                className={`flex-1 py-2.5 rounded-xl text-xs font-semibold text-white transition-all cursor-pointer bg-gradient-to-r from-brand-blue to-brand-purple hover:from-brand-blue-hover hover:to-brand-purple-hover`}
              >
                {editingId ? 'Cập Nhật' : 'Lưu Lại'}
              </button>
            </div>
          </form>
        </div>

        {/* List View */}
        <div className="lg:col-span-2 space-y-4">
          
          {/* Search Bar */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-4 top-3.5" />
            <input
              type="text"
              placeholder="Tìm kiếm User Agent..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-11 pr-4 py-3 rounded-2xl border border-dark-border bg-slate-950/20 text-sm text-slate-200 placeholder-slate-500 focus:border-slate-800 transition-all outline-none"
            />
          </div>

          {/* List Table */}
          <div className="border border-dark-border rounded-2xl bg-slate-950/30 overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-dark-border bg-slate-900/20 text-xxs font-bold uppercase tracking-wider text-slate-500">
                    <th className="p-4 w-24">OS</th>
                    <th className="p-4">User Agent String</th>
                    <th className="p-4 text-right pr-6 w-32">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-border text-xs">
                  {filteredUas.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="p-12 text-center text-slate-600 font-medium">
                        Không có User Agent nào được ghi nhận.
                      </td>
                    </tr>
                  ) : (
                    filteredUas.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-900/10 transition-all group">
                        <td className="p-4">
                          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[10px] font-bold border ${
                            item.platform === 'Windows' 
                              ? 'bg-blue-500/10 border-blue-500/20 text-blue-400' 
                              : item.platform === 'macOS' 
                              ? 'bg-purple-500/10 border-purple-500/20 text-purple-400' 
                              : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                          }`}>
                            <Laptop className="w-3 h-3" />
                            {item.platform}
                          </span>
                        </td>
                        <td className="p-4 font-mono text-slate-400 max-w-md truncate relative pr-8">
                          <span className="block truncate">{item.ua}</span>
                        </td>
                        <td className="p-4 text-right pr-6">
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => handleCopy(item.id, item.ua)}
                              className="p-1.5 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-white transition-all cursor-pointer"
                              title="Copy User Agent"
                            >
                              {copiedId === item.id ? (
                                <Check className="w-3.5 h-3.5 text-brand-emerald" />
                              ) : (
                                <Copy className="w-3.5 h-3.5" />
                              )}
                            </button>
                            <button
                              onClick={() => startEdit(item)}
                              className="p-1.5 rounded-lg border border-dark-border bg-slate-900/30 text-slate-500 hover:text-white transition-all cursor-pointer"
                              title="Sửa"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => {
                                if (confirm('Xóa User Agent này?')) deleteUserAgent(item.id);
                              }}
                              className="p-1.5 rounded-lg border border-brand-rose/20 bg-brand-rose/5 text-brand-rose hover:bg-brand-rose/10 transition-all cursor-pointer"
                              title="Xóa"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

        </div>

      </div>

      {/* Batch Import Dialog */}
      {isImportOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-xl rounded-2xl border border-dark-border bg-dark-card p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-dark-border pb-3">
              <h3 className="text-sm font-bold text-slate-200">Batch Import User Agents</h3>
              <button 
                onClick={() => setIsImportOpen(false)}
                className="text-slate-500 hover:text-white text-xs cursor-pointer"
              >
                Đóng
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex gap-4 border-b border-dark-border pb-3">
                <button
                  type="button"
                  onClick={() => setImportType('text')}
                  className={`text-xs font-semibold pb-1 border-b-2 cursor-pointer ${
                    importType === 'text' ? 'border-brand-blue text-brand-blue' : 'border-transparent text-slate-400'
                  }`}
                >
                  Import TXT (Mỗi dòng một UA)
                </button>
                <button
                  type="button"
                  onClick={() => setImportType('json')}
                  className={`text-xs font-semibold pb-1 border-b-2 cursor-pointer ${
                    importType === 'json' ? 'border-brand-blue text-brand-blue' : 'border-transparent text-slate-400'
                  }`}
                >
                  Import JSON Array
                </button>
              </div>

              {importType === 'text' && (
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 block">Chọn OS áp dụng</label>
                  <div className="grid grid-cols-3 gap-2">
                    {(['Windows', 'macOS', 'Linux'] as const).map((os) => (
                      <button
                        key={os}
                        type="button"
                        onClick={() => setImportPlatform(os)}
                        className={`py-1.5 rounded-lg text-xxs font-semibold border transition-all cursor-pointer ${
                          importPlatform === os
                            ? 'border-brand-blue bg-brand-blue/10 text-brand-blue'
                            : 'border-dark-border bg-slate-900/20 text-slate-400 hover:text-white'
                        }`}
                      >
                        {os}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-400 block">Dữ liệu nạp</label>
                <textarea
                  rows={8}
                  placeholder={importType === 'text' 
                    ? "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...\nMozilla/5.0 (Macintosh; Intel Mac)..."
                    : '[\n  {"ua": "Mozilla/5.0...", "platform": "Windows"},\n  {"ua": "Mozilla/5.0...", "platform": "macOS"}\n]'
                  }
                  value={importText}
                  onChange={(e) => setImportText(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-xs text-slate-200 font-mono"
                ></textarea>
              </div>
            </div>

            {importResult && (
              <div className="p-3 rounded-xl border border-brand-blue/20 bg-brand-blue/5 text-brand-blue text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                <span>{importResult}</span>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setIsImportOpen(false)}
                className="px-4 py-2 rounded-xl border border-dark-border text-slate-400 hover:text-white text-xs font-semibold transition-all cursor-pointer"
              >
                Hủy
              </button>
              <button
                type="button"
                onClick={handleImportSubmit}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-blue to-brand-purple hover:from-brand-blue-hover hover:to-brand-purple-hover text-white text-xs font-semibold transition-all cursor-pointer"
              >
                Import ngay
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
