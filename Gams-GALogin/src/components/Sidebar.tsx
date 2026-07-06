import React from 'react';
import { useStore } from '../store/useStore';
import {
  LayoutDashboard,
  AppWindow,
  Network,
  Cookie,
  Zap,
  Settings,
  User,
  LogOut,
  Code2,
  UserCheck,
  FileCode
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { activeTab, setActiveTab, user, logout } = useStore();

  const menuItems = [
    { id: 'dashboard', name: 'Bảng điều khiển', icon: LayoutDashboard },
    { id: 'profiles', name: 'Danh sách Profile', icon: AppWindow },
    { id: 'proxies', name: 'Quản lý Proxy', icon: Network },
    { id: 'cookies', name: 'Quản lý Cookie', icon: Cookie },
    { id: 'user-agents', name: 'Quản lý User Agent', icon: UserCheck },
    { id: 'templates', name: 'Template Profile', icon: FileCode },
    { id: 'automation', name: 'Tự động hóa', icon: Zap },
    { id: 'api-guide', name: 'Kết nối API', icon: Code2 },
    { id: 'settings', name: 'Cài đặt hệ thống', icon: Settings },
    { id: 'account', name: 'Tài khoản', icon: User },
  ] as const;

  return (
    <aside className="w-64 h-screen glass-panel flex flex-col justify-between border-r border-dark-border select-none z-10 shrink-0">
      {/* Top Brand Logo Section */}
      <div className="p-6">
        <div className="flex items-center gap-3">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-blue to-brand-purple flex items-center justify-center shadow-lg shadow-brand-blue/20">
            {/* Custom Modern Logo combining G + Browser Window + User Profile */}
            <svg
              className="w-6 h-6 text-white"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 2a10 10 0 0 1 8 4M12 2v10l6.5 6.5M12 12H2a10 10 0 0 1 10-10z" />
              <circle cx="12" cy="12" r="4" fill="currentColor" fillOpacity="0.2" />
            </svg>
            <div className="absolute -inset-0.5 bg-gradient-to-tr from-brand-blue to-brand-purple rounded-xl blur-xs opacity-50 -z-10 animate-pulse-slow"></div>
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-wider bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
              Gams-GA
            </h1>
            <span className="text-xxs font-semibold tracking-widest text-brand-blue uppercase">
              Trình Quản Lý
            </span>
          </div>
        </div>
      </div>

      {/* Menu Links */}
      <nav className="flex-1 px-4 py-2 space-y-1.5 overflow-y-auto">
        <span className="px-3 text-xxs font-semibold text-dark-muted tracking-widest uppercase block mb-3">
          Danh Mục
        </span>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 relative group cursor-pointer ${
                isActive
                  ? 'text-white bg-gradient-to-r from-brand-blue/15 to-brand-purple/5 border border-brand-blue/20 shadow-xs'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/40 border border-transparent'
              }`}
            >
              <Icon
                className={`w-5 h-5 transition-transform duration-300 group-hover:scale-105 ${
                  isActive ? 'text-brand-blue' : 'text-slate-400 group-hover:text-slate-200'
                }`}
              />
              <span className="relative z-10">{item.name}</span>
              
              {isActive && (
                <div className="absolute left-0 w-1 h-5 rounded-r-md bg-gradient-to-b from-brand-blue to-brand-purple"></div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Profile Info & Logout */}
      <div className="p-4 border-t border-dark-border">
        {user ? (
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-2 rounded-xl bg-slate-900/30 border border-dark-border">
              <div className="relative">
                <img
                  src={user.avatar}
                  alt={user.name}
                  className="w-10 h-10 rounded-lg object-cover ring-2 ring-brand-purple/20"
                />
                <div className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-brand-emerald border-2 border-dark-bg rounded-full animate-pulse-slow"></div>
              </div>
              <div className="overflow-hidden">
                <h4 className="text-sm font-semibold text-slate-200 truncate">{user.name}</h4>
                <p className="text-xs text-slate-500 truncate">{user.role}</p>
              </div>
            </div>
            
            <button
              onClick={logout}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-brand-rose/20 text-brand-rose bg-brand-rose/5 hover:bg-brand-rose/10 hover:border-brand-rose/30 text-sm font-medium transition-all duration-300 cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
              <span>Đăng xuất</span>
            </button>
          </div>
        ) : (
          <div className="p-3 text-center text-xs text-slate-500">
            Hệ thống an toàn
          </div>
        )}
      </div>
    </aside>
  );
};
