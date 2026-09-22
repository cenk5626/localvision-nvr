import React, { useEffect, useState } from 'react';
import { Camera, RecordingItem } from '../types';
import { camerasApi, recordingsApi } from '../services/api';
import { BookmarkIcon, DownloadIcon, PlayIcon, RefreshIcon } from '../components/common/Icons';
import { Modal } from '../components/common/Modal';

export const Playback: React.FC = () => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedCameraId, setSelectedCameraId] = useState<number | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [recordings, setRecordings] = useState<RecordingItem[]>([]);
  const [selectedRecording, setSelectedRecording] = useState<RecordingItem | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Dışa aktarma modalı
  const [exportModalRec, setExportModalRec] = useState<RecordingItem | null>(null);
  const [addWatermark, setAddWatermark] = useState(true);
  const [exportNotes, setExportNotes] = useState('');
  const [isExporting, setIsExporting] = useState(false);
  const [exportResult, setExportResult] = useState<any | null>(null);

  useEffect(() => {
    const fetchCameras = async () => {
      try {
        const res = await camerasApi.list();
        setCameras(res.data);
        if (res.data.length > 0 && selectedCameraId === null) {
          setSelectedCameraId(res.data[0].id);
        }
      } catch (e) {
        // ignore
      }
    };
    fetchCameras();
  }, []);

  const fetchRecordings = async () => {
    if (!selectedCameraId) return;
    setIsLoading(true);
    try {
      const res = await recordingsApi.list({
        camera_id: selectedCameraId,
        date: selectedDate,
      });
      setRecordings(res.data);
      if (res.data.length > 0) {
        setSelectedRecording(res.data[0]);
      } else {
        setSelectedRecording(null);
      }
    } catch (e) {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRecordings();
  }, [selectedCameraId, selectedDate]);

  const handleToggleBookmark = async (rec: RecordingItem) => {
    try {
      const nextProtected = !rec.is_protected;
      await recordingsApi.bookmark(rec.id, {
        is_protected: nextProtected,
        is_bookmarked: nextProtected,
      });
      setRecordings((prev) =>
        prev.map((r) =>
          r.id === rec.id ? { ...r, is_protected: nextProtected, is_bookmarked: nextProtected } : r
        )
      );
      if (selectedRecording?.id === rec.id) {
        setSelectedRecording({ ...selectedRecording, is_protected: nextProtected, is_bookmarked: nextProtected });
      }
    } catch (err) {
      alert('Yer imi güncellenemedi.');
    }
  };

  const handleExport = async () => {
    if (!exportModalRec) return;
    setIsExporting(true);
    setExportResult(null);
    try {
      const res = await recordingsApi.export(exportModalRec.id, {
        add_watermark: addWatermark,
        notes: exportNotes,
      });
      setExportResult(res.data.details);
    } catch (err) {
      alert('Dışa aktarma hatası oluştu.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Üst Filtre Çubuğu */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 bg-dark-800 border border-dark-700 rounded-2xl shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Geçmiş Kayıt ve Zaman Çizelgesi</h2>
          <p className="text-xs text-slate-400">
            Segmentli MP4 kayıtlarını oynatın, zaman çizelgesinde arayın ve delil doğrulama özeti ile dışa aktarın
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Kamera Seçimi */}
          <select
            value={selectedCameraId || ''}
            onChange={(e) => setSelectedCameraId(Number(e.target.value))}
            className="px-3 py-2 bg-dark-900 border border-dark-700 rounded-xl text-xs text-white focus:outline-none focus:border-brand-500 cursor-pointer"
          >
            {cameras.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>

          {/* Tarih Seçimi */}
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-3 py-2 bg-dark-900 border border-dark-700 rounded-xl text-xs text-white focus:outline-none focus:border-brand-500 cursor-pointer"
          />

          <button
            onClick={fetchRecordings}
            className="p-2 rounded-xl bg-dark-900 hover:bg-dark-700 border border-dark-700 text-slate-300 transition-colors cursor-pointer"
            title="Yenile"
          >
            <RefreshIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Video Oynatıcı & Kontroller */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sol 2 Sütun: Video Ekranı */}
        <div className="lg:col-span-2 bg-dark-800 border border-dark-700 rounded-2xl p-5 space-y-4 shadow-xl">
          <div className="aspect-video bg-black rounded-xl overflow-hidden border border-dark-700 relative flex items-center justify-center">
            {selectedRecording ? (
              <video
                key={selectedRecording.id}
                src={selectedRecording.stream_url}
                controls
                autoPlay
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="text-center p-8 text-slate-500 text-xs">
                {isLoading ? 'Kayıtlar taranıyor...' : 'Seçili tarihe ait video segmenti bulunamadı.'}
              </div>
            )}
          </div>

          {/* Seçili Segment Detayları & Eylemler */}
          {selectedRecording && (
            <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-dark-900/60 border border-dark-700 rounded-xl text-xs">
              <div>
                <span className="font-semibold text-white">{selectedRecording.file_name}</span>
                <div className="text-slate-400 text-[11px] mt-0.5">
                  Boyut: {selectedRecording.file_size_mb} MB | Başlangıç:{' '}
                  {new Date(selectedRecording.start_time).toLocaleTimeString('tr-TR')}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleToggleBookmark(selectedRecording)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${
                    selectedRecording.is_protected
                      ? 'bg-amber-500 text-dark-900 font-bold'
                      : 'bg-dark-800 text-slate-300 hover:text-white border border-dark-700'
                  }`}
                >
                  <BookmarkIcon className="w-3.5 h-3.5" filled={selectedRecording.is_protected} />
                  {selectedRecording.is_protected ? 'Korumalı' : 'Koru / Yıldızla'}
                </button>

                <button
                  onClick={() => setExportModalRec(selectedRecording)}
                  className="px-3.5 py-1.5 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow cursor-pointer"
                >
                  <DownloadIcon className="w-3.5 h-3.5" />
                  Dışa Aktar
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Sağ 1 Sütun: Segment Listesi (Zaman Çizelgesi) */}
        <div className="bg-dark-800 border border-dark-700 rounded-2xl p-5 space-y-3 shadow-xl flex flex-col">
          <h3 className="text-sm font-semibold text-white">
            Kayıt Segmentleri ({recordings.length})
          </h3>
          <p className="text-[11px] text-slate-400">
            Mavi: Sürekli kayıt | Mor: AI Olaylı | Sarı: Korumalı
          </p>

          <div className="flex-1 overflow-y-auto space-y-2 max-h-[480px]">
            {recordings.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">
                Seçilen günde kayıt bulunmuyor.
              </div>
            ) : (
              recordings.map((rec) => {
                const isSelected = selectedRecording?.id === rec.id;
                let borderColor = 'border-dark-700';
                if (rec.is_protected) borderColor = 'border-amber-500/50 bg-amber-500/5';
                else if (rec.has_ai_event) borderColor = 'border-purple-500/40 bg-purple-500/5';
                else borderColor = 'border-dark-700 bg-dark-900/60';

                return (
                  <div
                    key={rec.id}
                    onClick={() => setSelectedRecording(rec)}
                    className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${borderColor} ${
                      isSelected ? 'ring-2 ring-brand-500' : 'hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-center justify-between font-semibold text-white">
                      <span>{new Date(rec.start_time).toLocaleTimeString('tr-TR')}</span>
                      <span className="text-[10px] text-slate-400 font-mono">{rec.file_size_mb} MB</span>
                    </div>
                    <div className="flex items-center justify-between mt-1 text-[11px] text-slate-400">
                      <span>Süre: {Math.round(rec.duration_seconds)} sn</span>
                      {rec.is_protected && <span className="text-amber-400 font-semibold">★ Korumalı</span>}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Dışa Aktarma Modalı */}
      {exportModalRec && (
        <Modal
          isOpen={Boolean(exportModalRec)}
          onClose={() => {
            setExportModalRec(null);
            setExportResult(null);
          }}
          title="Videoyu Dışa Aktar (Delil Doğrulama Özeti İle)"
          maxWidth="max-w-lg"
        >
          <div className="space-y-4 text-xs">
            <p className="text-slate-300">
              Bu kayıt bağımsız bir MP4 olarak kaydedilecek ve adli doğrulama için SHA-256 bütünlük özeti üretilecektir.
            </p>

            <label className="flex items-center gap-2 p-3 bg-dark-900 rounded-xl border border-dark-700 cursor-pointer">
              <input
                type="checkbox"
                checked={addWatermark}
                onChange={(e) => setAddWatermark(e.target.checked)}
                className="rounded border-dark-600 text-brand-600 focus:ring-0"
              />
              <span className="text-slate-200 font-medium">
                Zaman Damgası ve Kamera Adı Filigranı Ekle
              </span>
            </label>

            <div>
              <label className="block text-slate-300 font-semibold mb-1">Dışa Aktarma Notu</label>
              <textarea
                value={exportNotes}
                onChange={(e) => setExportNotes(e.target.value)}
                placeholder="örn: 14 Eylül Güvenlik İncelemesi"
                rows={2}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-xl text-white focus:outline-none focus:border-brand-500"
              />
            </div>

            {/* Dışa Aktarma Sonucu */}
            {exportResult && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl space-y-1 text-emerald-400">
                <div className="font-bold">✓ Dışa Aktarma Tamamlandı</div>
                <div className="font-mono text-[10px] break-all">
                  SHA-256: {exportResult.sha256}
                </div>
                <div className="text-[11px] text-slate-400">
                  Dosya Adı: {exportResult.filename}
                </div>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-3 border-t border-dark-700">
              <button
                type="button"
                onClick={() => {
                  setExportModalRec(null);
                  setExportResult(null);
                }}
                className="px-4 py-2 rounded-xl text-slate-400 hover:text-white"
              >
                Kapat
              </button>
              <button
                type="button"
                onClick={handleExport}
                disabled={isExporting}
                className="px-5 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-xl font-semibold shadow cursor-pointer"
              >
                {isExporting ? 'Aktarılıyor...' : 'Dışa Aktarmayı Başlat'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
