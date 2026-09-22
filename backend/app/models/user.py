"""
LocalVision NVR - Kullanıcı ve Yetkilendirme Modeli.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from app.core.constants import UserRole
from app.core.database import Base


class User(Base):
    """Sistem kullanıcıları tablosu."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=True)
    full_name = Column(String(128), nullable=True)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(32), default=UserRole.USER.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Güvenlik ve Giriş Sınırlandırma
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # İzinli Kameralar Listesi (JSON serialized string: örn: "[1, 2]")
    # Boş ise rolü ADMIN veya OPERATOR olanlar hepsini görebilir.
    allowed_camera_ids_json = Column(Text, default="[]", nullable=False)

    # Tercihler (JSON: görünüm ızgarası, favori kameralar vs.)
    preferences_json = Column(Text, default="{}", nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def allowed_camera_ids(self) -> list[int]:
        try:
            return json.loads(self.allowed_camera_ids_json or "[]")
        except Exception:
            return []

    @allowed_camera_ids.setter
    def allowed_camera_ids(self, values: list[int]):
        self.allowed_camera_ids_json = json.dumps(values)
