import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import {
  Plus,
  RefreshCw,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Play,
  HelpCircle,
  FileText
} from 'lucide-react';

export const Proxies: React.FC = () => {
  const { proxies, addProxy, deleteProxy, testProxy, testAllProxies } = useStore();

  const [showImport, setShowImport] = useState(false);
  const [importText, setImportText] = useState('');
  const [proxyType, setProxyType] = useState<'HTTP' | 'SOCKS5'>('HTTP');
  const [proxyGroup, setProxyGroup] = useState('Imported Group');

  const [isTestingAll, setIsTestingAll] = useState(false);

  const handleBatchImport = (e: React.FormEvent) => {
    e.preventDefault();
    if (!importText.trim()) return;

    const lines = importText.split('\n').filter((l) => l.trim() !== '');
    let successCount = 0;

    lines.forEach((line) => {
      try {
        let host = '';
        let port = 80;
        let username = '';
        let password = '';

        // Match format: host:port:user:pass or user:pass@host:port or host:port
        if (line.includes('@')) {
          const parts = line.split('@');
          const auth = parts[0].split(':');
          const network = parts[1].split(':');
          
          username = auth[0];
          password = auth[1];
          host = network[0];
          port = parseInt(network[1]);
        } else {
          const parts = line.split(':');
          host = parts[0];
          port = parseInt(parts[1]);
          if (parts[2]) username = parts[2];
          if (parts[3]) password = parts[3];
        }

        if (host && port) {
          addProxy({
            host,
            port,
            type: proxyType,
            group: proxyGroup,
            username: username || undefined,
            password: password || undefined
          });
          successCount++;
        }
      } catch (err) {
        console.error('Failed to parse proxy line: ', line);
      }
    });

    setImportText('');
    setShowImport(false);
  };

  const handleTestAll = async () => {
    setIsTestingAll(true);
    await testAllProxies();
    setIsTestingAll(false);
  };

  const getLatencyColor = (speed?: number) => {
    if (!speed || speed === 0) return 'text-slate-500';
    if (speed < 100) return 'text-brand-emerald bg-brand-emerald/10 border-brand-emerald/20';
    if (speed < 200) return 'text-brand-amber bg-brand-amber/10 border-brand-amber/20';
    return 'text-brand-rose bg-brand-rose/10 border-brand-rose/20';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-slate-200">Quản lý Proxy</h2>
          <p className="text-xs text-slate-500">
            Tổng số proxy: <span className="font-semibold text-slate-400">{proxies.length}</span> | Hoạt động:{' '}
            <span className="font-semibold text-brand-emerald">{proxies.filter((p) => p.status === 'active').length}</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleTestAll}
            disabled={isTestingAll || proxies.length === 0}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/40 text-slate-300 hover:text-white hover:border-slate-700 font-semibold text-xs transition-all disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isTestingAll ? 'animate-spin' : ''}`} />
            <span>Kiểm tra độ trễ</span>
          </button>
          <button
            onClick={() => setShowImport(!showImport)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-blue to-brand-purple hover:from-brand-blue-hover hover:to-brand-purple-hover text-white text-xs font-semibold shadow-lg shadow-brand-blue/20 hover:shadow-brand-blue/30 transition-all cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Nhập Proxy</span>
          </button>
        </div>
      </div>

      {/* Batch Import Panel */}
      {showImport && (
        <form onSubmit={handleBatchImport} className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4 animate-fade-in">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-brand-blue" />
              <h4 className="text-sm font-bold text-slate-300">Nhập danh sách Proxy (Batch Import)</h4>
            </div>
            <button
              type="button"
              onClick={() => setShowImport(false)}
              className="text-xs text-slate-500 hover:text-slate-300 cursor-pointer"
            >
              Đóng
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 block">Loại Proxy mặc định</label>
              <select
                value={proxyType}
                onChange={(e) => setProxyType(e.target.value as any)}
                className="w-full px-4 py-2 rounded-xl border border-dark-border bg-slate-950/40 text-xs text-slate-300 focus:bg-slate-900 cursor-pointer"
              >
                <option value="HTTP">HTTP / HTTPS</option>
                <option value="SOCKS5">SOCKS5</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 block">Nhóm Proxy gắn thẻ</label>
              <input
                type="text"
                value={proxyGroup}
                onChange={(e) => setProxyGroup(e.target.value)}
                placeholder="Ví dụ: US Mobile Group"
                className="w-full px-4 py-2 rounded-xl border border-dark-border bg-slate-950/40 text-xs text-slate-300 focus:bg-slate-900"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-400 block">Dữ liệu Proxy (Mỗi dòng một proxy)</label>
            <textarea
              placeholder={`Định dạng hỗ trợ:
IP:Port
IP:Port:Username:Password
Username:Password@IP:Port`}
              value={importText}
              onChange={(e) => setImportText(e.target.value)}
              rows={5}
              required
              className="w-full px-4 py-3 rounded-xl border border-dark-border bg-slate-950/40 text-xs text-slate-200 font-mono focus:bg-slate-900"
            ></textarea>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => setShowImport(false)}
              className="px-4 py-2 rounded-xl border border-dark-border text-slate-400 hover:text-white text-xs font-semibold transition-all cursor-pointer"
            >
              Hủy
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-brand-blue hover:bg-brand-blue-hover text-white text-xs font-semibold shadow-xs transition-all cursor-pointer"
            >
              Xác nhận Import
            </button>
          </div>
        </form>
      )}

      {/* Proxies Data Grid */}
      <div className="border border-dark-border rounded-2xl bg-slate-950/30 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-dark-border bg-slate-900/20 text-xxs font-bold uppercase tracking-wider text-slate-500">
                <th className="p-4 pl-6">Địa chỉ Host</th>
                <th className="p-4 text-center">Port</th>
                <th className="p-4">Giao Thức</th>
                <th className="p-4">Thông tin Auth (User)</th>
                <th className="p-4 text-center">Trạng Thái</th>
                <th className="p-4">Độ Trễ Latency</th>
                <th className="p-4">Nhóm Proxy</th>
                <th className="p-4 text-right pr-6 w-36">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-border text-xs">
              {proxies.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-16 text-center text-slate-600 text-sm font-medium">
                    Chưa có proxy nào được thêm vào. Bấm "Import Proxy" để bắt đầu.
                  </td>
                </tr>
              ) : (
                proxies.map((p) => {
                  const isTesting = p.status === 'testing';
                  return (
                    <tr key={p.id} className="hover:bg-slate-900/20 transition-all">
                      {/* Host */}
                      <td className="p-4 pl-6 font-semibold text-slate-200 font-mono">
                        {p.host}
                      </td>

                      {/* Port */}
                      <td className="p-4 text-center font-mono text-slate-400">
                        {p.port}
                      </td>

                      {/* Protocol */}
                      <td className="p-4">
                        <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold border border-dark-border bg-slate-900 text-slate-400 font-mono">
                          {p.type}
                        </span>
                      </td>

                      {/* Auth credentials info */}
                      <td className="p-4 font-mono text-slate-500">
                        {p.username ? (
                          <span>{p.username}</span>
                        ) : (
                          <span className="text-slate-700 italic">None</span>
                        )}
                      </td>

                      {/* Connection status */}
                      <td className="p-4 text-center">
                        {p.status === 'active' && (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xxs font-semibold bg-brand-emerald/10 text-brand-emerald border border-brand-emerald/20">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Hoạt động</span>
                          </span>
                        )}
                        {p.status === 'failed' && (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xxs font-semibold bg-brand-rose/10 text-brand-rose border border-brand-rose/20">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            <span>Mất kết nối</span>
                          </span>
                        )}
                        {p.status === 'inactive' && (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xxs font-semibold bg-slate-900 text-slate-500 border border-dark-border">
                            <span>Chưa kiểm tra</span>
                          </span>
                        )}
                        {isTesting && (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xxs font-semibold bg-brand-blue/10 text-brand-blue border border-brand-blue/20">
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                            <span>Đang kiểm tra...</span>
                          </span>
                        )}
                      </td>

                      {/* Speed Latency */}
                      <td className="p-4 font-mono">
                        {p.status === 'active' && p.speed ? (
                          <span className={`px-2 py-0.5 rounded-lg border text-[10px] font-bold ${getLatencyColor(p.speed)}`}>
                            {p.speed} ms
                          </span>
                        ) : (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>

                      {/* Proxy Group */}
                      <td className="p-4 text-slate-400 font-semibold">
                        {p.group}
                      </td>

                      {/* Action buttons */}
                      <td className="p-4 text-right pr-6">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => testProxy(p.id)}
                            disabled={isTesting}
                            title="Kiểm tra kết nối"
                            className="p-2 rounded-lg border border-dark-border bg-slate-900/30 text-slate-400 hover:text-brand-blue hover:border-brand-blue/20 transition-all cursor-pointer disabled:opacity-50"
                          >
                            <Play className="w-3.5 h-3.5 fill-slate-400/5 hover:fill-brand-blue/10" />
                          </button>
                          <button
                            onClick={() => deleteProxy(p.id)}
                            title="Xóa Proxy"
                            className="p-2 rounded-lg border border-dark-border bg-slate-900/30 text-slate-400 hover:text-brand-rose hover:border-brand-rose/20 transition-all cursor-pointer"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-dark-border bg-slate-900/10 flex items-center justify-between text-xxs text-slate-500">
          <span>Hỗ trợ các định dạng Proxy tĩnh, Proxy xoay, Mobile Proxy (Socks5/Http)</span>
          <span className="flex items-center gap-1">
            <HelpCircle className="w-3.5 h-3.5 text-slate-600" />
            <span>Xem tài liệu API Proxy</span>
          </span>
        </div>

      </div>

    </div>
  );
};
