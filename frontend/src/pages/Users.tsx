import React, { useEffect, useState } from 'react';
import { Camera, User } from '../types';
import { camerasApi, usersApi } from '../services/api';
import { PlusIcon, RefreshIcon, TrashIcon, UsersIcon } from '../components/common/Icons';
import { Modal } from '../components/common/Modal';
import { USER_ROLE_LABELS, UserRole } from '../constants';

export const UsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Kullanıcı Ekleme / Düzenleme Modalı
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<UserRole>(UserRole.USER);
  const [allowedCams, setAllowedCams] = useState<number[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const [uRes, cRes] = await Promise.all([usersApi.list(), camerasApi.list()]);
      setUsers(uRes.data);
      setCameras(cRes.data);
    } catch (e) {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleOpenAdd = () => {
    setEditingUserId(null);
    setUsername('');
    setPassword('');
    setFullName('');
    setEmail('');
    setRole(UserRole.USER);
    setAllowedCams([]);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (u: User) => {
    setEditingUserId(u.id);
    setUsername(u.username);
    setPassword('');
    setFullName(u.full_name || '');
    setEmail(u.email || '');
    setRole(u.role);
    setAllowedCams(u.allowed_camera_ids || []);
    setIsModalOpen(true);
  };

  const handleDeleteUser = async (u: User) => {
    if (confirm(`"${u.username}" kullanıcısını silmek istediğinize emin misiniz?`)) {
      try {
        await usersApi.delete(u.id);
        fetchUsers();
      } catch (err: any) {
        alert(err.response?.data?.detail || 'Kullanıcı silinemedi.');
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      if (editingUserId) {
        await usersApi.update(editingUserId, {
          full_name: fullName,
          email,
          role,
          allowed_camera_ids: allowedCams,
          new_password: password || undefined,
        });
      } else {
        await usersApi.create({
          username,
          password,
          full_name: fullName,
          email,
          role,
          allowed_camera_ids: allowedCams,
        });
      }
      setIsModalOpen(false);
      fetchUsers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'İşlem başarısız.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleCameraPerm = (camId: number) => {
    if (allowedCams.includes(camId)) {
      setAllowedCams(allowedCams.filter((id) => id !== camId));
    } else {
      setAllowedCams([...allowedCams, camId]);
    }
  };

  return (
    <div className="space-y-6">
      {/* Üst Başlık & Buton */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 bg-dark-800 border border-dark-700 rounded-2xl shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Kullanıcılar ve Roller (RBAC)</h2>
          <p className="text-xs text-slate-400">
            Sistem yöneticisi, operatör, izleyici ve kullanıcı hesaplarını yönetin
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchUsers}
            className="p-2.5 rounded-xl bg-dark-900 hover:bg-dark-700 border border-dark-700 text-slate-300 transition-colors cursor-pointer"
            title="Yenile"
          >
            <RefreshIcon className="w-4 h-4" />
          </button>

          <button
            onClick={handleOpenAdd}
            className="px-4 py-2.5 bg-brand-600 hover:bg-brand-500 text-white rounded-xl text-xs font-semibold flex items-center gap-2 shadow-lg shadow-brand-600/30 transition-colors cursor-pointer"
          >
            <PlusIcon className="w-4 h-4" />
            Yeni Kullanıcı Ekle
          </button>
        </div>
      </div>

      {/* Kullanıcı Tablosu */}
      <div className="bg-dark-800 border border-dark-700 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-dark-900/60 border-b border-dark-700 text-slate-400 uppercase tracking-wider font-semibold">
              <tr>
                <th className="px-6 py-3.5">Kullanıcı</th>
                <th className="px-6 py-3.5">Rol</th>
                <th className="px-6 py-3.5">İzinli Kameralar</th>
                <th className="px-6 py-3.5">Durum</th>
                <th className="px-6 py-3.5 text-right">İşlemler</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dark-700/60">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-dark-700/40 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-semibold text-white">{u.username}</div>
                    <div className="text-[11px] text-slate-400">{u.full_name || u.email || '—'}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-1 rounded-md text-[11px] font-semibold bg-dark-700 text-slate-200 border border-dark-600">
                      {USER_ROLE_LABELS[u.role] || u.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-300">
                    {u.role === UserRole.ADMIN || u.role === UserRole.OPERATOR ? (
                      <span className="text-emerald-400 font-medium">Tüm Kameralar (Tam Yetki)</span>
                    ) : u.allowed_camera_ids?.length > 0 ? (
                      <span className="text-cyan-400">{u.allowed_camera_ids.length} Kamera İzinli</span>
                    ) : (
                      <span className="text-slate-500">Kamera İzni Yok</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${u.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                      {u.is_active ? 'Aktif' : 'Devre Dışı'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button
                      onClick={() => handleOpenEdit(u)}
                      className="px-2.5 py-1 rounded-lg bg-dark-700 hover:bg-dark-600 text-slate-300 hover:text-white transition-colors cursor-pointer"
                    >
                      Düzenle
                    </button>
                    {u.username !== 'admin' && (
                      <button
                        onClick={() => handleDeleteUser(u)}
                        className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 transition-colors cursor-pointer"
                        title="Sil"
                      >
                        <TrashIcon className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Kullanıcı Ekle / Düzenle Modalı */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingUserId ? 'Kullanıcıyı Düzenle' : 'Yeni Kullanıcı Oluştur'}
        maxWidth="max-w-lg"
      >
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Kullanıcı Adı *</label>
            <input
              type="text"
              required
              disabled={Boolean(editingUserId)}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-dark-900 border border-dark-700 rounded-xl text-white disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">
              {editingUserId ? 'Yeni Parola (Değiştirmek istemiyorsanız boş bırakın)' : 'Parola *'}
            </label>
            <input
              type="password"
              required={!editingUserId}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3.5 py-2.5 bg-dark-900 border border-dark-700 rounded-xl text-white"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Ad Soyad</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-xl text-white"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Sistem Rolü *</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as UserRole)}
                className="w-full px-3 py-2 bg-dark-900 border border-dark-700 rounded-xl text-white cursor-pointer"
              >
                {Object.entries(USER_ROLE_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Kamera İzinleri (Yalnızca Viewer / User rolleri için) */}
          {(role === UserRole.VIEWER || role === UserRole.USER) && (
            <div className="space-y-2 pt-2 border-t border-dark-700">
              <label className="block text-slate-300 font-semibold">İzin Verilen Kameralar:</label>
              <div className="max-h-36 overflow-y-auto space-y-1.5 p-2 bg-dark-900 rounded-xl border border-dark-700">
                {cameras.map((c) => (
                  <label key={c.id} className="flex items-center gap-2 p-1 text-slate-300 hover:text-white cursor-pointer">
                    <input
                      type="checkbox"
                      checked={allowedCams.includes(c.id)}
                      onChange={() => toggleCameraPerm(c.id)}
                      className="rounded border-dark-600 text-brand-600"
                    />
                    <span>{c.name}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-3 border-t border-dark-700">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 rounded-xl text-slate-400 hover:text-white"
            >
              İptal
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-xl font-semibold shadow cursor-pointer"
            >
              {isSubmitting ? 'Kaydediliyor...' : 'Kaydet'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
