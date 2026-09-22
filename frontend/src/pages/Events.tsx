import React, { useEffect, useState } from 'react';
import { Camera, EventItem } from '../types';
import { camerasApi, eventsApi } from '../services/api';
import { BookmarkIcon, DownloadIcon, FilterIcon, RefreshIcon } from '../components/common/Icons';
import { EventType, EVENT_TYPE_LABELS } from '../constants';
import { Modal } from '../components/common/Modal';

export const Events: React.FC = () => {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState<string>('');
  const [selectedEventType, setSelectedEventType] = useState<string>('');
  const [onlyBookmarked, setOnlyBookmarked] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState(true);

  // Video Oynatma Modalı
  const [activeVideoClip, setActiveVideoClip] = useState<{ url: string; title: string } | null>(null);

  const fetchEvents = async () => {
    setIsLoading(true);
    try {
      const params: any = { limit: 100 };
      if (selectedCameraId) params.camera_id = Number(selectedCameraId);
      if (selectedEventType) params.event_type = selectedEventType;
      if (onlyBookmarked) params.is_bookmarked = true;

      const [evRes, camRes] = await Promise.all([
        eventsApi.list(params),
        camerasApi.list(),
      ]);
      setEvents(evRes.data);
      setCameras(camRes.data);
    } catch (err) {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [selectedCameraId, selectedEventType, onlyBookmarked]);

  const handleToggleBookmark = async (ev: EventItem, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const nextState = !ev.is_bookmarked;
      await eventsApi.bookmark(ev.id, { is_bookmarked: nextState });
      setEvents((prev) =>
        prev.map((item) => (item.id === ev.id ? { ...item, is_bookmarked: nextState } : item))
      );
    } catch (err) {
      alert('Yer imi güncellenemedi.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Üst Filtre Çubuğu */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 bg-dark-800 border border-dark-700 rounded-2xl shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Olay Merkezi & Alarmlar</h2>
          <p className="text-xs text-slate-400">
            Algılanan insan, araç, bölge ihlali ve çizgi geçişi kayıtları
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Kamera Filtresi */}
          <select
            value={selectedCameraId}
            onChange={(e) => setSelectedCameraId(e.target.value)}
            className="px-3 py-2 bg-dark-900 border border-dark-700 rounded-xl text-xs text-white focus:outline-none focus:border-brand-500 cursor-pointer"
          >
            <option value="">Tüm Kameralar</option>
            {cameras.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>

          {/* Olay Türü Filtresi */}
          <select
            value={selectedEventType}
            onChange={(e) => setSelectedEventType(e.target.value)}
            className="px-3 py-2 bg-dark-900 border border-dark-700 rounded-xl text-xs text-white focus:outline-none focus:border-brand-500 cursor-pointer"
          >
            <option value="">Tüm Olay Türleri</option>
            {Object.entries(EVENT_TYPE_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v.label}
              </option>
            ))}
          </select>

          {/* Sadece Yer İmliler */}
          <button
            onClick={() => setOnlyBookmarked(!onlyBookmarked)}
            className={`px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer ${
              onlyBookmarked
                ? 'bg-amber-500 text-dark-900 font-bold'
                : 'bg-dark-900 text-slate-400 border border-dark-700 hover:text-white'
            }`}
          >
            <BookmarkIcon className="w-4 h-4" filled={onlyBookmarked} />
            Yıldızlılar
          </button>

          {/* Yenile Butonu */}
          <button
            onClick={fetchEvents}
            className="p-2 rounded-xl bg-dark-900 hover:bg-dark-700 border border-dark-700 text-slate-300 transition-colors cursor-pointer"
            title="Yenile"
          >
            <RefreshIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Olay Kartları Galerisi */}
      {isLoading ? (
        <div className="p-16 text-center text-slate-400">Olaylar yükleniyor...</div>
      ) : events.length === 0 ? (
        <div className="p-16 text-center text-slate-400 bg-dark-800 border border-dark-700 rounded-2xl space-y-2">
          <p className="text-base font-semibold text-slate-300">Filtrelere uygun olay bulunamadı.</p>
          <p className="text-xs text-slate-500">
            Kamera önünde hareket veya insan/araç belirdiğinde olaylar anında burada listelenecektir.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {events.map((ev) => {
            const config = EVENT_TYPE_LABELS[ev.event_type] || {
              label: ev.event_type,
              badgeColor: 'bg-dark-700 text-slate-300',
            };

            return (
              <div
                key={ev.id}
                className="group bg-dark-800 border border-dark-700 hover:border-dark-600 rounded-2xl overflow-hidden shadow-lg transition-all duration-200 flex flex-col"
              >
                {/* Snapshot Önizleme */}
                <div
                  onClick={() => {
                    if (ev.clip_url) {
                      setActiveVideoClip({
                        url: ev.clip_url,
                        title: `${ev.camera_name} - ${config.label}`,
                      });
                    }
                  }}
                  className="relative h-44 bg-black overflow-hidden flex items-center justify-center cursor-pointer"
                >
                  {ev.snapshot_url ? (
                    <img
                      src={ev.snapshot_url}
                      alt="Olay Anı"
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="text-xs text-slate-600">Önizleme Yok</div>
                  )}

                  {/* Video Klip Oynat Rozeti */}
                  {ev.clip_url && (
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <div className="w-12 h-12 rounded-full bg-brand-600/90 text-white flex items-center justify-center shadow-lg transform group-hover:scale-110 transition-transform">
                        <svg className="w-6 h-6 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z" />
                        </svg>
                      </div>
                    </div>
                  )}

                  {/* Güven Skoru */}
                  <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded text-[10px] font-mono bg-black/75 text-slate-300 backdrop-blur-sm">
                    %{Math.round(ev.confidence * 100)} Güven
                  </div>
                </div>

                {/* Kart Gövdesi */}
                <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs font-bold text-white truncate">{ev.camera_name}</span>
                      <button
                        onClick={(e) => handleToggleBookmark(ev, e)}
                        title={ev.is_bookmarked ? 'Yer imini kaldır' : 'Yer imine ekle'}
                        className={`p-1 rounded transition-colors cursor-pointer ${
                          ev.is_bookmarked
                            ? 'text-amber-400 hover:text-amber-300'
                            : 'text-slate-500 hover:text-slate-300'
                        }`}
                      >
                        <BookmarkIcon className="w-4 h-4" filled={ev.is_bookmarked} />
                      </button>
                    </div>

                    <span className={`inline-block px-2.5 py-0.5 rounded-md text-[11px] font-semibold border ${config.badgeColor}`}>
                      {config.label}
                    </span>
                  </div>

                  {/* Tarih ve Butonlar */}
                  <div className="pt-2 border-t border-dark-700/60 flex items-center justify-between text-xs">
                    <span className="text-[11px] text-slate-400">
                      {new Date(ev.created_at).toLocaleString('tr-TR')}
                    </span>

                    {ev.clip_url && (
                      <a
                        href={ev.clip_url}
                        download
                        onClick={(e) => e.stopPropagation()}
                        title="Video Klibi İndir"
                        className="p-1.5 rounded-lg bg-dark-700 hover:bg-dark-600 text-slate-300 hover:text-white transition-colors cursor-pointer"
                      >
                        <DownloadIcon className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Video Oynatıcı Modalı */}
      {activeVideoClip && (
        <Modal
          isOpen={Boolean(activeVideoClip)}
          onClose={() => setActiveVideoClip(null)}
          title={activeVideoClip.title}
          maxWidth="max-w-3xl"
        >
          <div className="space-y-4">
            <div className="aspect-video bg-black rounded-xl overflow-hidden border border-dark-700">
              <video
                src={activeVideoClip.url}
                controls
                autoPlay
                className="w-full h-full object-contain"
              />
            </div>
            <div className="flex justify-between items-center text-xs text-slate-400">
              <span>Olay öncesi 5 sn ve olay sonrası kesit tamponu dahil edilmiştir.</span>
              <a
                href={activeVideoClip.url}
                download
                className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-xl font-semibold flex items-center gap-1.5 cursor-pointer"
              >
                <DownloadIcon className="w-4 h-4" />
                MP4 İndir
              </a>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
