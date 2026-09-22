import axios from 'axios';
import {
  MOCK_USER,
  MOCK_CAMERAS,
  MOCK_EVENTS,
  MOCK_SYSTEM_HEALTH,
  MOCK_STORAGE_STATUS,
  MOCK_STORAGE_POLICY,
  MOCK_USERS,
  MOCK_AUDIT_LOGS,
  MOCK_RECORDINGS,
} from './mockData';

export const isDemoMode = (): boolean => {
  return localStorage.getItem('localvision_demo_mode') === 'true';
};

export const setDemoMode = (enabled: boolean) => {
  if (enabled) {
    localStorage.setItem('localvision_demo_mode', 'true');
    localStorage.setItem('localvision_token', MOCK_USER.access_token);
    localStorage.setItem('localvision_user', JSON.stringify(MOCK_USER));
  } else {
    localStorage.removeItem('localvision_demo_mode');
    localStorage.removeItem('localvision_token');
    localStorage.removeItem('localvision_user');
  }
};

const getBaseUrl = (): string => {
  return localStorage.getItem('localvision_api_url') || (import.meta as any).env?.VITE_API_URL || '/api';
};

const api = axios.create({
  baseURL: getBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

// Oturum jetonunu her isteğe ekle
api.interceptors.request.use((config) => {
  const customUrl = localStorage.getItem('localvision_api_url');
  if (customUrl) {
    config.baseURL = customUrl;
  }
  const token = localStorage.getItem('localvision_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 401 Unauthorized durumunda login ekranına yönlendir
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !isDemoMode()) {
      localStorage.removeItem('localvision_token');
      localStorage.removeItem('localvision_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Demo Modu için sahte axios yanıtı yardımcısı
const mockResponse = <T>(data: T) => Promise.resolve({ data, status: 200, statusText: 'OK', headers: {}, config: {} as any });

export const authApi = {
  login: async (data: { username: string; password: string }) => {
    // Vercel üzerinde veya demo modunda doğrudan giriş sağla
    const isVercelHost = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app');
    const hasCustomBackend = Boolean(localStorage.getItem('localvision_api_url'));

    if (isDemoMode() || data.username === 'demo' || (isVercelHost && !hasCustomBackend)) {
      setDemoMode(true);
      return mockResponse(MOCK_USER);
    }

    try {
      return await api.post('/auth/login', data);
    } catch (err: any) {
      // Backend çevrimdışıysa (veya yerel sunucu henüz açılmadıysa) admin girişini demo modunda aç
      const isOffline = !err.response || err.response.status === 404 || err.code === 'ERR_NETWORK';
      if (isOffline && (data.username === 'admin' || isVercelHost)) {
        console.warn('Backend API ulaşılamadı. Vitrin/Demo modu ile oturum açılıyor.');
        setDemoMode(true);
        return mockResponse(MOCK_USER);
      }
      throw err;
    }
  },
  getMe: () => isDemoMode() ? mockResponse(MOCK_USER) : api.get('/auth/me'),
  updatePreferences: (preferences: Record<string, any>) =>
    isDemoMode() ? mockResponse({ ...MOCK_USER, preferences }) : api.put('/auth/preferences', { preferences }),
};

export const camerasApi = {
  list: () => isDemoMode() ? mockResponse(MOCK_CAMERAS) : api.get('/cameras'),
  get: (id: number) => {
    if (isDemoMode()) {
      const cam = MOCK_CAMERAS.find(c => c.id === id) || MOCK_CAMERAS[0];
      return mockResponse(cam);
    }
    return api.get(`/cameras/${id}`);
  },
  create: (data: any) => {
    if (isDemoMode()) {
      const newCam = { ...data, id: Date.now(), status: 'online' };
      MOCK_CAMERAS.push(newCam);
      return mockResponse(newCam);
    }
    return api.post('/cameras', data);
  },
  update: (id: number, data: any) => {
    if (isDemoMode()) {
      return mockResponse({ id, ...data });
    }
    return api.put(`/cameras/${id}`, data);
  },
  delete: (id: number) => isDemoMode() ? mockResponse({ message: 'Deleted' }) : api.delete(`/cameras/${id}`),
  testConnection: (data: any) => isDemoMode() ? mockResponse({ success: true, message: 'Demo bağlantı testi başarılı' }) : api.post('/cameras/test-connection', data),
  discoverWebcams: () => isDemoMode() ? mockResponse([{ index: 0, name: 'Demo PC Web Kamerası 0', status: 'available' }]) : api.get('/cameras/discover-webcams'),
  discoverOnvif: () => isDemoMode() ? mockResponse([]) : api.get('/cameras/discover-onvif'),
};

export const eventsApi = {
  list: (params?: any) => isDemoMode() ? mockResponse(MOCK_EVENTS) : api.get('/events', { params }),
  get: (id: number) => {
    if (isDemoMode()) {
      const ev = MOCK_EVENTS.find(e => e.id === id) || MOCK_EVENTS[0];
      return mockResponse(ev);
    }
    return api.get(`/events/${id}`);
  },
  bookmark: (id: number, data: { is_bookmarked: boolean; bookmark_note?: string }) => {
    if (isDemoMode()) {
      const ev = MOCK_EVENTS.find(e => e.id === id);
      if (ev) {
        ev.is_bookmarked = data.is_bookmarked;
        ev.bookmark_note = data.bookmark_note || null;
      }
      return mockResponse(ev);
    }
    return api.post(`/events/${id}/bookmark`, data);
  },
};

export const recordingsApi = {
  list: (params: { camera_id: number; date?: string; limit?: number }) =>
    isDemoMode() ? mockResponse(MOCK_RECORDINGS) : api.get('/recordings', { params }),
  bookmark: (id: number, data: { is_bookmarked: boolean; is_protected: boolean }) =>
    isDemoMode() ? mockResponse({ id, ...data }) : api.post(`/recordings/${id}/bookmark`, data),
  export: (id: number, data: { add_watermark: boolean; notes?: string }) =>
    isDemoMode() ? mockResponse({ message: 'Demo ihracat hazır', download_url: '#' }) : api.post(`/recordings/${id}/export`, data),
  delete: (id: number) => isDemoMode() ? mockResponse({ message: 'Deleted' }) : api.delete(`/recordings/${id}`),
};

export const storageApi = {
  getStatus: () => isDemoMode() ? mockResponse(MOCK_STORAGE_STATUS) : api.get('/storage/status'),
  getPolicy: () => isDemoMode() ? mockResponse(MOCK_STORAGE_POLICY) : api.get('/storage/policy'),
  updatePolicy: (data: any) => isDemoMode() ? mockResponse(data) : api.put('/storage/policy', data),
  pruneNow: () => isDemoMode() ? mockResponse({ pruned_count: 3, freed_gb: 12.4 }) : api.post('/storage/prune-now'),
  backupNas: (data: { nas_path: string }) => isDemoMode() ? mockResponse({ synced_count: 5, transferred_gb: 4.2 }) : api.post('/storage/backup-nas', data),
};

export const usersApi = {
  list: () => isDemoMode() ? mockResponse(MOCK_USERS) : api.get('/users'),
  create: (data: any) => isDemoMode() ? mockResponse({ id: Date.now(), ...data }) : api.post('/users', data),
  update: (id: number, data: any) => isDemoMode() ? mockResponse({ id, ...data }) : api.put(`/users/${id}`, data),
  delete: (id: number) => isDemoMode() ? mockResponse({ message: 'Deleted' }) : api.delete(`/users/${id}`),
};

export const systemApi = {
  getHealth: () => isDemoMode() ? mockResponse(MOCK_SYSTEM_HEALTH) : api.get('/system/health'),
  getPrivacyChecklist: () => isDemoMode() ? mockResponse({
    offline_mode: true,
    face_recognition_disabled: true,
    biometrics_disabled: true,
    encrypted_credentials: true,
    tamper_proof_logs: true,
  }) : api.get('/system/privacy-checklist'),
  getAuditLogs: (params?: any) => isDemoMode() ? mockResponse(MOCK_AUDIT_LOGS) : api.get('/system/audit-logs', { params }),
};

export default api;
