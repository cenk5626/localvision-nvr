import React, { useEffect, useState } from 'react';
import { systemApi } from '../services/api';
import { CheckIcon, SettingsIcon } from '../components/common/Icons';

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<any>(null);
  const [checklist, setChecklist] = useState<any>(null);

  useEffect(() => {
    const fetchSettingsData = async () => {
      try {
        const [hRes, cRes] = await Promise.all([
          systemApi.getHealth(),
          systemApi.getPrivacyChecklist(),
        ]);
        setHealth(hRes.data);
        setChecklist(cRes.data);
      } catch (e) {
        // ignore
      }
    };
    fetchSettingsData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Üst Başlık */}
      <div className="p-5 bg-dark-800 border border-dark-700 rounded-2xl shadow-lg">
        <h2 className="text-xl font-bold text-white tracking-tight">Sistem Ayarları ve Gizlilik</h2>
        <p className="text-xs text-slate-400">
          Tasarım itibarıyla gizlilik ilkeleri, yasal uyum denetim listesi ve sistem özellikleri
        </p>
      </div>

      {/* Katı Gizlilik Garantisi Kartı */}
      <div className="p-6 bg-dark-800 border border-dark-700 rounded-2xl space-y-4 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-lg">
            🛡️
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Tasarım İtibarıyla Gizlilik (Privacy by Design)</h3>
            <p className="text-xs text-slate-400">LocalVision NVR mimari olarak katı gizlilik sınırlarıyla geliştirilmiştir.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-2 text-xs">
          <div className="p-3.5 rounded-xl bg-dark-900/80 border border-dark-700 flex items-start gap-2.5">
            <span className="text-emerald-400 font-bold">✓</span>
            <div>
              <span className="font-semibold text-white block">Sıfır Biyometri / Yüz Tanıma Yok</span>
              <span className="text-slate-400 text-[11px]">Sistem asla yüz veritabanı, yüz taraması veya kişi profillemesi yapmaz.</span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-dark-900/80 border border-dark-700 flex items-start gap-2.5">
            <span className="text-emerald-400 font-bold">✓</span>
            <div>
              <span className="font-semibold text-white block">İnternetsiz Yerel Ağ (%100 Çevrimdışı)</span>
              <span className="text-slate-400 text-[11px]">Dış ağ kesilse bile kayıt, canlı izleme ve AI olay tespiti kesintisiz çalışır.</span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-dark-900/80 border border-dark-700 flex items-start gap-2.5">
            <span className="text-emerald-400 font-bold">✓</span>
            <div>
              <span className="font-semibold text-white block">Şifreli Kimlik Bilgileri (AES-256)</span>
              <span className="text-slate-400 text-[11px]">Kamera RTSP ve ONVIF şifreleri veritabanında AES-256-GCM ile saklanır.</span>
            </div>
          </div>
        </div>
      </div>

      {/* Yasal Denetim Listesi (KVKK / GDPR / Yerel Mevzuat) */}
      <div className="p-6 bg-dark-800 border border-dark-700 rounded-2xl space-y-4 shadow-xl">
        <h3 className="text-sm font-semibold text-white">Yasal Mevzuat ve Güvenlik Kontrol Listesi</h3>
        <p className="text-xs text-slate-400">
          Kamera sisteminizi işletirken aşağıdaki yasal gerekliliklere dikkat etmeniz önerilir:
        </p>

        <div className="space-y-3 pt-1 text-xs">
          {checklist?.legal_checklist?.map((item: any, idx: number) => (
            <div
              key={idx}
              className="p-3.5 bg-dark-900/70 border border-dark-700 rounded-xl flex items-start justify-between gap-4"
            >
              <div className="space-y-1">
                <span className="font-bold text-slate-200">{item.item}</span>
                <p className="text-slate-400 text-[11px] leading-relaxed">{item.description}</p>
              </div>
              <span className="px-2.5 py-1 rounded-md text-[10px] font-bold bg-dark-800 border border-dark-700 text-emerald-400 shrink-0">
                {item.status}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Uzaktan Erişim ve Güvenlik Tavsiyesi */}
      <div className="p-5 bg-dark-800 border border-dark-700 rounded-2xl space-y-3 text-xs shadow-xl">
        <h3 className="text-sm font-semibold text-white">Güvenli Uzaktan Erişim Tavsiyesi</h3>
        <p className="text-slate-400 leading-relaxed">
          LocalVision NVR, güvenliğiniz için varsayılan olarak yalnızca yerel ağda dinler. Dışarıdan izleme gerektiğinde:
        </p>
        <ul className="list-disc list-inside text-slate-300 space-y-1 text-[11px]">
          <li><span className="text-amber-400 font-semibold">Asla</span> modeminize 8000 veya 554 portunu doğrudan dışarıya (port forwarding) açmayın.</li>
          <li>Güvenli bağlantı için yerel ağınıza <span className="text-emerald-400 font-semibold">WireGuard</span> veya <span className="text-emerald-400 font-semibold">Tailscale VPN</span> kurarak bağlanın.</li>
          <li>Web erişimi için HTTPS / TLS sertifikalı ters vekil sunucu (Reverse Proxy: Nginx veya Caddy) kullanın.</li>
        </ul>
      </div>

      {/* Sistem Bilgileri */}
      {health && (
        <div className="p-5 bg-dark-800 border border-dark-700 rounded-2xl flex flex-wrap items-center justify-between gap-4 text-xs text-slate-400">
          <div>
            Sürüm: <span className="text-white font-mono">{health.app_name} v{health.version}</span>
          </div>
          <div>
            İşletim Sistemi: <span className="text-slate-200 font-medium">{health.os}</span>
          </div>
          <div>
            Uptime: <span className="text-slate-200 font-medium">{Math.floor(health.uptime_seconds / 60)} dk</span>
          </div>
        </div>
      )}
    </div>
  );
};
