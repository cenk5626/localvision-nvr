import React, { useEffect, useState } from 'react';
import { systemApi } from '../services/api';
import { HistoryIcon, RefreshIcon } from '../components/common/Icons';

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [actionFilter, setActionFilter] = useState('');
  const [usernameFilter, setUsernameFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const params: any = { limit: 100 };
      if (actionFilter) params.action = actionFilter;
      if (usernameFilter) params.username = usernameFilter;

      const res = await systemApi.getAuditLogs(params);
      setLogs(res.data);
    } catch (e) {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter, usernameFilter]);

  return (
    <div className="space-y-6">
      {/* Üst Başlık & Filtreler */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 bg-dark-800 border border-dark-700 rounded-2xl shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Güvenlik ve Denetim Günlüğü</h2>
          <p className="text-xs text-slate-400">
            Tüm kullanıcı girişleri, indirmeler, dışa aktarmalar ve yetki değişiklikleri değiştirilemez biçimde kaydedilir
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            value={usernameFilter}
            onChange={(e) => setUsernameFilter(e.target.value)}
            placeholder="Kullanıcı adı ara..."
            className="px-3 py-2 bg-dark-900 border border-dark-700 rounded-xl text-xs text-white focus:outline-none focus:border-brand-500"
          />

          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="px-3 py-2 bg-dark-900 border border-dark-700 rounded-xl text-xs text-white focus:outline-none focus:border-brand-500 cursor-pointer"
          >
            <option value="">Tüm Eylemler</option>
            <option value="auth_login">Giriş Başarılı</option>
            <option value="auth_login_failed">Hatalı Giriş Denemesi</option>
            <option value="camera_create">Kamera Eklendi</option>
            <option value="recording_download">Video İndirildi</option>
            <option value="recording_export">Video Dışa Aktarıldı</option>
            <option value="retention_prune">Kayıt Temizlendi</option>
          </select>

          <button
            onClick={fetchLogs}
            className="p-2.5 rounded-xl bg-dark-900 hover:bg-dark-700 border border-dark-700 text-slate-300 transition-colors cursor-pointer"
            title="Yenile"
          >
            <RefreshIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Tablo */}
      <div className="bg-dark-800 border border-dark-700 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-dark-900/60 border-b border-dark-700 text-slate-400 uppercase tracking-wider font-semibold">
              <tr>
                <th className="px-6 py-3.5">Zaman Damgası</th>
                <th className="px-6 py-3.5">Kullanıcı</th>
                <th className="px-6 py-3.5">Eylem</th>
                <th className="px-6 py-3.5">IP Adresi</th>
                <th className="px-6 py-3.5">Ayrıntılar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-700/60">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                    Kayıt bulunamadı.
                  </td>
                </tr>
              ) : (
                logs.map((l) => (
                  <tr key={l.id} className="hover:bg-dark-700/40 transition-colors">
                    <td className="px-6 py-3.5 text-slate-300 font-mono text-[11px]">
                      {new Date(l.created_at).toLocaleString('tr-TR')}
                    </td>
                    <td className="px-6 py-3.5 font-semibold text-white">{l.username}</td>
                    <td className="px-6 py-3.5">
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-dark-900 border border-dark-700 text-cyan-300">
                        {l.action}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 font-mono text-slate-400 text-[11px]">{l.ip_address || '—'}</td>
                    <td className="px-6 py-3.5 font-mono text-slate-400 text-[10px] max-w-xs truncate">
                      {JSON.stringify(l.details)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
