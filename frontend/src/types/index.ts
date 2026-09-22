import { CameraSourceType, CameraStatus, EventType, RecordingMode, UserRole } from '../constants';

export interface User {
  id: number;
  username: string;
  email?: string;
  full_name?: string;
  role: UserRole;
  is_active: boolean;
  allowed_camera_ids: number[];
  created_at: string;
}

export interface Camera {
  id: number;
  name: string;
  description?: string;
  source_type: CameraSourceType;
  rtsp_url?: string;
  webcam_index: number;
  status: CameraStatus;
  is_enabled: boolean;
  fps: number;
  actual_fps: number;
  width: number;
  height: number;
  codec: string;
  recording_mode: RecordingMode;
  detection_enabled: boolean;
  roi_polygons: Array<{ name: string; points: number[][] }>;
  tripwires: Array<{ name: string; line: number[][] }>;
  created_at: string;
}

export interface EventItem {
  id: number;
  camera_id: number;
  camera_name: string;
  event_type: EventType;
  confidence: number;
  temporary_track_id?: number;
  has_snapshot: boolean;
  has_clip: boolean;
  snapshot_url?: string;
  clip_url?: string;
  is_bookmarked: boolean;
  bookmark_note?: string;
  details?: Record<string, any>;
  created_at: string;
}

export interface RecordingItem {
  id: number;
  camera_id: number;
  file_name: string;
  file_size_mb: number;
  duration_seconds: number;
  start_time: string;
  end_time?: string;
  recording_mode: RecordingMode;
  has_ai_event: boolean;
  is_bookmarked: boolean;
  is_protected: boolean;
  stream_url: string;
  download_url: string;
}

export interface DiskUsage {
  total_gb: number;
  used_gb: number;
  free_gb: number;
  free_percent: number;
  is_low_space: boolean;
  is_critical: boolean;
}

export interface SystemHealth {
  status: string;
  app_name: string;
  version: string;
  uptime_seconds: number;
  offline_mode: boolean;
  os: string;
  cpu_percent: number;
  memory_percent: number;
  disk: DiskUsage;
  active_cameras_count: number;
}
