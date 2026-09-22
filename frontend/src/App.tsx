import React, { useEffect, useState } from 'react';
import { Sidebar, TabType } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { Dashboard } from './pages/Dashboard';
import { LiveView } from './pages/LiveView';
import { Events } from './pages/Events';
import { Playback } from './pages/Playback';
import { Cameras } from './pages/Cameras';
import { Storage } from './pages/Storage';
import { UsersPage } from './pages/Users';
import { AuditLogs } from './pages/AuditLogs';
import { SettingsPage } from './pages/Settings';
import { Login } from './pages/Login';
import { UserRole } from './constants';
import { wsService } from './services/websocket';
import { camerasApi } from './services/api';

export const App: React.FC = () => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('localvision_token'));
  const [currentUser, setCurrentUser] = useState<any>(() => {
    const saved = localStorage.getItem('localvision_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [currentTab, setCurrentTab] = useState<TabType>('dashboard');
  const [unreadEvents, setUnreadEvents] = useState<any[]>([]);
  const [activeCamerasCount, setActiveCamerasCount] = useState<number>(0);

  // Oturum açıldığında WebSocket'i bağla
  useEffect(() => {
    if (token) {
      wsService.connect();

      const unsubscribe = wsService.subscribe((event) => {
        if (event.type === 'new_event') {
          setUnreadEvents((prev) => [event, ...prev]);
        }
      });

      // Aktif kamera sayısını sorgula
      camerasApi.list().then((res) => {
        setActiveCamerasCount(res.data.length);
      }).catch(() => {});

      return () => {
        unsubscribe();
        wsService.disconnect();
      };
    }
  }, [token]);

  const handleLoginSuccess = (user: any, newToken: string) => {
    setCurrentUser(user);
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('localvision_token');
    localStorage.removeItem('localvision_user');
    setToken(null);
    setCurrentUser(null);
  };

  if (!token || !currentUser) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  const role = (currentUser.role as UserRole) || UserRole.USER;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-dark-900 text-slate-100 selection:bg-brand-500 selection:text-white">
      {/* Sol Kenar Çubuğu */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => {
          setCurrentTab(tab);
          if (tab === 'events') {
            setUnreadEvents([]);
          }
        }}
        userRole={role}
        unreadEventsCount={unreadEvents.length}
      />

      {/* Ana İçerik Alanı */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Üst Bar */}
        <Header
          username={currentUser.username}
          userRole={role}
          unreadEvents={unreadEvents}
          onLogout={handleLogout}
          onViewEvents={() => {
            setCurrentTab('events');
            setUnreadEvents([]);
          }}
          activeCamerasCount={activeCamerasCount}
        />

        {/* Sekme İçeriği */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            {currentTab === 'dashboard' && <Dashboard onNavigateTab={setCurrentTab} />}
            {currentTab === 'live' && <LiveView />}
            {currentTab === 'events' && <Events />}
            {currentTab === 'playback' && <Playback />}
            {currentTab === 'cameras' && <Cameras />}
            {currentTab === 'storage' && <Storage />}
            {currentTab === 'users' && <UsersPage />}
            {currentTab === 'audit' && <AuditLogs />}
            {currentTab === 'settings' && <SettingsPage />}
          </div>
        </main>
      </div>
    </div>
  );
};
