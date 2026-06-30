import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import {
  Search,
  Plus,
  Bell,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  X
} from 'lucide-react';

export const Topbar: React.FC = () => {
  const {
    searchTerm,
    setSearchTerm,
    activeTab,
    setActiveTab,
    setIsCreateModalOpen,
    systemMetrics,
    logs,
    user,
    resetServer
  } = useStore();

  const [showNotifications, setShowNotifications] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  const handleResetServer = async () => {
    const confirmReset = window.confirm("Bạn có chắc chắn muốn đặt lại Máy chủ? Hành động này sẽ đóng lập tức tất cả các profile trình duyệt đang chạy để giải phóng bộ nhớ (tương tự stop.bat).");
    if (!confirmReset) return;

    setIsResetting(true);
    try {
      await resetServer();
    } catch (e) {
      console.error(e);
    } finally {
      setIsResetting(false);
    }
  };

  // Auto-switch to profiles tab if user starts typing a search query
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchTerm(value);
    if (value.trim() !== '' && activeTab !== 'profiles' && activeTab !== 'dashboard') {
      setActiveTab('profiles');
    }
  };

  // Filter logs to create notifications
  const recentAlerts = logs.slice(0, 5);
  const unreadCount = logs.filter(l => l.type === 'success' || l.type === 'error' || l.type === 'warning').length;

  // Determine resource status colors
  const getCpuColor = (val: number) => {
    if (val > 80) return 'text-brand-rose bg-brand-rose/10 border-brand-rose/20';
    if (val > 50) return 'text-brand-amber bg-brand-amber/10 border-brand-amber/20';
    return 'text-brand-emerald bg-brand-emerald/10 border-brand-emerald/20';
  };

  const getRamColor = (val: number) => {
    if (val > 85) return 'text-brand-rose bg-brand-rose/10 border-brand-rose/20';
    if (val > 60) return 'text-brand-amber bg-brand-amber/10 border-brand-amber/20';
    return 'text-brand-emerald bg-brand-emerald/10 border-brand-emerald/20';
  };

  return (
    <header className="h-20 border-b border-dark-border bg-dark-bg/60 backdrop-blur-md px-8 flex items-center justify-between z-5 select-none relative shrink-0">
      
      {/* Left Search Bar */}
      <div className="flex-1 max-w-md">
        <div className="relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-brand-blue transition-colors duration-300" />
          <input
            type="text"
            placeholder="Tìm kiếm profile theo tên, proxy, ghi chú..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="w-full pl-11 pr-4 py-2.5 rounded-xl border border-dark-border bg-slate-900/40 text-sm placeholder-slate-500 text-slate-200 transition-all duration-300 focus:bg-slate-900/80 focus:border-brand-blue/50 focus:ring-2 focus:ring-brand-blue/10"
          />
        </div>
      </div>

      {/* Right Dashboard Controls */}
      <div className="flex items-center gap-6">
        
        {/* System Resource Badges */}
        <div className="hidden lg:flex items-center gap-3 border-r border-dark-border pr-6 py-1 text-xs">
          {/* CPU Metric */}
          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border ${getCpuColor(systemMetrics.cpu)} transition-all duration-300`}>
            <Cpu className="w-3.5 h-3.5" />
            <span className="font-semibold">CPU:</span>
            <span>{systemMetrics.cpu}%</span>
          </div>
          {/* RAM Metric */}
          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border ${getRamColor(systemMetrics.ram)} transition-all duration-300`}>
            <Cpu className="w-3.5 h-3.5 rotate-90" />
            <span className="font-semibold">RAM:</span>
            <span>{systemMetrics.ram}%</span>
          </div>
        </div>

        {/* Reset Server Quick Action Button */}
        <button
          onClick={handleResetServer}
          disabled={isResetting}
          className={`flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-brand-rose/30 bg-brand-rose/5 text-brand-rose hover:bg-brand-rose/10 hover:border-brand-rose text-xs font-semibold active:scale-98 transition-all duration-300 cursor-pointer ${isResetting ? 'opacity-50 cursor-not-allowed' : ''}`}
          title="Đặt lại Máy chủ - Đóng toàn bộ các trình duyệt đang chạy"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin' : ''}`} />
          <span>Reset Server</span>
        </button>

        {/* Create Profile Button */}
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-blue to-brand-purple hover:from-brand-blue-hover hover:to-brand-purple-hover text-white text-sm font-semibold shadow-lg shadow-brand-blue/20 hover:shadow-brand-blue/30 active:scale-98 transition-all duration-300 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Tạo Profile</span>
        </button>

        {/* Notifications Panel */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className={`p-2.5 rounded-xl border border-dark-border bg-slate-900/30 text-slate-400 hover:text-white hover:border-slate-700/60 transition-all duration-300 cursor-pointer relative ${showNotifications ? 'border-brand-blue text-white' : ''}`}
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-brand-rose border-2 border-dark-bg rounded-full animate-pulse-slow"></span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-3 w-80 rounded-2xl glass-panel border border-dark-border-hover shadow-2xl p-4 animate-fade-in z-50">
              <div className="flex items-center justify-between pb-3 border-b border-dark-border mb-3">
                <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <span>Thông báo gần đây</span>
                  {unreadCount > 0 && (
                    <span className="px-1.5 py-0.5 text-xxs font-bold bg-brand-blue/20 text-brand-blue rounded-md">{unreadCount}</span>
                  )}
                </span>
                <button
                  onClick={() => setShowNotifications(false)}
                  className="p-1 rounded-lg text-slate-500 hover:text-white transition-colors duration-200"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {recentAlerts.length === 0 ? (
                  <p className="text-center text-xs text-slate-500 py-6">Không có thông báo mới</p>
                ) : (
                  recentAlerts.map((log) => (
                    <div
                      key={log.id}
                      className="flex items-start gap-2.5 p-2 rounded-lg bg-slate-950/40 border border-slate-900/80 hover:bg-slate-900/50 hover:border-slate-800 transition-colors"
                    >
                      {log.type === 'success' && <CheckCircle2 className="w-4 h-4 text-brand-emerald shrink-0 mt-0.5" />}
                      {log.type === 'error' && <AlertTriangle className="w-4 h-4 text-brand-rose shrink-0 mt-0.5" />}
                      {log.type === 'warning' && <AlertTriangle className="w-4 h-4 text-brand-amber shrink-0 mt-0.5" />}
                      {log.type === 'info' && <CheckCircle2 className="w-4 h-4 text-brand-blue shrink-0 mt-0.5" />}
                      
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-slate-300 break-words leading-relaxed">{log.message}</p>
                        <span className="text-xxs text-slate-600 mt-1 block">{log.timestamp}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Card */}
        {user && (
          <div className="flex items-center gap-3 pl-4 border-l border-dark-border">
            <div className="text-right hidden sm:block">
              <h5 className="text-xs font-semibold text-slate-300">{user.name}</h5>
              <span className="text-xxs text-dark-muted font-medium block truncate max-w-[120px]">{user.email}</span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-blue/30 to-brand-purple/30 border border-brand-purple/20 overflow-hidden flex items-center justify-center">
              <img
                src={user.avatar}
                alt={user.name}
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        )}

      </div>
    </header>
  );
};
