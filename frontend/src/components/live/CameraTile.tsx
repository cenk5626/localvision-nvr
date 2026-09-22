import React, { useState } from 'react';
import { Camera } from '../../types';
import { StatusBadge } from '../common/StatusBadge';
import { CameraStatus } from '../../constants';

interface CameraTileProps {
  camera: Camera;
  onSelect?: () => void;
  onOpenZoneEditor?: () => void;
}

export const CameraTile: React.FC<CameraTileProps> = ({
  camera,
  onSelect,
  onOpenZoneEditor,
}) => {
  const [streamError, setStreamError] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const streamUrl = `/api/cameras/${camera.id}/live.mjpeg`;

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  return (
    <div
      className={`group relative bg-dark-800 rounded-2xl border border-dark-700 overflow-hidden flex flex-col shadow-lg transition-all duration-200 ${
        isFullscreen ? 'fixed inset-4 z-50 bg-dark-900 border-dark-600' : 'h-full'
      }`}
    >
      {/* Üst Bilgi Çubuğu */}
      <div className="absolute top-0 inset-x-0 p-3 bg-gradient-to-b from-black/80 via-black/40 to-transparent z-10 flex items-center justify-between pointer-events-auto">
        <div className="flex items-center gap-2">
          <StatusBadge status={camera.status} />
          <span className="text-xs font-semibold text-white truncate drop-shadow-md">
            {camera.name}
          </span>
        </div>

        <div className="flex items-center gap-1.5 opacity-90 group-hover:opacity-100 transition-opacity">
          {camera.status === CameraStatus.ONLINE && (
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-black/60 text-slate-300 backdrop-blur-sm border border-white/10">
              {camera.actual_fps || camera.fps} FPS
            </span>
          )}
          <button
            onClick={toggleFullscreen}
            title={isFullscreen ? 'Küçült' : 'Tam Ekran'}
            className="p-1 rounded-lg bg-black/60 hover:bg-black/80 text-white backdrop-blur-sm transition-colors cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {isFullscreen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Video / Akış Alanı */}
      <div className="relative flex-1 bg-black flex items-center justify-center min-h-[220px]">
        {camera.status === CameraStatus.ONLINE && !streamError ? (
          <img
            src={streamUrl}
            alt={camera.name}
            onError={() => setStreamError(true)}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="flex flex-col items-center justify-center p-6 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-dark-700/60 flex items-center justify-center text-slate-500">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-300">
                {camera.status === CameraStatus.CONNECTING
                  ? 'Kamera Akışına Bağlanılıyor...'
                  : 'Kamera Çevrimdışı'}
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {camera.source_type === 'webcam'
                  ? `Webcam İndeksi: ${camera.webcam_index}`
                  : camera.rtsp_url || 'Bağlantı adresi bekleniyor'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Alt Kontrol / Bilgi Şeridi */}
      <div className="px-3 py-2 bg-dark-800 border-t border-dark-700/60 flex items-center justify-between text-xs text-slate-400">
        <span className="text-[11px] truncate">
          Çözünürlük: {camera.width}x{camera.height}
        </span>
        {onOpenZoneEditor && (
          <button
            onClick={onOpenZoneEditor}
            className="text-[11px] text-accent-cyan hover:underline font-medium cursor-pointer"
          >
            Bölgeleri Çiz
          </button>
        )}
      </div>
    </div>
  );
};
