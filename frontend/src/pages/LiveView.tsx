import React, { useEffect, useState } from 'react';
import { Camera } from '../types';
import { camerasApi } from '../services/api';
import { CameraTile } from '../components/live/CameraTile';
import { GridMode } from '../constants';
import { ZoneEditor } from '../components/cameras/ZoneEditor';

export const LiveView: React.FC = () => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [gridMode, setGridMode] = useState<GridMode>(GridMode.GRID_2X2);
  const [selectedCameraId, setSelectedCameraId] = useState<number | null>(null);
  const [zoneModalCamera, setZoneModalCamera] = useState<Camera | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchCameras = async () => {
    try {
      const res = await camerasApi.list();
      setCameras(res.data);
      if (res.data.length > 0 && selectedCameraId === null) {
        setSelectedCameraId(res.data[0].id);
      }
    } catch (err) {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
    const interval = setInterval(fetchCameras, 10000);
    return () => clearInterval(interval);
  }, []);

  // Grid CSS sınıfları
  const getGridClasses = () => {
    switch (gridMode) {
      case GridMode.SINGLE:
        return 'grid-cols-1';
      case GridMode.GRID_2X2:
        return 'grid-cols-1 md:grid-cols-2';
      case GridMode.GRID_3X3:
        return 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3';
      case GridMode.GRID_4X4:
        return 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4';
      default:
        return 'grid-cols-1 md:grid-cols-2';
    }
  };

  const displayedCameras =
    gridMode === GridMode.SINGLE && selectedCameraId
      ? cameras.filter((c) => c.id === selectedCameraId)
      : cameras;

  return (
    <div className="space-y-4">
      {/* Kontrol Çubuğu */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-dark-800 border border-dark-700 rounded-2xl">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">Çoklu Kamera Canlı İzleme</h2>
          <p className="text-xs text-slate-400">
            Düşük gecikmeli MJPEG akışı ile sıfır eklentiyle canlı görüntüleme
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Tekli Görünüm Seçili Kamera Seçici */}
          {gridMode === GridMode.SINGLE && cameras.length > 1 && (
            <select
              value={selectedCameraId || ''}
              onChange={(e) => setSelectedCameraId(Number(e.target.value))}
              className="px-3 py-1.5 bg-dark-900 border border-dark-700 rounded-xl text-xs text-white focus:outline-none focus:border-brand-500 cursor-pointer"
            >
              {cameras.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          )}

          {/* Izgara Düzeni Değiştirici */}
          <div className="flex items-center p-1 bg-dark-900 border border-dark-700 rounded-xl space-x-1">
            {[
              { id: GridMode.SINGLE, label: '1x1' },
              { id: GridMode.GRID_2X2, label: '2x2' },
              { id: GridMode.GRID_3X3, label: '3x3' },
              { id: GridMode.GRID_4X4, label: '4x4' },
            ].map((mode) => (
              <button
                key={mode.id}
                onClick={() => setGridMode(mode.id)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                  gridMode === mode.id
                    ? 'bg-brand-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {mode.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Kameralar Izgarası */}
      {displayedCameras.length === 0 ? (
        <div className="p-16 text-center text-slate-400 bg-dark-800 border border-dark-700 rounded-2xl space-y-3">
          <p className="text-base font-semibold text-slate-300">İzlenecek kamera bulunamadı.</p>
          <p className="text-xs text-slate-500">
            Kameralar sekmesine giderek bir RTSP kamera ekleyebilir veya bilgisayarınızın web kamerasını açabilirsiniz.
          </p>
        </div>
      ) : (
        <div className={`grid gap-4 ${getGridClasses()}`}>
          {displayedCameras.map((cam) => (
            <div
              key={cam.id}
              className={gridMode === GridMode.SINGLE ? 'h-[75vh]' : 'h-[320px]'}
            >
              <CameraTile
                camera={cam}
                onOpenZoneEditor={() => setZoneModalCamera(cam)}
              />
            </div>
          ))}
        </div>
      )}

      {/* Çokgen/Çizgi Bölge Düzenleyici Modalı */}
      <ZoneEditor
        isOpen={Boolean(zoneModalCamera)}
        camera={zoneModalCamera}
        onClose={() => setZoneModalCamera(null)}
        onSaved={fetchCameras}
      />
    </div>
  );
};
