"""
LocalVision NVR - Kamera Veritabanı Modeli.
RTSP, ONVIF ve Yerel PC Web Kamerası (Webcam Index) kaynaklarını destekler.
Kamera parolaları AES-256-GCM ile şifreli tutulur.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.core.constants import (
    CameraSourceType,
    CameraStatus,
    RecordingMode,
    SystemDefaults,
    SystemThresholds,
)
from app.core.database import Base
from app.core.security import security


class Camera(Base):
    """IP Kamera ve Yerel Kamera Tanımları."""
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(String(256), nullable=True)

    # Bağlantı Türü ve Parametreleri
    source_type = Column(String(32), default=CameraSourceType.RTSP.value, nullable=False)
    rtsp_url = Column(String(512), nullable=True)
    webcam_index = Column(Integer, default=0, nullable=False)  # PC kamerası indeksi (0, 1..)
    onvif_host = Column(String(128), nullable=True)
    onvif_port = Column(Integer, default=SystemDefaults.DEFAULT_ONVIF_PORT, nullable=True)
    username = Column(String(128), nullable=True)
    encrypted_password = Column(Text, nullable=True)  # AES-GCM ile şifrelenmiş parola

    # Durum ve Sağlık Metrikleri
    status = Column(String(32), default=CameraStatus.OFFLINE.value, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String(512), nullable=True)

    # Video Akış Özellikleri
    fps = Column(Integer, default=SystemDefaults.DEFAULT_LIVE_FPS, nullable=False)
    width = Column(Integer, default=1280, nullable=False)
    height = Column(Integer, default=720, nullable=False)
    bitrate_kbps = Column(Integer, default=2048, nullable=True)
    codec = Column(String(32), default="h264", nullable=False)

    # Kayıt Politikası
    recording_mode = Column(String(32), default=RecordingMode.CONTINUOUS.value, nullable=False)
    retention_days = Column(Integer, default=SystemDefaults.DEFAULT_RETENTION_DAYS, nullable=False)
    quota_gb = Column(Integer, default=SystemDefaults.DEFAULT_CAMERA_QUOTA_GB, nullable=False)

    # Yapay Zeka ve Algılama Yapılandırması
    detection_enabled = Column(Boolean, default=True, nullable=False)
    detection_fps = Column(Integer, default=SystemDefaults.DEFAULT_AI_FPS, nullable=False)
    confidence_threshold = Column(Float, default=SystemThresholds.DEFAULT_AI_CONFIDENCE, nullable=False)
    motion_sensitivity = Column(Float, default=SystemThresholds.DEFAULT_MOTION_SENSITIVITY, nullable=False)
    max_dwell_seconds = Column(Integer, default=SystemDefaults.MAX_DWELL_SECONDS, nullable=False)

    # İleri Düzey Kurallar (JSON formatında)
    # roi_polygons: [{"name": "Giriş Kapısı", "points": [[x1,y1], [x2,y2], ...]}]
    roi_polygons_json = Column(Text, default="[]", nullable=False)
    # tripwires: [{"name": "Çit Çizgisi", "line": [[x1,y1], [x2,y2]], "direction": "both"}]
    tripwires_json = Column(Text, default="[]", nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # ------------------------------------------------------------------------
    # Şifreli Parola Getter / Setter
    # ------------------------------------------------------------------------
    def set_password(self, plain_password: str) -> None:
        """Kamera parolasını AES-256-GCM ile şifreleyerek atar."""
        if plain_password:
            self.encrypted_password = security.encrypt_secret(plain_password)
        else:
            self.encrypted_password = ""

    def get_password(self) -> str:
        """Kamera parolasını güvenle çözer."""
        if not self.encrypted_password:
            return ""
        try:
            return security.decrypt_secret(self.encrypted_password)
        except Exception:
            return ""

    @property
    def roi_polygons(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.roi_polygons_json or "[]")
        except Exception:
            return []

    @roi_polygons.setter
    def roi_polygons(self, value: List[Dict[str, Any]]):
        self.roi_polygons_json = json.dumps(value)

    @property
    def tripwires(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.tripwires_json or "[]")
        except Exception:
            return []

    @tripwires.setter
    def tripwires(self, value: List[Dict[str, Any]]):
        self.tripwires_json = json.dumps(value)
