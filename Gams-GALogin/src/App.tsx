import { useEffect } from 'react';
import { useStore } from './store/useStore';
import { Sidebar } from './components/Sidebar';
import { Topbar } from './components/Topbar';
import { CreateProfileModal } from './components/CreateProfileModal';

// Pages
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Profiles } from './pages/Profiles';
import { Proxies } from './pages/Proxies';
import { Cookies } from './pages/Cookies';
import { Automation } from './pages/Automation';
import { SettingsPage } from './pages/Settings';
import { ApiGuide } from './pages/ApiGuide';
import { UserAgents } from './pages/UserAgents';
import { Templates } from './pages/Templates';

function App() {
  const { isAuthenticated, activeTab, updateMetrics, syncProfiles, fetchServerStatus } = useStore();

  // Fetch initial profiles and status if already authenticated (e.g. via cookie)
  useEffect(() => {
    if (isAuthenticated) {
      syncProfiles();
      fetchServerStatus();
    }
  }, [isAuthenticated, syncProfiles, fetchServerStatus]);

  // Run dynamic resource metrics simulator
  useEffect(() => {
    if (!isAuthenticated) return;
    
    // Initial update
    updateMetrics();
    
    // Interval update every 3 seconds
    const interval = setInterval(() => {
      updateMetrics();
    }, 3000);

    return () => clearInterval(interval);
  }, [isAuthenticated, updateMetrics]);

  // Route views
  const renderActivePage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'profiles':
        return <Profiles />;
      case 'proxies':
        return <Proxies />;
      case 'cookies':
        return <Cookies />;
      case 'user-agents':
        return <UserAgents />;
      case 'templates':
        return <Templates />;
      case 'automation':
        return <Automation />;
      case 'api-guide':
        return <ApiGuide />;
      case 'settings':
        return <SettingsPage />;
      case 'account':
        return (
          <div className="p-6 rounded-2xl border border-dark-border bg-slate-900/20 text-center space-y-4 max-w-xl mx-auto animate-fade-in">
            <h3 className="text-lg font-bold text-slate-200">Tài Khoản Gams-GALogin</h3>
            <p className="text-xs text-slate-500">Quản lý cấu hình đăng ký, giấy phép (License) và khóa bảo mật API.</p>
            <div className="border border-dark-border p-4 rounded-xl text-left text-xs space-y-2 font-mono bg-slate-950/40">
              <p><span className="text-slate-500">License Type:</span> <span className="text-brand-purple font-semibold">Enterprise License</span></p>
              <p><span className="text-slate-500">Valid Until:</span> <span className="text-slate-300">2027-12-31</span></p>
              <p><span className="text-slate-500">Max Profiles limit:</span> <span className="text-slate-300">Unlimited</span></p>
              <p><span className="text-slate-500">Owner Email:</span> <span className="text-slate-300">admin@giaancompany.io.vn</span></p>
            </div>
            <button
              onClick={() => alert('Liên hệ Support Gia An để cập nhật License')}
              className="px-5 py-2.5 rounded-xl bg-slate-900 border border-dark-border hover:border-slate-700 text-slate-300 text-xs font-semibold cursor-pointer"
            >
              Gia hạn bản quyền
            </button>
          </div>
        );
      default:
        return <Dashboard />;
    }
  };

  // Login Gate
  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <div className="flex w-screen h-screen bg-dark-bg text-slate-200 overflow-hidden relative font-sans">
      
      {/* Sidebar Menu */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        
        {/* Topbar Controls */}
        <Topbar />

        {/* Dynamic Inner View Scroll Wrapper */}
        <main className="flex-1 overflow-y-auto p-8 bg-slate-950/20 relative">
          <div className="max-w-7xl mx-auto w-full">
            {renderActivePage()}
          </div>
        </main>

      </div>

      {/* Profile Creation Modal Dialog */}
      <CreateProfileModal />

    </div>
  );
}

export default App;
