import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import { KeyRound, Mail, Eye, EyeOff, Loader2 } from 'lucide-react';

export const Login: React.FC = () => {
  const { login, forgotPassword, resetPassword } = useStore();
  const [email, setEmail] = useState('admin@giaancompany.io.vn');
  const [password, setPassword] = useState('password123');
  const [rememberMe, setRememberMe] = useState(true);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Recovery States
  const [viewMode, setViewMode] = useState<'login' | 'forgot' | 'reset'>('login');
  const [otpCode, setOtpCode] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    
    if (!email.includes('@')) {
      setError('Vui lòng nhập định dạng email hợp lệ!');
      return;
    }
    
    if (password.length < 6) {
      setError('Mật khẩu phải có tối thiểu 6 ký tự!');
      return;
    }
    
    setLoading(true);
    try {
      const success = await login(email, password, rememberMe);
      if (!success) {
        setError('Đăng nhập thất bại. Tài khoản hoặc mật khẩu không hợp lệ.');
      }
    } catch (err) {
      setError('Có lỗi xảy ra trong quá trình xác thực.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!email.includes('@')) {
      setError('Vui lòng nhập định dạng email hợp lệ!');
      return;
    }

    setLoading(true);
    try {
      const res = await forgotPassword(email);
      if (res.success) {
        setSuccessMsg(res.message);
        setViewMode('reset');
      } else {
        setError(res.message);
      }
    } catch (err: any) {
      setError('Lỗi gửi yêu cầu khôi phục mật khẩu.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (otpCode.length < 6) {
      setError('Mã xác thực OTP phải gồm 6 chữ số!');
      return;
    }

    if (newPassword.length < 6) {
      setError('Mật khẩu mới phải có tối thiểu 6 ký tự!');
      return;
    }

    setLoading(true);
    try {
      const res = await resetPassword(email, otpCode, newPassword);
      if (res.success) {
        setSuccessMsg('Đặt lại mật khẩu thành công! Vui lòng đăng nhập bằng mật khẩu mới.');
        setPassword(newPassword); // Auto-fill
        setViewMode('login');
      } else {
        setError(res.message);
      }
    } catch (err: any) {
      setError('Lỗi xác nhận đặt lại mật khẩu.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-screen bg-dark-bg flex items-center justify-center relative overflow-hidden bg-glow-purple bg-glow-blue select-none">
      
      {/* Background Decorative Rings */}
      <div className="absolute top-1/4 left-1/3 w-[500px] h-[500px] bg-brand-blue/5 rounded-full blur-[100px] pointer-events-none animate-pulse-slow"></div>
      <div className="absolute bottom-1/4 right-1/3 w-[600px] h-[600px] bg-brand-purple/5 rounded-full blur-[120px] pointer-events-none animate-pulse-slow"></div>

      {/* Main Container */}
      <div className="w-full max-w-md p-8 rounded-2xl glass-panel glass-card-glow shadow-2xl relative z-10 mx-4 animate-fade-in">
        
        {/* Header Logo */}
        <div className="flex flex-col items-center text-center mb-8">
          <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-blue to-brand-purple flex items-center justify-center shadow-xl shadow-brand-blue/20 mb-4">
            <svg
              className="w-8 h-8 text-white"
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
            <div className="absolute -inset-1 bg-gradient-to-tr from-brand-blue to-brand-purple rounded-2xl blur-xs opacity-60 -z-10 animate-pulse-slow"></div>
          </div>
          <h2 className="text-2xl font-bold tracking-wider bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
            Gams-GALogin
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {viewMode === 'login' && 'Phần mềm quản lý profile trình duyệt Chromium đa tài khoản'}
            {viewMode === 'forgot' && 'Khôi phục mật khẩu tài khoản qua SMTP/DNS'}
            {viewMode === 'reset' && 'Thiết lập mật khẩu mới thông qua mã xác thực'}
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-5 p-3 rounded-xl border border-brand-rose/20 bg-brand-rose/5 text-brand-rose text-xs flex items-center gap-2 animate-fade-in">
            <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {/* Success Message */}
        {successMsg && (
          <div className="mb-5 p-3 rounded-xl border border-brand-emerald/20 bg-brand-emerald/5 text-brand-emerald text-xs flex items-center gap-2 animate-fade-in">
            <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{successMsg}</span>
          </div>
        )}

        {/* LOGIN FORM */}
        {viewMode === 'login' && (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 block">Email đăng nhập</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ten@congtygiaan.vn"
                  disabled={loading}
                  className="w-full pl-11 pr-4 py-3 rounded-xl border border-dark-border bg-slate-900/40 text-sm text-slate-200 placeholder-slate-600 transition-all duration-300 focus:bg-slate-900/80 focus:border-brand-blue/50 focus:ring-2 focus:ring-brand-blue/10"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 block">Mật khẩu</label>
              <div className="relative">
                <KeyRound className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  disabled={loading}
                  className="w-full pl-11 pr-11 py-3 rounded-xl border border-dark-border bg-slate-900/40 text-sm text-slate-200 placeholder-slate-600 transition-all duration-300 focus:bg-slate-900/80 focus:border-brand-blue/50 focus:ring-2 focus:ring-brand-blue/10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-200 cursor-pointer p-0.5"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs pt-1">
              <label className="flex items-center gap-2 text-slate-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-slate-700 text-brand-blue focus:ring-0 w-4 h-4 bg-slate-900/40"
                />
                <span>Duy trì đăng nhập</span>
              </label>
              <button
                type="button"
                onClick={() => {
                  setError('');
                  setSuccessMsg('');
                  setViewMode('forgot');
                }}
                className="text-brand-blue hover:underline bg-transparent border-0 cursor-pointer focus:outline-none"
              >
                Quên mật khẩu?
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 mt-2 rounded-xl bg-gradient-to-r from-brand-blue to-brand-purple hover:from-brand-blue-hover hover:to-brand-purple-hover text-white text-sm font-semibold shadow-lg shadow-brand-blue/20 hover:shadow-brand-blue/30 transition-all active:scale-98 cursor-pointer flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Đang xác thực hệ thống...</span>
                </>
              ) : (
                <span>Đăng nhập Gams-GALogin</span>
              )}
            </button>
          </form>
        )}

        {/* FORGOT PASSWORD FORM */}
        {viewMode === 'forgot' && (
          <form onSubmit={handleForgotSubmit} className="space-y-5 animate-fade-in">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 block">Nhập Email nhận mã OTP</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ten@congtygiaan.vn"
                  disabled={loading}
                  className="w-full pl-11 pr-4 py-3 rounded-xl border border-dark-border bg-slate-900/40 text-sm text-slate-200 placeholder-slate-600 transition-all duration-300 focus:bg-slate-900/80 focus:border-brand-blue/50 focus:ring-2 focus:ring-brand-blue/10"
                />
              </div>
              <span className="text-xxs text-slate-500 block leading-relaxed">
                Mã xác thực sẽ được gửi trực tiếp qua cấu hình SMTP/DNS liên kết bảo mật với email của bạn.
              </span>
            </div>

            <div className="space-y-3 pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 rounded-xl bg-brand-purple hover:bg-brand-purple-hover text-white text-sm font-semibold transition-all active:scale-98 cursor-pointer flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Đang gửi mã...</span>
                  </>
                ) : (
                  <span>Gửi mã OTP khôi phục</span>
                )}
              </button>

              <button
                type="button"
                onClick={() => {
                  setError('');
                  setSuccessMsg('');
                  setViewMode('login');
                }}
                className="w-full py-3 rounded-xl border border-dark-border bg-slate-900/20 text-slate-400 hover:text-white hover:bg-slate-900/40 text-xs font-semibold transition-all cursor-pointer"
              >
                Quay lại đăng nhập
              </button>
            </div>
          </form>
        )}

        {/* RESET PASSWORD FORM */}
        {viewMode === 'reset' && (
          <form onSubmit={handleResetSubmit} className="space-y-5 animate-fade-in">
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 block">Mã xác thực OTP (6 chữ số)</label>
              <input
                type="text"
                required
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                placeholder="123456"
                disabled={loading}
                className="w-full px-4 py-3 rounded-xl border border-dark-border bg-slate-900/40 text-sm text-slate-200 placeholder-slate-600 transition-all duration-300 text-center tracking-widest font-mono text-lg focus:bg-slate-900/80 focus:border-brand-blue/50"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 block">Mật khẩu mới (Tối thiểu 6 ký tự)</label>
              <div className="relative">
                <KeyRound className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Nhập mật khẩu mới"
                  disabled={loading}
                  className="w-full pl-11 pr-11 py-3 rounded-xl border border-dark-border bg-slate-900/40 text-sm text-slate-200 placeholder-slate-600 transition-all duration-300 focus:bg-slate-900/80 focus:border-brand-blue/50 focus:ring-2 focus:ring-brand-blue/10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-200 cursor-pointer p-0.5"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-brand-blue to-brand-purple hover:from-brand-blue-hover hover:to-brand-purple-hover text-white text-sm font-semibold transition-all active:scale-98 cursor-pointer flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Đang đặt lại mật khẩu...</span>
                  </>
                ) : (
                  <span>Xác nhận đặt lại mật khẩu</span>
                )}
              </button>

              <button
                type="button"
                onClick={() => {
                  setError('');
                  setSuccessMsg('');
                  setViewMode('login');
                }}
                className="w-full py-3 rounded-xl border border-dark-border bg-slate-900/20 text-slate-400 hover:text-white hover:bg-slate-900/40 text-xs font-semibold transition-all cursor-pointer"
              >
                Quay lại đăng nhập
              </button>
            </div>
          </form>
        )}

        {/* Footnote */}
        <div className="mt-8 text-center text-xxs text-slate-600 border-t border-dark-border/50 pt-5">
          <span>Hệ thống bảo mật cấp doanh nghiệp • © 2026 Gams Co., Ltd.</span>
        </div>

      </div>
    </div>
  );
};
