"""
LocalVision NVR - Olay (Event) Veritabanı Modeli.
İnsan, araç, hareket, çizgi ihlali ve bölge ihlali olaylarını saklar.
Gizlilik: Asla yüz verisi veya kişi adı saklanmaz.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from app.core.constants import EventType
from app.core.database import Base


class Event(Base):
    """Algılanan güvenlik olayları tablosu."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), index=True, nullable=False)
    camera_name = Column(String(128), nullable=False)

    event_type = Column(String(32), index=True, nullable=False)  # EventType enum
    confidence = Column(Float, default=0.0, nullable=False)
    
    # Geçici anonim takip ID'si (yalnızca anlık hareket analizi için, kalıcı biyometrik profil DEĞİLDİR)
    temporary_track_id = Column(Integer, nullable=True)

    # Dosya yolları (Küçük resim ve video kesiti)
    snapshot_path = Column(String(512), nullable=True)
    video_clip_path = Column(String(512), nullable=True)

    # Ek bağlam (Algılanan koordinatlar: [x1, y1, x2, y2], bölge adı, kural adı)
    details_json = Column(Text, default="{}", nullable=False)

    # Yer imi ve koruma
    is_bookmarked = Column(Boolean, default=False, index=True, nullable=False)
    bookmark_note = Column(String(256), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False)

    @property
    def details(self) -> Dict[str, Any]:
        try:
            return json.loads(self.details_json or "{}")
        except Exception:
            return {}

    @details.setter
    def details(self, value: Dict[str, Any]):
        self.details_json = json.dumps(value)
