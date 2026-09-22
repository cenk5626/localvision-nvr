import React, { useRef, useState, useEffect } from 'react';
import { Modal } from '../common/Modal';
import { Camera } from '../../types';
import { camerasApi } from '../../services/api';

interface ZoneEditorProps {
  isOpen: boolean;
  onClose: () => void;
  camera: Camera | null;
  onSaved: () => void;
}

export const ZoneEditor: React.FC<ZoneEditorProps> = ({
  isOpen,
  onClose,
  camera,
  onSaved,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [zones, setZones] = useState<Array<{ name: string; points: number[][] }>>([]);
  const [tripwires, setTripwires] = useState<Array<{ name: string; line: number[][] }>>([]);
  const [currentPoints, setCurrentPoints] = useState<number[][]>([]);
  const [zoneName, setZoneName] = useState('Yasak Bölge');
  const [mode, setMode] = useState<'polygon' | 'tripwire'>('polygon');
  const [bgImage, setBgImage] = useState<HTMLImageElement | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (camera && isOpen) {
      setZones(camera.roi_polygons || []);
      setTripwires(camera.tripwires || []);
      setCurrentPoints([]);

      // Kameranın anlık görüntüsünü tuval arkasına yükle
      const img = new Image();
      img.src = `/api/cameras/${camera.id}/snapshot?t=${Date.now()}`;
      img.onload = () => setBgImage(img);
    }
  }, [camera, isOpen]);

  // Tuvali yeniden çiz
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Temizle
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Arka plan resmini çiz
    if (bgImage) {
      ctx.drawImage(bgImage, 0, 0, canvas.width, canvas.height);
    } else {
      ctx.fillStyle = '#111827';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    // Mevcut kayıtlı çokgenleri çiz (Mavi/Cyan)
    zones.forEach((zone) => {
      if (zone.points.length < 3) return;
      ctx.beginPath();
      ctx.moveTo(zone.points[0][0], zone.points[0][1]);
      for (let i = 1; i < zone.points.length; i++) {
        ctx.lineTo(zone.points[i][0], zone.points[i][1]);
      }
      ctx.closePath();
      ctx.fillStyle = 'rgba(6, 182, 212, 0.25)';
      ctx.fill();
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 2;
      ctx.stroke();

      // İsim etiketi
      ctx.fillStyle = '#ffffff';
      ctx.font = '12px sans-serif';
      ctx.fillText(zone.name, zone.points[0][0], zone.points[0][1] - 6);
    });

    // Kayıtlı çizgileri çiz (Turuncu/Kırmızı)
    tripwires.forEach((tw) => {
      if (tw.line.length === 2) {
        ctx.beginPath();
        ctx.moveTo(tw.line[0][0], tw.line[0][1]);
        ctx.lineTo(tw.line[1][0], tw.line[1][1]);
        ctx.strokeStyle = '#f43f5e';
        ctx.lineWidth = 3;
        ctx.stroke();

        ctx.fillStyle = '#f43f5e';
        ctx.font = '12px sans-serif';
        ctx.fillText(tw.name, tw.line[0][0], tw.line[0][1] - 6);
      }
    });

    // Şu an çizilmekte olan noktaları ve çizgileri çiz
    if (currentPoints.length > 0) {
      ctx.beginPath();
      ctx.moveTo(currentPoints[0][0], currentPoints[0][1]);
      for (let i = 1; i < currentPoints.length; i++) {
        ctx.lineTo(currentPoints[i][0], currentPoints[i][1]);
      }
      ctx.strokeStyle = mode === 'polygon' ? '#eab308' : '#f97316';
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Noktaları işaretle
      currentPoints.forEach(([x, y]) => {
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#eab308';
        ctx.fill();
      });
    }
  }, [bgImage, zones, tripwires, currentPoints, mode]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = Math.round((e.clientX - rect.left) * (canvas.width / rect.width));
    const y = Math.round((e.clientY - rect.top) * (canvas.height / rect.height));

    const newPts = [...currentPoints, [x, y]];

    if (mode === 'tripwire' && newPts.length === 2) {
      // Çizgi tamamlandı
      setTripwires([...tripwires, { name: zoneName, line: newPts }]);
      setCurrentPoints([]);
    } else {
      setCurrentPoints(newPts);
    }
  };

  const handleFinishPolygon = () => {
    if (currentPoints.length >= 3) {
      setZones([...zones, { name: zoneName, points: currentPoints }]);
      setCurrentPoints([]);
    } else {
      alert('Bir bölge oluşturmak için en az 3 nokta eklemelisiniz.');
    }
  };

  const handleSave = async () => {
    if (!camera) return;
    setIsSaving(true);
    try {
      await camerasApi.update(camera.id, {
        roi_polygons: zones,
        tripwires: tripwires,
      });
      onSaved();
      onClose();
    } catch (err) {
      alert('Bölgeler kaydedilemedi.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Algılama Bölgeleri ve Çizgileri: ${camera?.name}`}
      maxWidth="max-w-4xl"
    >
      <div className="space-y-4">
        {/* Çizim Araç Çubuğu */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-dark-900 rounded-xl border border-dark-700">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                setMode('polygon');
                setCurrentPoints([]);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer ${
                mode === 'polygon' ? 'bg-cyan-600 text-white' : 'bg-dark-800 text-slate-400 hover:text-white'
              }`}
            >
              ⬟ Çokgen Bölge (ROI)
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('tripwire');
                setCurrentPoints([]);
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold cursor-pointer ${
                mode === 'tripwire' ? 'bg-rose-600 text-white' : 'bg-dark-800 text-slate-400 hover:text-white'
              }`}
            >
              ─ Sanal Çizgi (Tripwire)
            </button>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="text"
              value={zoneName}
              onChange={(e) => setZoneName(e.target.value)}
              placeholder="Bölge veya Çizgi Adı"
              className="px-3 py-1.5 bg-dark-800 border border-dark-700 rounded-lg text-xs text-white"
            />
            {mode === 'polygon' && (
              <button
                type="button"
                onClick={handleFinishPolygon}
                disabled={currentPoints.length < 3}
                className="px-3 py-1.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-40 text-white rounded-lg text-xs font-medium cursor-pointer"
              >
                Bölgeyi Kapat
              </button>
            )}
            <button
              type="button"
              onClick={() => setCurrentPoints([])}
              className="px-2.5 py-1.5 bg-dark-800 hover:bg-dark-700 text-slate-400 rounded-lg text-xs cursor-pointer"
            >
              İptal
            </button>
          </div>
        </div>

        {/* İnteraktif Çizim Tuvali */}
        <div className="relative border border-dark-700 rounded-xl overflow-hidden bg-black flex justify-center">
          <canvas
            ref={canvasRef}
            width={640}
            height={360}
            onClick={handleCanvasClick}
            className="cursor-crosshair max-w-full h-auto"
          />
        </div>

        {/* Tanımlı Liste & Temizle */}
        <div className="flex items-center justify-between text-xs text-slate-400 px-1">
          <div>
            Kayıtlı: <span className="text-cyan-400 font-semibold">{zones.length} Bölge</span>,{' '}
            <span className="text-rose-400 font-semibold">{tripwires.length} Çizgi</span>
          </div>
          <div className="space-x-2">
            <button
              onClick={() => {
                setZones([]);
                setTripwires([]);
              }}
              className="text-rose-400 hover:underline cursor-pointer"
            >
              Tümünü Temizle
            </button>
          </div>
        </div>

        {/* Kaydet & Kapat */}
        <div className="flex justify-end gap-3 pt-3 border-t border-dark-700">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white hover:bg-dark-700"
          >
            Vazgeç
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            className="px-5 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg cursor-pointer"
          >
            {isSaving ? 'Kaydediliyor...' : 'Bölgeleri Kaydet'}
          </button>
        </div>
      </div>
    </Modal>
  );
};
