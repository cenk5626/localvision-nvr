import React, { useState } from 'react';
import { CameraIcon } from '../components/common/Icons';
import { authApi } from '../services/api';

interface LoginProps {
  onLoginSuccess: (user: any, token: string) => void;
}

export const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('Admin*LocalVision2026!');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const res = await authApi.login({ username, password });
      const data = res.data;
      localStorage.setItem('localvision_token', data.access_token);
      localStorage.setItem('localvision_user', JSON.stringify(data));
      onLoginSuccess(data, data.access_token);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Giriş yapılamadı. Bilgilerinizi kontrol edin.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900">
      <div className="w-full max-w-md bg-dark-800/90 backdrop-blur-xl border border-dark-700/80 rounded-3xl p-8 shadow-2xl space-y-6">
        {/* Logo */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-tr from-brand-600 to-accent-cyan flex items-center justify-center shadow-xl shadow-brand-600/30">
            <CameraIcon className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">LocalVision NVR</h2>
          <p className="text-xs text-slate-400">Yerel Ağ Odaklı Güvenlik & Gizlilik Tasarımlı VMS</p>
        </div>

        {/* Hata Mesajı */}
        {errorMessage && (
          <div className="p-3 bg-rose-500/15 border border-rose-500/30 rounded-xl text-xs text-rose-400">
            {errorMessage}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Kullanıcı Adı</label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
              placeholder="admin"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Parola</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-dark-900 border border-dark-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm transition-all shadow-lg shadow-brand-600/30 disabled:opacity-50 cursor-pointer"
          >
            {isLoading ? 'Giriş Yapılıyor...' : 'Oturum Aç'}
          </button>

          <div className="relative flex py-1 items-center">
            <div className="flex-grow border-t border-dark-700"></div>
            <span className="flex-shrink mx-3 text-[11px] text-slate-500 uppercase tracking-wider font-semibold">veya</span>
            <div className="flex-grow border-t border-dark-700"></div>
          </div>

          <button
            type="button"
            onClick={async () => {
              setIsLoading(true);
              try {
                const res = await authApi.login({ username: 'demo', password: '' });
                onLoginSuccess(res.data, res.data.access_token);
              } finally {
                setIsLoading(false);
              }
            }}
            disabled={isLoading}
            className="w-full py-3 px-4 rounded-xl bg-dark-700/80 hover:bg-dark-600 text-slate-200 hover:text-white font-medium text-xs transition-all border border-dark-600 cursor-pointer flex items-center justify-center space-x-2"
          >
            <span>✨ Demo Modunda Keşfet (Vercel Vitrin)</span>
          </button>
        </form>

        {/* Demo Bilgisi */}
        <div className="p-3.5 rounded-xl bg-dark-900/60 border border-dark-700 text-xs text-slate-400 space-y-1">
          <span className="font-semibold text-slate-300">Yerel NVR Giriş Bilgileri:</span>
          <div className="font-mono text-[11px] text-accent-cyan">admin / Admin*LocalVision2026!</div>
          <div className="text-[10px] text-slate-500">Vercel üzerinde arka uç olmadan test etmek için üstteki Demo butonunu kullanabilirsiniz.</div>
        </div>
      </div>
    </div>
  );
};
