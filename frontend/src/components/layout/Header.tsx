import React, { useState } from 'react';
import { BellIcon, LogOutIcon } from '../common/Icons';
import { USER_ROLE_LABELS, UserRole } from '../../constants';

interface HeaderProps {
  username: string;
  userRole: UserRole;
  unreadEvents: any[];
  onLogout: () => void;
  onViewEvents: () => void;
  activeCamerasCount: number;
}

export const Header: React.FC<HeaderProps> = ({
  username,
  userRole,
  unreadEvents,
  onLogout,
  onViewEvents,
  activeCamerasCount,
}) => {
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <header className="h-16 bg-dark-800/80 backdrop-blur-md border-b border-dark-700 px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Sol: Sistem Durum Özeti */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-dark-900/60 border border-dark-700 text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-slate-300 font-medium">Yerel NVR Aktif</span>
          <span className="text-slate-500">|</span>
          <span className="text-accent-cyan font-medium">{activeCamerasCount} Kamera Yayında</span>
        </div>
      </div>

      {/* Sağ: Bildirimler ve Kullanıcı Bilgisi */}
      <div className="flex items-center gap-4">
        {/* Bildirim Zili */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2.5 rounded-xl bg-dark-700/60 hover:bg-dark-700 text-slate-300 hover:text-white transition-colors relative cursor-pointer"
            aria-label="Bildirimler"
          >
            <BellIcon className="w-5 h-5" />
            {unreadEvents.length > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center animate-bounce">
                {unreadEvents.length}
              </span>
            )}
          </button>

          {/* Bildirim Açılır Kutusu */}
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-dark-800 border border-dark-700 rounded-2xl shadow-2xl overflow-hidden z-50 animate-fade-in">
              <div className="p-3 border-b border-dark-700 flex items-center justify-between bg-dark-900/50">
                <span className="text-xs font-semibold text-white">Son Olay Bildirimleri</span>
                <button
                  onClick={() => {
                    setShowNotifications(false);
                    onViewEvents();
                  }}
                  className="text-xs text-brand-500 hover:underline cursor-pointer"
                >
                  Tümünü Gör
                </button>
              </div>
              <div className="max-h-64 overflow-y-auto divide-y divide-dark-700/50">
                {unreadEvents.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-400">Yeni olay bulunmuyor.</div>
                ) : (
                  unreadEvents.slice(0, 5).map((ev, idx) => (
                    <div key={idx} className="p-3 hover:bg-dark-700/40 transition-colors text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-200">{ev.camera_name}</span>
                        <span className="text-[10px] text-slate-400">
                          {new Date(ev.created_at).toLocaleTimeString('tr-TR')}
                        </span>
                      </div>
                      <p className="text-slate-400 text-[11px] capitalize">{ev.event_type.replace('_', ' ')}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Kullanıcı Profili ve Rolü */}
        <div className="flex items-center gap-3 pl-3 border-l border-dark-700">
          <div className="text-right">
            <div className="text-sm font-semibold text-white leading-tight">{username}</div>
            <div className="text-[11px] text-slate-400">{USER_ROLE_LABELS[userRole] || userRole}</div>
          </div>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-600 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-md">
            {username.charAt(0).toUpperCase()}
          </div>
          <button
            onClick={onLogout}
            title="Güvenli Çıkış"
            className="p-2 text-slate-400 hover:text-rose-400 hover:bg-dark-700 rounded-lg transition-colors cursor-pointer"
          >
            <LogOutIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  );
};
