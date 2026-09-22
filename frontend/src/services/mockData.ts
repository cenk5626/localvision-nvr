/**
 * LocalVision NVR - Vercel Vitrin / Demo Modu İçin Mock Veri Seti
 * Canlı sunucuya bağlı olmadan Vercel üzerinde tüm arayüzü ve özellikleri test etmeyi sağlar.
 */

import { CameraSourceType, CameraStatus, EventType, RecordingMode, UserRole } from '../constants';

export const MOCK_USER = {
  access_token: "demo_vercel_jwt_token_localvision_2026",
  token_type: "bearer",
  user_id: 1,
  username: "admin",
  role: UserRole.ADMIN,
  full_name: "Sistem Yöneticisi (Demo)",
  allowed_camera_ids: [],
  preferences: { theme: "dark", default_grid: "2x2" },
};

export const MOCK_CAMERAS = [
  {
    id: 1,
    name: "Ön Giriş Kapısı (IP Cam 1)",
    description: "Ana bina giriş kapısı ve turnike alanı",
    source_type: CameraSourceType.RTSP,
    rtsp_url: "rtsp://192.168.1.101:554/stream1",
    webcam_index: 0,
    status: CameraStatus.ONLINE,
    is_enabled: true,
    width: 1920,
    height: 1080,
    fps: 25,
    codec: "H.264",
    recording_mode: RecordingMode.AI_ANY,
    zones_json: JSON.stringify([
      {
        id: "zone-1",
        name: "Giriş Güvenlik Bölgesi",
        type: "polygon",
        points: [{ x: 100, y: 150 }, { x: 500, y: 150 }, { x: 450, y: 400 }, { x: 80, y: 380 }],
        alert_on_person: true,
        alert_on_vehicle: false,
      }
    ]),
    tripwires_json: JSON.stringify([
      {
        id: "tripwire-1",
        name: "Turnike Giriş Çizgisi",
        start: { x: 120, y: 280 },
        end: { x: 420, y: 280 },
        direction: "both",
      }
    ]),
  },
  {
    id: 2,
    name: "Otopark & Araç Girişi (IP Cam 2)",
    description: "Araç bariyeri ve ziyaretçi otoparkı",
    source_type: CameraSourceType.RTSP,
    rtsp_url: "rtsp://192.168.1.102:554/stream1",
    webcam_index: 0,
    status: CameraStatus.ONLINE,
    is_enabled: true,
    width: 2560,
    height: 1440,
    fps: 30,
    codec: "H.265",
    recording_mode: RecordingMode.VEHICLE_ONLY,
    zones_json: "[]",
    tripwires_json: JSON.stringify([
      {
        id: "tripwire-2",
        name: "Bariyer Çizgisi",
        start: { x: 50, y: 320 },
        end: { x: 550, y: 320 },
        direction: "both",
      }
    ]),
  },
  {
    id: 3,
    name: "Depo İç Güvenlik (IP Cam 3)",
    description: "Hammadde ve sevkiyat alanı",
    source_type: CameraSourceType.RTSP,
    rtsp_url: "rtsp://192.168.1.103:554/stream1",
    webcam_index: 0,
    status: CameraStatus.ONLINE,
    is_enabled: true,
    width: 1920,
    height: 1080,
    fps: 20,
    codec: "H.264",
    recording_mode: RecordingMode.CONTINUOUS,
    zones_json: JSON.stringify([
      {
        id: "zone-depo",
        name: "Yasak İstif Alanı",
        type: "polygon",
        points: [{ x: 200, y: 200 }, { x: 600, y: 200 }, { x: 580, y: 450 }, { x: 180, y: 450 }],
        alert_on_person: true,
        alert_on_vehicle: true,
      }
    ]),
    tripwires_json: "[]",
  },
  {
    id: 4,
    name: "Ofis Koridoru (IP Cam 4)",
    description: "Yönetim katı geçiş koridoru",
    source_type: CameraSourceType.RTSP,
    rtsp_url: "rtsp://192.168.1.104:554/stream1",
    webcam_index: 0,
    status: CameraStatus.ONLINE,
    is_enabled: true,
    width: 1280,
    height: 720,
    fps: 15,
    codec: "H.264",
    recording_mode: RecordingMode.PERSON_ONLY,
    zones_json: "[]",
    tripwires_json: "[]",
  },
];

export const MOCK_EVENTS = [
  {
    id: 101,
    camera_id: 1,
    camera_name: "Ön Giriş Kapısı (IP Cam 1)",
    event_type: EventType.PERSON_DETECTED,
    severity: "warning",
    confidence: 0.94,
    bbox: [240, 110, 180, 360],
    snapshot_path: "/snapshots/demo_event_person.jpg",
    clip_path: "/clips/demo_event_person.mp4",
    is_bookmarked: true,
    bookmark_note: "Önemli ziyaretçi girişi doğrulandı",
    created_at: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
  },
  {
    id: 102,
    camera_id: 2,
    camera_name: "Otopark & Araç Girişi (IP Cam 2)",
    event_type: EventType.LINE_CROSSED,
    severity: "info",
    confidence: 0.89,
    bbox: [320, 200, 240, 160],
    snapshot_path: "/snapshots/demo_event_car.jpg",
    clip_path: "/clips/demo_event_car.mp4",
    is_bookmarked: false,
    bookmark_note: null,
    created_at: new Date(Date.now() - 14 * 60 * 1000).toISOString(),
  },
  {
    id: 103,
    camera_id: 3,
    camera_name: "Depo İç Güvenlik (IP Cam 3)",
    event_type: EventType.ZONE_INTRUSION,
    severity: "critical",
    confidence: 0.96,
    bbox: [210, 220, 150, 310],
    snapshot_path: "/snapshots/demo_event_warehouse.jpg",
    clip_path: "/clips/demo_event_warehouse.mp4",
    is_bookmarked: true,
    bookmark_note: "Yetkisiz depo içi hareket",
    created_at: new Date(Date.now() - 42 * 60 * 1000).toISOString(),
  },
  {
    id: 104,
    camera_id: 1,
    camera_name: "Ön Giriş Kapısı (IP Cam 1)",
    event_type: EventType.DWELL_ALERT,
    severity: "warning",
    confidence: 0.91,
    bbox: [250, 130, 170, 340],
    snapshot_path: null,
    clip_path: null,
    is_bookmarked: false,
    bookmark_note: null,
    created_at: new Date(Date.now() - 95 * 60 * 1000).toISOString(),
  },
];

export const MOCK_SYSTEM_HEALTH = {
  status: "healthy",
  app_name: "LocalVision NVR (Vercel Vitrin)",
  version: "1.0.0",
  uptime_seconds: 86400,
  offline_mode: true,
  os: "Cloud CDN / Vercel Edge",
  cpu_percent: 24.5,
  memory_percent: 38.2,
  disk: {
    total_gb: 2000.0,
    used_gb: 840.5,
    free_gb: 1159.5,
    free_percent: 57.9,
    is_low_space: false,
    is_critical: false,
  },
  active_cameras_count: 4,
};

export const MOCK_STORAGE_STATUS = {
  status: "ok",
  total_space_gb: 2000.0,
  used_space_gb: 840.5,
  free_space_gb: 1159.5,
  free_space_percent: 57.9,
  is_low_space: false,
  is_critical: false,
  retention_days: 14,
  pruning_target_gb: 200.0,
  protected_recordings_count: 8,
};

export const MOCK_STORAGE_POLICY = {
  retention_days: 14,
  max_storage_gb: 1800,
  auto_prune: true,
  preserve_bookmarked: true,
};

export const MOCK_USERS = [
  {
    id: 1,
    username: "admin",
    role: UserRole.ADMIN,
    full_name: "Sistem Yöneticisi",
    is_active: true,
    allowed_camera_ids: [],
    created_at: "2026-01-01T00:00:00Z",
  },
  {
    id: 2,
    username: "operator1",
    role: UserRole.OPERATOR,
    full_name: "Nöbetçi Operatör",
    is_active: true,
    allowed_camera_ids: [1, 2, 3],
    created_at: "2026-01-10T00:00:00Z",
  },
  {
    id: 3,
    username: "guvenlik_izleyici",
    role: UserRole.VIEWER,
    full_name: "Güvenlik Görevlisi",
    is_active: true,
    allowed_camera_ids: [1, 2],
    created_at: "2026-02-01T00:00:00Z",
  },
];

export const MOCK_AUDIT_LOGS = [
  {
    id: 1,
    user_id: 1,
    username: "admin",
    action: "system_startup",
    resource_type: "system",
    resource_id: 1,
    details: "Sistem ve yapay zeka tespit motoru başlatıldı",
    created_at: new Date(Date.now() - 3600 * 1000).toISOString(),
  },
  {
    id: 2,
    user_id: 1,
    username: "admin",
    action: "export_clip",
    resource_type: "recording",
    resource_id: 42,
    details: "SHA-256 bütünlük damgalı adli video dışa aktarıldı",
    created_at: new Date(Date.now() - 1800 * 1000).toISOString(),
  },
];

export const MOCK_RECORDINGS = [
  {
    id: 1,
    camera_id: 1,
    camera_name: "Ön Giriş Kapısı (IP Cam 1)",
    file_path: "/recordings/cam1_2026-09-22_10-00-00.mp4",
    start_time: new Date(Date.now() - 7200 * 1000).toISOString(),
    end_time: new Date(Date.now() - 3600 * 1000).toISOString(),
    duration_seconds: 3600,
    file_size_mb: 245.8,
    is_protected: true,
    is_bookmarked: true,
    sha256_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  },
  {
    id: 2,
    camera_id: 2,
    camera_name: "Otopark & Araç Girişi (IP Cam 2)",
    file_path: "/recordings/cam2_2026-09-22_09-00-00.mp4",
    start_time: new Date(Date.now() - 10800 * 1000).toISOString(),
    end_time: new Date(Date.now() - 7200 * 1000).toISOString(),
    duration_seconds: 3600,
    file_size_mb: 312.4,
    is_protected: false,
    is_bookmarked: false,
    sha256_hash: "7d1a54127b222502f5b79b5fb0803061152a44f92b37e23c65dd0040dc61580b",
  },
];
