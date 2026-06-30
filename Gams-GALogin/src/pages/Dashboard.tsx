import React from 'react';
import { useStore } from '../store/useStore';
import {
  AppWindow,
  Play,
  Network,
  Activity,
  Terminal,
  Trash2,
  TrendingUp,
  Cpu,
  Database,
  RotateCcw
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { profiles, proxies, logs, clearLogs, systemMetrics, resetServer } = useStore();

  const totalProfiles = profiles.length;
  const runningProfiles = profiles.filter((p) => p.status === 'running').length;
  const activeProxies = proxies.filter((pr) => pr.status === 'active').length;

  // Calculate circular SVG stroke dashoffsets
  const calculateCircleDashOffset = (percentage: number, radius = 40) => {
    const circumference = 2 * Math.PI * radius;
    return circumference - (percentage / 100) * circumference;
  };

  // Mock data for weekly activity SVG path
  const activityData = [45, 60, 52, 85, 70, 92, 110]; // last 7 days profile hours
  const svgWidth = 600;
  const svgHeight = 160;
  const maxVal = Math.max(...activityData);
  const minVal = 0;
  const points = activityData
    .map((val, index) => {
      const x = (index / (activityData.length - 1)) * (svgWidth - 40) + 20;
      const y = svgHeight - ((val - minVal) / (maxVal - minVal)) * (svgHeight - 40) - 20;
      return `${x},${y}`;
    })
    .join(' ');

  // SVG Area path closing it out at bottom
  const areaPoints = `
    20,${svgHeight - 10} 
    ${points} 
    ${(activityData.length - 1) * ((svgWidth - 40) / (activityData.length - 1)) + 20},${svgHeight - 10}
  `;

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Page Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-200">Trực quan Hệ thống</h2>
        <p className="text-xs text-slate-500">Tổng quan tình trạng vận hành, tài nguyên thiết bị và lịch trình hoạt động.</p>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        
        {/* Metric 1 */}
        <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 hover:border-slate-800 hover:bg-slate-900/30 transition-all duration-300 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-blue/5 rounded-full blur-2xl group-hover:bg-brand-blue/10 transition-colors"></div>
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-slate-500">Tổng số Profiles</p>
              <h3 className="text-2xl font-bold text-slate-200 mt-2 font-mono">{totalProfiles}</h3>
            </div>
            <div className="p-2.5 rounded-xl border border-brand-blue/20 bg-brand-blue/5 text-brand-blue">
              <AppWindow className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xxs text-slate-600 mt-4 flex items-center gap-1.5">
            <TrendingUp className="w-3 h-3 text-brand-emerald" />
            <span className="text-brand-emerald font-semibold">+12%</span> so với tuần trước
          </p>
        </div>

        {/* Metric 2 */}
        <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 hover:border-slate-800 hover:bg-slate-900/30 transition-all duration-300 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-purple/5 rounded-full blur-2xl group-hover:bg-brand-purple/10 transition-colors"></div>
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-slate-500">Browser Đang Chạy</p>
              <h3 className="text-2xl font-bold text-slate-200 mt-2 font-mono">{runningProfiles}</h3>
            </div>
            <div className="p-2.5 rounded-xl border border-brand-purple/20 bg-brand-purple/5 text-brand-purple">
              <Play className="w-5 h-5 fill-brand-purple/20" />
            </div>
          </div>
          <p className="text-xxs text-slate-600 mt-4 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-emerald animate-pulse-slow"></span>
            Cập nhật theo thời gian thực
          </p>
        </div>

        {/* Metric 3 */}
        <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 hover:border-slate-800 hover:bg-slate-900/30 transition-all duration-300 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-cyan/5 rounded-full blur-2xl group-hover:bg-brand-cyan/10 transition-colors"></div>
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-slate-500">Proxy Hoạt Động</p>
              <h3 className="text-2xl font-bold text-slate-200 mt-2 font-mono">{activeProxies}</h3>
            </div>
            <div className="p-2.5 rounded-xl border border-brand-cyan/20 bg-brand-cyan/5 text-brand-cyan">
              <Network className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xxs text-slate-600 mt-4">
            Tỷ lệ kết nối: <span className="font-semibold text-brand-emerald">{(activeProxies / (proxies.length || 1) * 100).toFixed(0)}%</span>
          </p>
        </div>

        {/* Metric 4 */}
        <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 hover:border-slate-800 hover:bg-slate-900/30 transition-all duration-300 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-brand-emerald/5 rounded-full blur-2xl group-hover:bg-brand-emerald/10 transition-colors"></div>
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-slate-500">Tốc Độ Băng Thông</p>
              <h3 className="text-2xl font-bold text-slate-200 mt-2 font-mono">{systemMetrics.networkSpeed} <span className="text-xs font-normal text-slate-500">KB/s</span></h3>
            </div>
            <div className="p-2.5 rounded-xl border border-brand-emerald/20 bg-brand-emerald/5 text-brand-emerald">
              <Activity className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xxs text-slate-600 mt-4">
            Đã đồng bộ tổng cộng: <span className="font-semibold text-slate-400">{systemMetrics.totalTraffic}</span>
          </p>
        </div>

      </div>

      {/* Middle Section: Chart & System Load */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        
        {/* Left 2 cols: SVG Chart Card */}
        <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-bold text-slate-300">Hoạt Động Profile</h4>
              <p className="text-xxs text-slate-500">Thời gian chạy tích lũy (giờ) của các browser 7 ngày gần nhất.</p>
            </div>
            <span className="text-xxs px-2.5 py-1 rounded-md border border-dark-border bg-slate-900/40 text-slate-400 font-semibold">
              Hàng tuần
            </span>
          </div>

          <div className="relative pt-4 w-full h-[180px] flex items-center justify-center">
            <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-full text-brand-blue">
              <defs>
                <linearGradient id="area-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--color-brand-blue)" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="var(--color-brand-blue)" stopOpacity="0" />
                </linearGradient>
              </defs>
              {/* Grid Lines */}
              <line x1="20" y1="20" x2={svgWidth - 20} y2="20" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
              <line x1="20" y1="60" x2={svgWidth - 20} y2="60" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
              <line x1="20" y1="100" x2={svgWidth - 20} y2="100" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
              <line x1="20" y1="140" x2={svgWidth - 20} y2="140" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
              
              {/* Chart Path Area */}
              <polygon points={areaPoints} fill="url(#area-grad)" />
              {/* Chart Line */}
              <polyline points={points} fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
              
              {/* Data circles & text */}
              {activityData.map((val, idx) => {
                const x = (idx / (activityData.length - 1)) * (svgWidth - 40) + 20;
                const y = svgHeight - ((val - minVal) / (maxVal - minVal)) * (svgHeight - 40) - 20;
                const days = ['T5', 'T6', 'T7', 'CN', 'T2', 'T3', 'T4'];
                return (
                  <g key={idx} className="group/dot cursor-pointer">
                    <circle cx={x} cy={y} r="4.5" fill="#12141c" stroke="var(--color-brand-blue)" strokeWidth="2" />
                    <text x={x} y={y - 10} textAnchor="middle" fill="#94a3b8" fontSize="9" fontWeight="bold" className="opacity-0 group-hover/dot:opacity-100 transition-opacity bg-slate-950 p-1">
                      {val}h
                    </text>
                    <text x={x} y={svgHeight - 2} textAnchor="middle" fill="#64748b" fontSize="8" fontWeight="bold">
                      {days[idx]}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>

        {/* Right 1 col: System Monitor Ring Charts */}
        <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 flex flex-col justify-between">
          <div>
            <h4 className="text-sm font-bold text-slate-300">Tải Kho Tài Nguyên</h4>
            <p className="text-xxs text-slate-500">Tỷ lệ tải phần cứng hiện tại của thiết bị.</p>
          </div>

          <div className="flex items-center justify-around py-4">
            
            {/* CPU Circular Chart */}
            <div className="flex flex-col items-center gap-2">
              <div className="relative w-24 h-24 flex items-center justify-center">
                <svg className="w-full h-full -rotate-90">
                  <circle cx="48" cy="48" r="40" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="6" />
                  <circle
                    cx="48"
                    cy="48"
                    r="40"
                    fill="none"
                    stroke="var(--color-brand-blue)"
                    strokeWidth="6"
                    strokeDasharray={2 * Math.PI * 40}
                    strokeDashoffset={calculateCircleDashOffset(systemMetrics.cpu)}
                    strokeLinecap="round"
                    className="transition-all duration-500"
                  />
                </svg>
                <div className="absolute flex flex-col items-center justify-center">
                  <Cpu className="w-4 h-4 text-brand-blue mb-0.5" />
                  <span className="text-sm font-bold text-slate-200 font-mono leading-none">{systemMetrics.cpu}%</span>
                </div>
              </div>
              <span className="text-xxs font-semibold text-slate-500">Tải CPU</span>
            </div>

            {/* RAM Circular Chart */}
            <div className="flex flex-col items-center gap-2">
              <div className="relative w-24 h-24 flex items-center justify-center">
                <svg className="w-full h-full -rotate-90">
                  <circle cx="48" cy="48" r="40" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="6" />
                  <circle
                    cx="48"
                    cy="48"
                    r="40"
                    fill="none"
                    stroke="var(--color-brand-purple)"
                    strokeWidth="6"
                    strokeDasharray={2 * Math.PI * 40}
                    strokeDashoffset={calculateCircleDashOffset(systemMetrics.ram)}
                    strokeLinecap="round"
                    className="transition-all duration-500"
                  />
                </svg>
                <div className="absolute flex flex-col items-center justify-center">
                  <Database className="w-4 h-4 text-brand-purple mb-0.5" />
                  <span className="text-sm font-bold text-slate-200 font-mono leading-none">{systemMetrics.ram}%</span>
                </div>
              </div>
              <span className="text-xxs font-semibold text-slate-500">RAM Sử Dụng</span>
            </div>

          </div>

          <span className="text-center text-xxs text-slate-600 block border-t border-dark-border/40 pt-3 leading-normal">
            💻 Tối ưu hóa Chromium giúp giảm 30% tài nguyên so với thông thường.
          </span>
        </div>

      </div>

      {/* Dynamic Shell Activity Terminal */}
      <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-brand-blue" />
            <h4 className="text-sm font-bold text-slate-300">Terminal Log Sự Kiện Hoạt Động</h4>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={async () => {
                if (window.confirm("Bạn có chắc chắn muốn đặt lại Máy chủ? Hành động này sẽ đóng lập tức toàn bộ các profile trình duyệt đang chạy (tương tự stop.bat).")) {
                  await resetServer();
                }
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-brand-rose/25 bg-brand-rose/5 text-brand-rose hover:bg-brand-rose/10 hover:border-brand-rose/50 transition-all text-xxs font-semibold cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Đặt lại Server</span>
            </button>
            <button
              onClick={clearLogs}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-dark-border bg-slate-900/40 text-slate-500 hover:text-brand-rose hover:border-brand-rose/20 transition-all text-xxs font-semibold cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Xóa Logs</span>
            </button>
          </div>
        </div>

        {/* Console Box */}
        <div className="h-52 rounded-xl bg-slate-950 border border-slate-900 p-4 font-mono text-xs overflow-y-auto space-y-2 select-text">
          {logs.length === 0 ? (
            <p className="text-slate-600 text-center py-12">Không có sự kiện hệ thống mới ghi nhận</p>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="flex gap-4 items-start select-text">
                <span className="text-slate-600 shrink-0 select-none">[{log.timestamp}]</span>
                <span className={`shrink-0 select-none uppercase font-bold text-[10px] px-1 rounded-sm ${
                  log.type === 'success' ? 'bg-brand-emerald/10 text-brand-emerald border border-brand-emerald/10' :
                  log.type === 'error' ? 'bg-brand-rose/10 text-brand-rose border border-brand-rose/10' :
                  log.type === 'warning' ? 'bg-brand-amber/10 text-brand-amber border border-brand-amber/10' :
                  'bg-brand-blue/10 text-brand-blue border border-brand-blue/10'
                }`}>
                  {log.type}
                </span>
                <span className={`break-words ${
                  log.type === 'success' ? 'text-slate-300' :
                  log.type === 'error' ? 'text-brand-rose/90' :
                  log.type === 'warning' ? 'text-brand-amber/90' :
                  'text-slate-400'
                }`}>
                  {log.message}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

    </div>
  );
};
