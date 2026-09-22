import React, { useState, useEffect } from 'react';
import { Modal } from '../common/Modal';
import { Camera } from '../../types';
import { CameraSourceType, RecordingMode, RECORDING_MODE_LABELS, SOURCE_TYPE_LABELS } from '../../constants';
import { camerasApi } from '../../services/api';

interface CameraModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  cameraToEdit?: Camera | null;
}

export const CameraModal: React.FC<CameraModalProps> = ({
  isOpen,
  onClose,
  onSave,
  cameraToEdit,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [sourceType, setSourceType] = useState<CameraSourceType>(CameraSourceType.WEBCAM);
  const [rtspUrl, setRtspUrl] = useState('');
  const [webcamIndex, setWebcamIndex] = useState(0);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fps, setFps] = useState(20);
  const [recordingMode, setRecordingMode] = useState<RecordingMode>(RecordingMode.CONTINUOUS);
  const [retentionDays, setRetentionDays] = useState(14);
  const [detectionEnabled, setDetectionEnabled] = useState(true);
  const [detectionFps, setDetectionFps] = useState(5);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.45);

  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoveredWebcams, setDiscoveredWebcams] = useState<any[]>([]);
  const [discoveredOnvif, setDiscoveredOnvif] = useState<any[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (cameraToEdit) {
      setName(cameraToEdit.name);
      setDescription(cameraToEdit.description || '');
      setSourceType(cameraToEdit.source_type);
      setRtspUrl(cameraToEdit.rtsp_url || '');
      setWebcamIndex(cameraToEdit.webcam_index || 0);
      setFps(cameraToEdit.fps || 20);
      setRecordingMode(cameraToEdit.recording_mode || RecordingMode.CONTINUOUS);
      setDetectionEnabled(cameraToEdit.detection_enabled);
    } else {
      setName('Yeni Kamera');
      setDescription('');
      setSourceType(CameraSourceType.WEBCAM);
      setRtspUrl('');
      setWebcamIndex(0);
      setFps(20);
      setRecordingMode(RecordingMode.CONTINUOUS);
      setDetectionEnabled(true);
    }
    setTestResult(null);
  }, [cameraToEdit, isOpen]);

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await camerasApi.testConnection({
        source_type: sourceType,
        rtsp_url: rtspUrl,
        webcam_index: webcamIndex,
        username,
        password,
      });
      if (res.data.success) {
        setTestResult({ success: true, message: res.data.message });
      } else {
        setTestResult({ success: false, message: res.data.error || 'Bağlantı kurulamadı.' });
      }
    } catch (err: any) {
      setTestResult({ success: false, message: err.response?.data?.detail || 'Test başarısız oldu.' });
    } finally {
      setIsTesting(false);
    }
  };

  const handleDiscoverWebcams = async () => {
    setIsDiscovering(true);
    try {
      const res = await camerasApi.discoverWebcams();
      setDiscoveredWebcams(res.data.webcams || []);
      if (res.data.webcams.length > 0) {
        setSourceType(CameraSourceType.WEBCAM);
        setWebcamIndex(res.data.webcams[0].index);
        setName(res.data.webcams[0].name);
      }
    } catch (e) {
      // ignore
    } finally {
      setIsDiscovering(false);
    }
  };

  const handleDiscoverOnvif = async () => {
    setIsDiscovering(true);
    try {
      const res = await camerasApi.discoverOnvif();
      setDiscoveredOnvif(res.data.cameras || []);
    } catch (e) {
      // ignore
    } finally {
      setIsDiscovering(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payload: any = {
        name,
        description,
        source_type: sourceType,
        rtsp_url: sourceType === CameraSourceType.RTSP ? rtspUrl : null,
        webcam_index: sourceType === CameraSourceType.WEBCAM ? Number(webcamIndex) : 0,
        username: username || null,
        password: password || null,
        fps: Number(fps),
        recording_mode: recordingMode,
        retention_days: Number(retentionDays),
        detection_enabled: detectionEnabled,
        detection_fps: Number(detectionFps),
        confidence_threshold: Number(confidenceThreshold),
      };

      if (cameraToEdit) {
        await camerasApi.update(cameraToEdit.id, payload);
      } else {
        await camerasApi.create(payload);
      }
      onSave();
      onClose();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Kaydetme hatası');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={cameraToEdit ? `Kamerayı Düzenle: ${cameraToEdit.name}` : 'Yeni Kamera Ekle'}
      maxWidth="max-w-2xl"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Hızlı Keşif Butonları */}
        {!cameraToEdit && (
          <div className="p-3 bg-dark-900/70 border border-dark-700 rounded-xl space-y-2">
            <span className="text-xs font-semibold text-slate-300">Otomatik Donanım Keşfi:</span>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleDiscoverWebcams}
                disabled={isDiscovering}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-brand-600/30 hover:bg-brand-600/50 text-brand-300 border border-brand-500/30 transition-colors cursor-pointer"
              >
                {isDiscovering ? 'Aranıyor...' : '💻 Bilgisayar Kameramı Otomatik Bul'}
              </button>
              <button
                type="button"
                onClick={handleDiscoverOnvif}
                disabled={isDiscovering}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-accent-cyan/20 hover:bg-accent-cyan/30 text-cyan-300 border border-cyan-500/30 transition-colors cursor-pointer"
              >
                🌐 Ağdaki ONVIF Kameraları Tara
              </button>
            </div>

            {/* Keşfedilen Web Kameraları */}
            {discoveredWebcams.length > 0 && (
              <div className="mt-2 space-y-1">
                {discoveredWebcams.map((wc) => (
                  <div
                    key={wc.index}
                    onClick={() => {
                      setSourceType(CameraSourceType.WEBCAM);
                      setWebcamIndex(wc.index);
                      setName(wc.name);
                    }}
                    className="p-2 rounded-lg bg-dark-800 hover:bg-brand-600/20 border border-dark-700 hover:border-brand-500/50 text-xs flex justify-between items-center cursor-pointer"
                  >
                    <span className="font-semibold text-white">{wc.name}</span>
                    <span className="text-slate-400">Çözünürlük: {wc.resolution} (Seçmek için tıkla)</span>
                  </div>
                ))}
              </div>
            )}

            {/* Keşfedilen ONVIF Cihazları */}
            {discoveredOnvif.length > 0 && (
              <div className="mt-2 space-y-1">
                {discoveredOnvif.map((onv, idx) => (
                  <div
                    key={idx}
                    onClick={() => {
                      setSourceType(CameraSourceType.RTSP);
                      setRtspUrl(`rtsp://${onv.ip}:${onv.port}/h264Preview_01_main`);
                      setName(`ONVIF IP Kamera (${onv.ip})`);
                    }}
                    className="p-2 rounded-lg bg-dark-800 hover:bg-cyan-600/20 border border-dark-700 hover:border-cyan-500/50 text-xs flex justify-between items-center cursor-pointer"
                  >
                    <span className="font-semibold text-white">{onv.manufacturer} ({onv.ip})</span>
                    <span className="text-slate-400">{onv.xaddrs}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Temel Bilgiler */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Kamera Adı *</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="örn: Giriş Kapısı veya PC Kameram"
              className="w-full px-3.5 py-2.5 bg-dark-900 border border-dark-700 rounded-xl text-sm text-white focus:outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Kaynak Türü *</label>
            <select
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value as CameraSourceType)}
              className="w-full px-3.5 py-2.5 bg-dark-900 border border-dark-700 rounded-xl text-sm text-white focus:outline-none focus:border-brand-500 cursor-pointer"
            >
              {Object.entries(SOURCE_TYPE_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Kaynak Detayları */}
        {sourceType === CameraSourceType.WEBCAM ? (
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">PC Web Kamerası İndeksi (0 = Birincil Kamera)</label>
            <input
              type="number"
              min={0}
              max={10}
              value={webcamIndex}
              onChange={(e) => setWebcamIndex(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 bg-dark-900 border border-dark-700 rounded-xl text-sm text-white focus:outline-none focus:border-brand-500"
            />
            <p className="text-[11px] text-slate-400 mt-1">Bilgisayarınızın dahili veya USB kamerasını kullanır.</p>
          </div>
        ) : (
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">RTSP Akış URL'si *</label>
              <input
                type="text"
                required={sourceType === CameraSourceType.RTSP}
                value={rtspUrl}
                onChange={(e) => setRtspUrl(e.target.value)}
                placeholder="rtsp://192.168.1.100:554/stream1"
                className="w-full px-3.5 py-2.5 bg-dark-900 border border-dark-700 rounded-xl text-sm text-white focus:outline-none focus:border-brand-500 font-mono"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Kamera Kullanıcı Adı</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin"
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-xl text-sm text-white focus:outline-none focus:border-brand-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Kamera Parolası</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-xl text-sm text-white focus:outline-none focus:border-brand-500"
                />
              </div>
            </div>
            <p className="text-[11px] text-slate-400">
              * Parola veritabanında düz metin tutulmaz; AES-256-GCM ile güvenle şifrelenir.
            </p>
          </div>
        )}

        {/* Bağlantı Test Butonu ve Sonucu */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-dark-900/60 border border-dark-700">
          <div>
            <span className="text-xs font-semibold text-slate-300">Bağlantıyı Doğrula:</span>
            {testResult && (
              <p className={`text-xs mt-0.5 ${testResult.success ? 'text-emerald-400' : 'text-rose-400'}`}>
                {testResult.message}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={isTesting}
            className="px-4 py-2 text-xs font-semibold rounded-xl bg-dark-700 hover:bg-dark-600 text-white transition-colors cursor-pointer"
          >
            {isTesting ? 'Test Ediliyor...' : 'Akışı Test Et'}
          </button>
        </div>

        {/* Kayıt ve Yapay Zeka Ayarları */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-dark-700">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Kayıt Stratejisi</label>
            <select
              value={recordingMode}
              onChange={(e) => setRecordingMode(e.target.value as RecordingMode)}
              className="w-full px-3.5 py-2.5 bg-dark-900 border border-dark-700 rounded-xl text-sm text-white focus:outline-none focus:border-brand-500 cursor-pointer"
            >
              {Object.entries(RECORDING_MODE_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Kayıt Saklama Süresi (Gün)</label>
            <input
              type="number"
              min={1}
              max={365}
              value={retentionDays}
              onChange={(e) => setRetentionDays(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 bg-dark-900 border border-dark-700 rounded-xl text-sm text-white focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>

        {/* Butonlar */}
        <div className="flex justify-end gap-3 pt-4 border-t border-dark-700">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-dark-700 transition-colors cursor-pointer"
          >
            İptal
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-2.5 rounded-xl text-sm font-semibold bg-brand-600 hover:bg-brand-500 text-white transition-colors shadow-lg shadow-brand-600/30 cursor-pointer"
          >
            {isSubmitting ? 'Kaydediliyor...' : cameraToEdit ? 'Güncelle' : 'Kamerayı Ekle'}
          </button>
        </div>
      </form>
    </Modal>
  );
};
