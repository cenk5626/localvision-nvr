import React from 'react';
import {
  CameraIcon,
  DashboardIcon,
  HistoryIcon,
  PlayIcon,
  SettingsIcon,
  ShieldAlertIcon,
  StorageIcon,
  UsersIcon,
} from '../common/Icons';
import { UserRole } from '../../constants';

export type TabType =
  | 'dashboard'
  | 'live'
  | 'events'
  | 'playback'
  | 'cameras'
  | 'storage'
  | 'users'
  | 'audit'
  | 'settings';

interface SidebarProps {
  currentTab: TabType;
  onSelectTab: (tab: TabType) => void;
  userRole: UserRole;
  unreadEventsCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  userRole,
  unreadEventsCount,
}) => {
  const isAdmin = userRole === UserRole.ADMIN;
  const isOperatorOrAdmin = userRole === UserRole.ADMIN || userRole === UserRole.OPERATOR;

  const navItems = [
    { id: 'dashboard' as TabType, label: 'Genel Durum', icon: DashboardIcon },
    { id: 'live' as TabType, label: 'Canlı İzleme', icon: CameraIcon },
    {
      id: 'events' as TabType,
      label: 'Olay Merkezi',
      icon: ShieldAlertIcon,
      badge: unreadEventsCount > 0 ? unreadEventsCount : undefined,
    },
    { id: 'playback' as TabType, label: 'Geçmiş Kayıt', icon: PlayIcon },
    { id: 'cameras' as TabType, label: 'Kameralar', icon: HistoryIcon },
    { id: 'storage' as TabType, label: 'Depolama', icon: StorageIcon, hidden: !isOperatorOrAdmin },
    { id: 'users' as TabType, label: 'Kullanıcılar', icon: UsersIcon, hidden: !isAdmin },
    { id: 'settings' as TabType, label: 'Ayarlar & Gizlilik', icon: SettingsIcon },
  ];

  return (
    <aside className="w-64 bg-dark-800 border-r border-dark-700 flex flex-col shrink-0 min-h-screen">
      {/* Logo & Marka */}
      <div className="h-16 flex items-center gap-3 px-6 border-b border-dark-700 bg-dark-900/40">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-accent-cyan flex items-center justify-center shadow-lg shadow-brand-500/20">
          <CameraIcon className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-white tracking-tight leading-none text-base">LocalVision</h1>
          <span className="text-[10px] text-accent-cyan font-medium uppercase tracking-wider">NVR / VMS</span>
        </div>
      </div>

      {/* Navigasyon Linkleri */}
      <nav className="p-3 space-y-1 flex-1">
        {navItems
          .filter((item) => !item.hidden)
          .map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-medium transition-all duration-150 cursor-pointer ${
                  isActive
                    ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-dark-700/60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-rose-500 text-white animate-pulse">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
      </nav>

      {/* Çevrimdışı Güvenlik Rozeti */}
      <div className="p-4 m-3 rounded-xl bg-dark-900/80 border border-dark-700/80 text-xs text-slate-400 space-y-1">
        <div className="flex items-center gap-2 text-emerald-400 font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          Yerel Ağ Koruması
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Sistem %100 çevrimdışı ve gizlilik odaklı çalışmaktadır. Bulut transferi kapalıdır.
        </p>
      </div>
    </aside>
  );
};
