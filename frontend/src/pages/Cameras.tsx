import React, { useEffect, useState } from 'react';
import { Camera } from '../types';
import { camerasApi } from '../services/api';
import { CameraModal } from '../components/cameras/CameraModal';
import { ZoneEditor } from '../components/cameras/ZoneEditor';
import { PlusIcon, RefreshIcon, TrashIcon } from '../components/common/Icons';
import { StatusBadge } from '../components/common/StatusBadge';
import { RECORDING_MODE_LABELS, SOURCE_TYPE_LABELS } from '../constants';

export const Cameras: React.FC = () => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [cameraToEdit, setCameraToEdit] = useState<Camera | null>(null);
  const [zoneCamera, setZoneCamera] = useState<Camera | null>(null);

  const fetchCameras = async () => {
    setIsLoading(true);
    try {
      const res = await camerasApi.list();
      setCameras(res.data);
    } catch (e) {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
  }, []);

  const handleDeleteCamera = async (cam: Camera) => {
    if (confirm(`"${cam.name}" kamerasını ve tüm kayıt bağlantılarını silmek istediğinize emin misiniz?`)) {
      try {
        await camerasApi.delete(cam.id);
        fetchCameras();
      } catch (err) {
        alert('Kamera silinemedi.');
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Üst Başlık & Aksiyonlar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 bg-dark-800 border border-dark-700 rounded-2xl shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Kamera Yönetimi</h2>
          <p className="text-xs text-slate-400">
            RTSP akışları, ONVIF cihazları ve yerel PC web kameralarını yapılandırın
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchCameras}
            className="p-2.5 rounded-xl bg-dark-900 hover:bg-dark-700 border border-dark-700 text-slate-300 transition-colors cursor-pointer"
            title="Yenile"
          >
            <RefreshIcon className="w-4 h-4" />
          </button>

          <button
            onClick={() => {
              setCameraToEdit(null);
              setIsModalOpen(true);
            }}
            className="px-4 py-2.5 bg-brand-600 hover:bg-brand-500 text-white rounded-xl text-xs font-semibold flex items-center gap-2 shadow-lg shadow-brand-600/30 transition-colors cursor-pointer"
          >
            <PlusIcon className="w-4 h-4" />
            Yeni Kamera Ekle
          </button>
        </div>
      </div>

      {/* Bulut Kamera Uyarısı (Prompt Zorunluluğu) */}
      <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3 text-xs text-amber-300">
        <span className="text-base leading-none">⚠️</span>
        <div>
          <span className="font-semibold text-white">Önemli Donanım Uyarısı: </span>
          RTSP ve ONVIF protokollerini desteklemeyen, yalnızca üreticinin kapalı bulut uygulaması (cloud app) üzerinden çalışan kameraların sistemle doğrudan yerel uyumluluğu garanti edilemez. Gizlilik ve kesintisiz yerel ağ çalışması için standart RTSP/ONVIF Profile S/T destekli kameralar önerilir.
        </div>
      </div>

      {/* Kamera Kartları */}
      {isLoading ? (
        <div className="p-16 text-center text-slate-400">Kameralar yükleniyor...</div>
      ) : cameras.length === 0 ? (
        <div className="p-16 text-center text-slate-400 bg-dark-800 border border-dark-700 rounded-2xl space-y-3">
          <p className="text-base font-semibold text-slate-300">Henüz kamera eklenmedi.</p>
          <p className="text-xs text-slate-500">
            Bilgisayarınızın web kamerasını tek tıkla test etmek veya ağdaki bir IP kamerayı eklemek için yukarıdaki butona tıklayın.
          </p>
          <button
            onClick={() => {
              setCameraToEdit(null);
              setIsModalOpen(true);
            }}
            className="px-4 py-2 bg-brand-600 text-white text-xs font-semibold rounded-xl cursor-pointer"
          >
            + Şimdi Kamera Ekle
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {cameras.map((cam) => (
            <div
              key={cam.id}
              className="bg-dark-800 border border-dark-700 hover:border-dark-600 rounded-2xl p-5 shadow-lg space-y-4 transition-all flex flex-col justify-between"
            >
              <div className="space-y-3">
                {/* Üst Başlık & Durum */}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-bold text-white truncate">{cam.name}</h3>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {SOURCE_TYPE_LABELS[cam.source_type] || cam.source_type}
                    </p>
                  </div>
                  <StatusBadge status={cam.status} />
                </div>

                {/* Parametre Tablosu */}
                <div className="p-3 bg-dark-900/60 rounded-xl border border-dark-700/60 space-y-1.5 text-xs text-slate-300">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Kayıt Modu:</span>
                    <span className="font-medium text-white truncate max-w-[160px]">
                      {RECORDING_MODE_LABELS[cam.recording_mode] || cam.recording_mode}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Çözünürlük:</span>
                    <span className="font-mono text-slate-300">{cam.width}x{cam.height}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Kare Hızı (FPS):</span>
                    <span className="font-mono text-emerald-400">{cam.actual_fps || cam.fps} FPS</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Algılama Bölgeleri:</span>
                    <span className="font-medium text-cyan-400">
                      {(cam.roi_polygons?.length || 0)} Bölge, {(cam.tripwires?.length || 0)} Çizgi
                    </span>
                  </div>
                </div>
              </div>

              {/* Aksiyon Butonları */}
              <div className="pt-3 border-t border-dark-700/60 flex items-center justify-between gap-2">
                <button
                  onClick={() => setZoneCamera(cam)}
                  className="px-3 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30 text-xs font-semibold transition-colors cursor-pointer"
                >
                  ⬟ Bölgeleri Çiz
                </button>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      setCameraToEdit(cam);
                      setIsModalOpen(true);
                    }}
                    className="px-3 py-1.5 rounded-lg bg-dark-700 hover:bg-dark-600 text-slate-200 text-xs font-medium transition-colors cursor-pointer"
                  >
                    Düzenle
                  </button>
                  <button
                    onClick={() => handleDeleteCamera(cam)}
                    className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 transition-colors cursor-pointer"
                    title="Kamerayı Sil"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Kamera Ekleme / Düzenleme Modalı */}
      <CameraModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={fetchCameras}
        cameraToEdit={cameraToEdit}
      />

      {/* Bölge Çizim Modalı */}
      <ZoneEditor
        isOpen={Boolean(zoneCamera)}
        camera={zoneCamera}
        onClose={() => setZoneCamera(null)}
        onSaved={fetchCameras}
      />
    </div>
  );
};
