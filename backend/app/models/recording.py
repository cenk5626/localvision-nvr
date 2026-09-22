"""
LocalVision NVR - Video Kayıt Segmenti Modeli.
Segmentli video dosyalarının indeksini ve saklama durumunu yönetir.
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, BigInteger, Column, DateTime, Float, ForeignKey, Integer, String
from app.core.constants import RecordingMode
from app.core.database import Base


class Recording(Base):
    """Segmentli video kayıtları tablosu."""
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), index=True, nullable=False)

    file_path = Column(String(512), nullable=False)
    file_name = Column(String(256), nullable=False)
    file_size_bytes = Column(BigInteger, default=0, nullable=False)
    duration_seconds = Column(Float, default=0.0, nullable=False)

    start_time = Column(DateTime(timezone=True), index=True, nullable=False)
    end_time = Column(DateTime(timezone=True), index=True, nullable=True)

    recording_mode = Column(String(32), default=RecordingMode.CONTINUOUS.value, nullable=False)
    has_ai_event = Column(Boolean, default=False, index=True, nullable=False)

    # Koruma Politikası: Yer imli kayıtlar otomatik budamada ASLA silinmez!
    is_bookmarked = Column(Boolean, default=False, index=True, nullable=False)
    is_protected = Column(Boolean, default=False, index=True, nullable=False)

    # Bütünlük ve delil doğrulama özeti (SHA-256)
    sha256_hash = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
