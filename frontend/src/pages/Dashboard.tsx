import React, { useEffect, useState } from 'react';
import { Camera, EventItem, SystemHealth } from '../types';
import { camerasApi, eventsApi, systemApi } from '../services/api';
import { CameraTile } from '../components/live/CameraTile';
import { EVENT_TYPE_LABELS, CameraStatus } from '../constants';
import { CameraIcon, ShieldAlertIcon, StorageIcon } from '../components/common/Icons';

interface DashboardProps {
  onNavigateTab: (tab: any) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigateTab }) => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [recentEvents, setRecentEvents] = useState<EventItem[]>([]);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [camsRes, eventsRes, healthRes] = await Promise.all([
          camerasApi.list(),
          eventsApi.list({ limit: 6 }),
          systemApi.getHealth(),
        ]);
        setCameras(camsRes.data);
        setRecentEvents(eventsRes.data);
        setHealth(healthRes.data);
      } catch (err) {
        // ignore
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();

    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, []);

  const onlineCamerasCount = cameras.filter((c) => c.status === CameraStatus.ONLINE).length;

  return (
    <div className="space-y-6">
      {/* Üst Karşılama ve Metrik Kartları */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Sistem Genel Durumu</h2>
          <p className="text-xs text-slate-400">
            Yerel NVR güvenlik ve algılama motoru aktif çalışıyor.
          </p>
        </div>
        <button
          onClick={() => onNavigateTab('live')}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-brand-600/20 transition-colors cursor-pointer"
        >
          Canlı İzleme Ekranını Aç →
        </button>
      </div>

      {/* İstatistik Kartları */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Kart 1: Kameralar */}
        <div className="p-5 bg-dark-800 border border-dark-700 rounded-2xl space-y-2 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Kameralar</span>
            <div className="p-2 rounded-xl bg-brand-600/20 text-brand-400">
              <CameraIcon className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{cameras.length}</span>
            <span className="text-xs text-emerald-400 font-medium">({onlineCamerasCount} Çevrimiçi)</span>
          </div>
          <p className="text-[11px] text-slate-500">RTSP & Yerel PC Web Kamerası</p>
        </div>

        {/* Kart 2: Yapay Zeka Olayları */}
        <div className="p-5 bg-dark-800 border border-dark-700 rounded-2xl space-y-2 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Son Olaylar</span>
            <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400">
              <ShieldAlertIcon className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">{recentEvents.length}</span>
            <span className="text-xs text-slate-400 font-medium">Kayıtlı İhlal</span>
          </div>
          <p className="text-[11px] text-slate-500">İnsan & Araç Tespitleri</p>
        </div>

        {/* Kart 3: Depolama */}
        <div className="p-5 bg-dark-800 border border-dark-700 rounded-2xl space-y-2 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Depolama Alanı</span>
            <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400">
              <StorageIcon className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">
              {health?.disk.free_gb ?? 0} GB
            </span>
            <span className="text-xs text-slate-400 font-medium">Boş</span>
          </div>
          <div className="w-full bg-dark-700 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-emerald-500 h-1.5 rounded-full"
              style={{ width: `${100 - (health?.disk.free_percent || 0)}%` }}
            ></div>
          </div>
        </div>

        {/* Kart 4: Sistem Performansı */}
        <div className="p-5 bg-dark-800 border border-dark-700 rounded-2xl space-y-2 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Sunucu Sağlığı</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              Stabil
            </span>
          </div>
          <div className="flex items-baseline gap-3 text-sm">
            <div>
              <span className="text-slate-400 text-xs">CPU: </span>
              <span className="font-bold text-white">{health?.cpu_percent ?? 0}%</span>
            </div>
            <div>
              <span className="text-slate-400 text-xs">RAM: </span>
              <span className="font-bold text-white">{health?.memory_percent ?? 0}%</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-500">
            Çalışma Süresi: {Math.floor((health?.uptime_seconds ?? 0) / 60)} dakika
          </p>
        </div>
      </div>

      {/* Orta Bölüm: Hızlı Canlı İzleme & Son Olaylar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Canlı Önizleme (2 Sütun) */}
        <div className="lg:col-span-2 bg-dark-800 border border-dark-700 rounded-2xl p-5 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Canlı Kamera Akışları</h3>
            <button
              onClick={() => onNavigateTab('live')}
              className="text-xs text-brand-400 hover:underline cursor-pointer"
            >
              Tümünü Genişlet →
            </button>
          </div>

          {cameras.length === 0 ? (
            <div className="p-12 text-center text-slate-400 border border-dashed border-dark-700 rounded-xl space-y-2">
              <p className="text-sm">Henüz eklenmiş kamera bulunmuyor.</p>
              <button
                onClick={() => onNavigateTab('cameras')}
                className="text-xs text-brand-400 hover:underline font-medium cursor-pointer"
              >
                + Kamera Ekle
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {cameras.slice(0, 4).map((camera) => (
                <div key={camera.id} className="h-56">
                  <CameraTile camera={camera} />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Son Olaylar Listesi (1 Sütun) */}
        <div className="bg-dark-800 border border-dark-700 rounded-2xl p-5 space-y-4 shadow-xl flex flex-col">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Son Algılanan Olaylar</h3>
            <button
              onClick={() => onNavigateTab('events')}
              className="text-xs text-brand-400 hover:underline cursor-pointer"
            >
              Olay Merkezi →
            </button>
          </div>

          <div className="space-y-3 flex-1 overflow-y-auto max-h-[460px]">
            {recentEvents.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">
                Henüz yapay zekâ olayı tetiklenmedi. Kamera karşısına bir kişi geçtiğinde burada listelenecektir.
              </div>
            ) : (
              recentEvents.map((ev) => {
                const config = EVENT_TYPE_LABELS[ev.event_type] || {
                  label: ev.event_type,
                  badgeColor: 'bg-dark-700 text-slate-300',
                };
                return (
                  <div
                    key={ev.id}
                    onClick={() => onNavigateTab('events')}
                    className="p-3 bg-dark-900/60 hover:bg-dark-700/50 border border-dark-700 rounded-xl flex items-center gap-3 transition-colors cursor-pointer"
                  >
                    {/* Küçük Resim */}
                    <div className="w-14 h-14 bg-black rounded-lg overflow-hidden shrink-0 border border-dark-700">
                      {ev.snapshot_url ? (
                        <img
                          src={ev.snapshot_url}
                          alt="Snapshot"
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-slate-600 text-[10px]">
                          Fotoğraf Yok
                        </div>
                      )}
                    </div>

                    {/* Olay Detayı */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-1">
                        <span className="text-xs font-semibold text-white truncate">{ev.camera_name}</span>
                        <span className="text-[10px] text-slate-400 shrink-0">
                          {new Date(ev.created_at).toLocaleTimeString('tr-TR')}
                        </span>
                      </div>
                      <span className={`inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-medium border ${config.badgeColor}`}>
                        {config.label}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
