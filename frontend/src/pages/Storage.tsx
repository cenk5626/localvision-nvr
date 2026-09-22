import React, { useEffect, useState } from 'react';
import { DiskUsage } from '../types';
import { storageApi } from '../services/api';
import { RefreshIcon, StorageIcon } from '../components/common/Icons';

export const Storage: React.FC = () => {
  const [diskInfo, setDiskInfo] = useState<DiskUsage | null>(null);
  const [cameraUsages, setCameraUsages] = useState<any[]>([]);
  const [policy, setPolicy] = useState<any>(null);
  const [storagePath, setStoragePath] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  // Politika formu
  const [retentionDays, setRetentionDays] = useState(14);
  const [maxDiskUsageGb, setMaxDiskUsageGb] = useState(500);
  const [autoPrune, setAutoPrune] = useState(true);
  const [nasEnabled, setNasEnabled] = useState(false);
  const [nasPath, setNasPath] = useState('');
  const [nasSchedule, setNasSchedule] = useState('daily');

  const [isPruning, setIsPruning] = useState(false);
  const [isBackingUp, setIsBackingUp] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [statusRes, policyRes] = await Promise.all([
        storageApi.getStatus(),
        storageApi.getPolicy(),
      ]);
      setDiskInfo(statusRes.data.disk);
      setCameraUsages(statusRes.data.cameras || []);
      setStoragePath(statusRes.data.storage_path || '');

      const p = policyRes.data;
      setPolicy(p);
      setRetentionDays(p.retention_days);
      setMaxDiskUsageGb(p.max_disk_usage_gb);
      setAutoPrune(p.auto_prune_enabled);
      setNasEnabled(p.nas_backup_enabled);
      setNasPath(p.nas_mount_path || '');
      setNasSchedule(p.nas_backup_schedule || 'daily');
    } catch (e) {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSavePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await storageApi.updatePolicy({
        retention_days: Number(retentionDays),
        max_disk_usage_gb: Number(maxDiskUsageGb),
        min_free_disk_percent: 10,
        auto_prune_enabled: autoPrune,
        nas_backup_enabled: nasEnabled,
        nas_mount_path: nasPath,
        nas_backup_schedule: nasSchedule,
      });
      setActionMessage('Depolama politikası güncellendi.');
      fetchData();
    } catch (err) {
      alert('Politika güncellenemedi.');
    }
  };

  const handlePruneNow = async () => {
    if (confirm('Saklama süresi dolmuş eski ve korunmayan kayıtlar kalıcı olarak silinecektir. Onaylıyor musunuz?')) {
      setIsPruning(true);
      setActionMessage(null);
      try {
        const res = await storageApi.pruneNow();
        setActionMessage(res.data.message);
        fetchData();
      } catch (err) {
        alert('Temizlik sırasında hata oluştu.');
      } finally {
        setIsPruning(false);
      }
    }
  };

  const handleBackupNas = async () => {
    if (!nasPath) {
      alert('Lütfen geçerli bir NAS hedef yolu girin.');
      return;
    }
    setIsBackingUp(true);
    setActionMessage(null);
    try {
      const res = await storageApi.backupNas({ nas_path: nasPath });
      setActionMessage(res.data.message);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'NAS yedekleme başarısız oldu.');
    } finally {
      setIsBackingUp(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Üst Başlık */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 bg-dark-800 border border-dark-700 rounded-2xl shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Depolama, Kota ve Yedekleme</h2>
          <p className="text-xs text-slate-400">
            Disk alanı yönetimi, otomatik budama politikası ve NAS (SMB/NFS) entegrasyonu
          </p>
        </div>

        <button
          onClick={fetchData}
          className="p-2.5 rounded-xl bg-dark-900 hover:bg-dark-700 border border-dark-700 text-slate-300 transition-colors cursor-pointer"
          title="Yenile"
        >
          <RefreshIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Geri Alınamaz Silinme Bildirimi (Prompt Zorunluluğu) */}
      <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-start gap-3 text-xs text-rose-300">
        <span className="text-base leading-none">⚠️</span>
        <div>
          <span className="font-semibold text-white">Kayıt Silme Politikası Uyarısı: </span>
          Saklama süresi dolan veya disk alanı azaldığında otomatik budama ile silinen kayıtlar
          <span className="font-bold underline ml-1">kesinlikle geri alınamaz.</span> Delil niteliğindeki veya kritik kayıtları korumak için kayıt listesinden "Korumalı / Yıldızlı" olarak işaretleyin. Korumalı kayıtlar sistem tarafından asla otomatik silinmez.
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 bg-emerald-500/15 border border-emerald-500/30 rounded-xl text-xs text-emerald-400">
          ✓ {actionMessage}
        </div>
      )}

      {/* Disk Durumu Göstergesi */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="md:col-span-2 p-6 bg-dark-800 border border-dark-700 rounded-2xl space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Birincil Kayıt Diski</h3>
            <span className="text-xs font-mono text-slate-400 truncate max-w-xs">{storagePath}</span>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-400">Kullanılan Alan: {diskInfo?.used_gb} GB</span>
              <span className="text-emerald-400 font-bold">Kalan: {diskInfo?.free_gb} GB (%{diskInfo?.free_percent})</span>
            </div>
            <div className="w-full bg-dark-900 rounded-full h-3 overflow-hidden border border-dark-700">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${
                  (diskInfo?.free_percent || 0) < 10 ? 'bg-rose-500' : 'bg-brand-500'
                }`}
                style={{ width: `${100 - (diskInfo?.free_percent || 0)}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-[11px] text-slate-500">
              <span>0 GB</span>
              <span>Toplam: {diskInfo?.total_gb} GB</span>
            </div>
          </div>

          <div className="pt-2 flex justify-end gap-3">
            <button
              onClick={handlePruneNow}
              disabled={isPruning}
              className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-rose-400 border border-rose-500/30 rounded-xl text-xs font-semibold transition-colors cursor-pointer"
            >
              {isPruning ? 'Temizleniyor...' : '🗑️ Süresi Dolanları Şimdi Temizle (Prune Now)'}
            </button>
          </div>
        </div>

        {/* Kamera Başına Disk Kullanımı */}
        <div className="p-6 bg-dark-800 border border-dark-700 rounded-2xl space-y-3 shadow-xl flex flex-col justify-between">
          <h3 className="text-sm font-semibold text-white">Kamera Bazlı Depolama</h3>
          <div className="space-y-2 flex-1 overflow-y-auto max-h-48 text-xs divide-y divide-dark-700/50">
            {cameraUsages.length === 0 ? (
              <p className="text-slate-500 py-4">Henüz kayıt verisi bulunmuyor.</p>
            ) : (
              cameraUsages.map((cu) => (
                <div key={cu.camera_id} className="pt-2 flex justify-between items-center">
                  <span className="text-slate-300 font-medium">Kamera {cu.camera_id}</span>
                  <span className="font-mono text-emerald-400">{cu.used_mb} MB</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Saklama Politikası ve NAS Yapılandırması */}
      <form onSubmit={handleSavePolicy} className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Sol: Otomatik Budama Politikası */}
        <div className="p-6 bg-dark-800 border border-dark-700 rounded-2xl space-y-4 shadow-xl">
          <h3 className="text-sm font-semibold text-white">Otomatik Saklama & Budama (Retention)</h3>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Genel Saklama Süresi (Gün)
            </label>
            <input
              type="number"
              min={1}
              max={365}
              value={retentionDays}
              onChange={(e) => setRetentionDays(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 bg-dark-900 border border-dark-700 rounded-xl text-sm text-white focus:outline-none focus:border-brand-500"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Bu süreden eski, yıldızsız kayıtlar otomatik olarak silinir.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Maksimum Disk Kotası (GB)
            </label>
            <input
              type="number"
              min={10}
              max={50000}
              value={maxDiskUsageGb}
              onChange={(e) => setMaxDiskUsageGb(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 bg-dark-900 border border-dark-700 rounded-xl text-sm text-white focus:outline-none focus:border-brand-500"
            />
          </div>

          <label className="flex items-center gap-2 p-3 bg-dark-900/60 rounded-xl border border-dark-700 cursor-pointer">
            <input
              type="checkbox"
              checked={autoPrune}
              onChange={(e) => setAutoPrune(e.target.checked)}
              className="rounded border-dark-600 text-brand-600"
            />
            <span className="text-xs text-slate-200 font-medium">
              Otomatik budama döngüsünü etkinleştir
            </span>
          </label>
        </div>

        {/* Sağ: NAS Yedekleme Yapılandırması */}
        <div className="p-6 bg-dark-800 border border-dark-700 rounded-2xl space-y-4 shadow-xl flex flex-col justify-between">
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-white">Ağ Depolama / NAS Yedekleme (SMB/NFS)</h3>

            <label className="flex items-center gap-2 p-3 bg-dark-900/60 rounded-xl border border-dark-700 cursor-pointer">
              <input
                type="checkbox"
                checked={nasEnabled}
                onChange={(e) => setNasEnabled(e.target.checked)}
                className="rounded border-dark-600 text-brand-600"
              />
              <span className="text-xs text-slate-200 font-medium">
                NAS harici yedeklemeyi etkinleştir
              </span>
            </label>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                NAS Paylaşım Yolu (Windows UNC veya Linux Mount)
              </label>
              <input
                type="text"
                value={nasPath}
                onChange={(e) => setNasPath(e.target.value)}
                placeholder="\\192.168.1.50\nvr_backup veya /mnt/nas"
                className="w-full px-3.5 py-2.5 bg-dark-900 border border-dark-700 rounded-xl text-sm text-white focus:outline-none focus:border-brand-500 font-mono text-xs"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Yedekleme Zaman Planı
              </label>
              <select
                value={nasSchedule}
                onChange={(e) => setNasSchedule(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-dark-900 border border-dark-700 rounded-xl text-sm text-white focus:outline-none focus:border-brand-500 cursor-pointer"
              >
                <option value="daily">Her Gece (Günlük Yedekleme)</option>
                <option value="weekly">Haftalık Yedekleme</option>
              </select>
            </div>
          </div>

          <div className="pt-4 flex items-center justify-between border-t border-dark-700">
            <button
              type="button"
              onClick={handleBackupNas}
              disabled={isBackingUp || !nasPath}
              className="px-4 py-2 bg-accent-cyan/20 hover:bg-accent-cyan/30 text-cyan-300 border border-cyan-500/30 rounded-xl text-xs font-semibold transition-colors disabled:opacity-40 cursor-pointer"
            >
              {isBackingUp ? 'Yedekleniyor...' : '💾 NAS\'a Şimdi Yedekle'}
            </button>

            <button
              type="submit"
              className="px-5 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-xl text-xs font-semibold shadow cursor-pointer"
            >
              Ayarları Kaydet
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
