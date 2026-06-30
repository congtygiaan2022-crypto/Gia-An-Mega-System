import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import {
  Play,
  Clock,
  Code,
  Terminal,
  Activity,
  HelpCircle
} from 'lucide-react';

export const Automation: React.FC = () => {
  const { profiles, addLog } = useStore();

  const [selectedProfileId, setSelectedProfileId] = useState(profiles[0]?.id || '');
  const [scriptText, setScriptText] = useState(`// Gams-GA Automation Script v1.0
async function runWorkflow() {
  await browser.goto('https://facebook.com');
  await browser.waitForSelector('input[name="email"]');
  await browser.type('input[name="email"]', 'my-email@gmail.com');
  await browser.wait(1500);
  await browser.click('button[name="login"]');
  await browser.screenshot('login_page.png');
}`);

  const [running, setRunning] = useState(false);
  const [consoleLogs, setConsoleLogs] = useState<string[]>([]);
  const [apiPort, setApiPort] = useState('1010');
  const [apiActive, setApiActive] = useState(true);

  // Mock Tasks
  const tasks = [
    { id: 't-1', name: 'Auto Warmup Cookies', profile: 'Facebook Ad Account 01', trigger: 'Mỗi 12 giờ', status: 'Scheduled' },
    { id: 't-2', name: 'Ad Campaign Metrics sync', profile: 'Google Ads Agency Profile', trigger: 'Mỗi 2 giờ', status: 'Idle' },
    { id: 't-3', name: 'Twitter bot auto-post', profile: 'Twitter/X Automation Bot 09', trigger: 'Mỗi 1 giờ', status: 'Running' }
  ];

  const handleRunScript = async () => {
    if (!selectedProfileId) {
      alert('Vui lòng chọn profile cần chạy kịch bản tự động hóa!');
      return;
    }
    setRunning(true);
    setConsoleLogs([]);
    
    const profileName = profiles.find(p => p.id === selectedProfileId)?.name || 'Profile';
    addLog(`Bắt đầu chạy kịch bản tự động hóa trên "${profileName}"`, 'info');

    const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));
    
    const steps = [
      `[INFO] Đang kết nối tới cổng Local API: http://127.0.0.1:${apiPort}`,
      `[INFO] Đang khởi chạy Chromium đầu cuối của profile: "${profileName}"...`,
      `[SUCCESS] Đã kết nối thành công với phiên Chromium DevTools (CDP).`,
      `[INFO] Thao tác: Điều hướng tới https://facebook.com`,
      `[INFO] Thao tác: Đang đợi selector "input[name='email']" xuất hiện...`,
      `[INFO] Thao tác: Nhập giá trị "my-email@gmail.com" vào ô nhập liệu.`,
      `[INFO] Thao tác: Click nút "Đăng nhập" (button[name='login'])`,
      `[INFO] Thao tác: Chụp màn hình trạng thái và lưu tại "login_page.png"`,
      `[SUCCESS] Kịch bản tự động hóa hoàn tất không có lỗi.`
    ];

    for (let i = 0; i < steps.length; i++) {
      setConsoleLogs(prev => [...prev, steps[i]]);
      await sleep(1000);
    }
    
    setRunning(false);
    addLog(`Kịch bản tự động hóa trên "${profileName}" hoàn tất.`, 'success');
  };

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-200">Automation Center</h2>
        <p className="text-xs text-slate-500">Tự động hóa các thao tác trên trình duyệt, lập lịch chạy bot và cấu hình API tích hợp.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        
        {/* Left Column: Script Canvas and Execution logs */}
        <div className="lg:col-span-2 space-y-5">
          
          {/* Script Editor Card */}
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code className="w-5 h-5 text-brand-blue" />
                <h4 className="text-sm font-bold text-slate-300">Biên soạn kịch bản Puppeteer / Playwright API</h4>
              </div>
              <div className="flex items-center gap-3">
                <select
                  value={selectedProfileId}
                  onChange={(e) => setSelectedProfileId(e.target.value)}
                  className="px-3 py-1.5 rounded-lg border border-dark-border bg-slate-950/40 text-xs text-slate-300 cursor-pointer"
                >
                  <option value="" disabled>-- Chọn profile chạy script --</option>
                  {profiles.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleRunScript}
                  disabled={running || !selectedProfileId}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-brand-blue hover:bg-brand-blue-hover text-white text-xs font-semibold shadow-xs transition-all disabled:opacity-50 cursor-pointer"
                >
                  <Play className="w-3.5 h-3.5 fill-white" />
                  <span>Chạy kịch bản</span>
                </button>
              </div>
            </div>

            <textarea
              value={scriptText}
              onChange={(e) => setScriptText(e.target.value)}
              rows={8}
              className="w-full px-4 py-3 rounded-xl border border-dark-border bg-slate-950/40 text-xs text-slate-300 font-mono focus:bg-slate-900 leading-relaxed"
            ></textarea>
          </div>

          {/* Console Output Terminal */}
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-3">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-brand-blue" />
              <h4 className="text-sm font-bold text-slate-300">Bảng điều khiển (Console)</h4>
            </div>

            <div className="h-44 rounded-xl bg-slate-950 border border-slate-900 p-4 font-mono text-xs overflow-y-auto space-y-1.5 select-text">
              {consoleLogs.length === 0 ? (
                <p className="text-slate-700 italic">Nhấp "Chạy kịch bản" để bắt đầu thực thi chuỗi kịch bản.</p>
              ) : (
                consoleLogs.map((log, index) => (
                  <div key={index} className="flex gap-2">
                    <span className="text-slate-600 select-none">&gt;</span>
                    <span className={
                      log.includes('[SUCCESS]') ? 'text-brand-emerald' :
                      log.includes('[ERROR]') ? 'text-brand-rose' :
                      'text-slate-300'
                    }>
                      {log}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

        {/* Right Column: Scheduler & API info */}
        <div className="space-y-5">
          
          {/* Automation scheduler */}
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
            
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-brand-purple" />
              <h4 className="text-sm font-bold text-slate-300">Lập Lịch Chạy Bot (Scheduler)</h4>
            </div>

            <div className="space-y-2">
              {tasks.map((task) => (
                <div key={task.id} className="p-3 rounded-xl border border-dark-border bg-slate-950/40 flex items-center justify-between text-xxs">
                  <div>
                    <span className="font-semibold text-slate-300 block">{task.name}</span>
                    <span className="text-slate-500 block truncate max-w-[150px] mt-0.5">{task.profile}</span>
                    <span className="text-slate-600 mt-1 block font-mono">Lặp lại: {task.trigger}</span>
                  </div>
                  <div className="text-right">
                    {task.status === 'Running' && (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-brand-emerald/10 text-brand-emerald border border-brand-emerald/20 animate-pulse-slow">
                        Đang chạy
                      </span>
                    )}
                    {task.status === 'Scheduled' && (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-brand-blue/10 text-brand-blue border border-brand-blue/20">
                        Đã lên lịch
                      </span>
                    )}
                    {task.status === 'Idle' && (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-900 text-slate-500 border border-dark-border">
                        Đang chờ
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>

          </div>

          {/* Local API server */}
          <div className="p-5 rounded-2xl border border-dark-border bg-slate-900/20 space-y-4">
            
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-brand-cyan" />
                <h4 className="text-sm font-bold text-slate-300">Kiểm soát API Nội Bộ</h4>
              </div>
              
              {/* Toggle API */}
              <button
                onClick={() => setApiActive(!apiActive)}
                className={`w-9 h-5 rounded-full p-0.5 transition-colors duration-300 cursor-pointer ${
                  apiActive ? 'bg-brand-blue' : 'bg-slate-800'
                }`}
              >
                <div className={`w-4 h-4 rounded-full bg-white transition-transform duration-300 ${
                  apiActive ? 'translate-x-4' : 'translate-x-0'
                }`}></div>
              </button>
            </div>

            <div className="space-y-3 text-xxs">
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Địa chỉ API:</span>
                <span className="font-mono font-semibold text-slate-300">http://127.0.0.1:{apiPort}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Trạng thái API Server:</span>
                <span>
                  {apiActive ? (
                    <span className="text-brand-emerald font-semibold">● ĐANG CHẠY</span>
                  ) : (
                    <span className="text-slate-500 font-semibold">○ ĐÃ DỪNG</span>
                  )}
                </span>
              </div>
              
              <div className="pt-2">
                <label className="text-slate-500 block mb-1">Cổng dịch vụ (Port)</label>
                <input
                  type="text"
                  value={apiPort}
                  onChange={(e) => setApiPort(e.target.value)}
                  disabled={!apiActive}
                  className="w-full px-3 py-1.5 rounded-lg border border-dark-border bg-slate-950/40 text-xxs font-mono text-slate-300"
                />
              </div>
            </div>

            <span className="text-center text-xxs text-slate-600 block border-t border-dark-border/40 pt-3 flex items-center justify-center gap-1">
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Xem tài liệu API tự động hóa Python/NodeJS</span>
            </span>

          </div>

        </div>

      </div>

    </div>
  );
};
