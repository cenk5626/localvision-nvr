/**
 * LocalVision NVR - Frontend Sabitleri ve Numaralandırmaları (Enums).
 * Kullanıcı Kuralı: "magic number / string kontrolü: önemli değerler sabit veya enum olarak tanımlanmalı"
 */

export enum UserRole {
  ADMIN = "admin",
  OPERATOR = "operator",
  VIEWER = "viewer",
  USER = "user",
}

export const USER_ROLE_LABELS: Record<UserRole, string> = {
  [UserRole.ADMIN]: "Sistem Yöneticisi",
  [UserRole.OPERATOR]: "Operatör",
  [UserRole.VIEWER]: "İzleyici",
  [UserRole.USER]: "Kullanıcı",
};

export enum CameraStatus {
  ONLINE = "online",
  OFFLINE = "offline",
  CONNECTING = "connecting",
  ERROR = "error",
}

export const CAMERA_STATUS_LABELS: Record<CameraStatus, { text: string; color: string }> = {
  [CameraStatus.ONLINE]: { text: "Çevrimiçi", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
  [CameraStatus.OFFLINE]: { text: "Çevrimdışı", color: "bg-rose-500/20 text-rose-400 border-rose-500/30" },
  [CameraStatus.CONNECTING]: { text: "Bağlanıyor", color: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
  [CameraStatus.ERROR]: { text: "Hata", color: "bg-rose-600/20 text-rose-300 border-rose-600/30" },
};

export enum CameraSourceType {
  RTSP = "rtsp",
  WEBCAM = "webcam",
  ONVIF = "onvif",
  FILE_LOOP = "file_loop",
}

export const SOURCE_TYPE_LABELS: Record<CameraSourceType, string> = {
  [CameraSourceType.RTSP]: "RTSP Akışı",
  [CameraSourceType.WEBCAM]: "PC Web Kamerası",
  [CameraSourceType.ONVIF]: "ONVIF IP Kamera",
  [CameraSourceType.FILE_LOOP]: "Sentetik Test Dosyası",
};

export enum RecordingMode {
  CONTINUOUS = "continuous",
  MOTION = "motion",
  PERSON_ONLY = "person_only",
  VEHICLE_ONLY = "vehicle_only",
  AI_ANY = "ai_any",
  SCHEDULED = "scheduled",
  MANUAL = "manual",
  DISABLED = "disabled",
}

export const RECORDING_MODE_LABELS: Record<RecordingMode, string> = {
  [RecordingMode.CONTINUOUS]: "Sürekli Kayıt (7/24)",
  [RecordingMode.MOTION]: "Sadece Hareket Algılandığında",
  [RecordingMode.PERSON_ONLY]: "Sadece İnsan Algılandığında (Gizlilik)",
  [RecordingMode.VEHICLE_ONLY]: "Sadece Araç Algılandığında",
  [RecordingMode.AI_ANY]: "İnsan veya Araç Algılandığında",
  [RecordingMode.SCHEDULED]: "Zaman Planına Göre",
  [RecordingMode.MANUAL]: "Manuel Kayıt",
  [RecordingMode.DISABLED]: "Kayıt Kapalı",
};

export enum EventType {
  PERSON_DETECTED = "person_detected",
  VEHICLE_DETECTED = "vehicle_detected",
  MOTION_DETECTED = "motion_detected",
  LINE_CROSSED = "line_crossed",
  ZONE_INTRUSION = "zone_intrusion",
  DWELL_ALERT = "dwell_alert",
}

export const EVENT_TYPE_LABELS: Record<EventType, { label: string; badgeColor: string }> = {
  [EventType.PERSON_DETECTED]: { label: "İnsan Algılandı", badgeColor: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
  [EventType.VEHICLE_DETECTED]: { label: "Araç Algılandı", badgeColor: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
  [EventType.MOTION_DETECTED]: { label: "Hareket Algılandı", badgeColor: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  [EventType.LINE_CROSSED]: { label: "Sanal Çizgi Geçildi", badgeColor: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
  [EventType.ZONE_INTRUSION]: { label: "Yasak Bölge İhlali", badgeColor: "bg-rose-500/20 text-rose-400 border-rose-500/30" },
  [EventType.DWELL_ALERT]: { label: "Bölgede Uzun Süre Kalındı", badgeColor: "bg-orange-500/20 text-orange-400 border-orange-500/30" },
};

export enum GridMode {
  SINGLE = "1x1",
  GRID_2X2 = "2x2",
  GRID_3X3 = "3x3",
  GRID_4X4 = "4x4",
}
