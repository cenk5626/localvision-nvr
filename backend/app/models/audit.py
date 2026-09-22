"""
LocalVision NVR - Denetim Günlüğü (Audit Log) Modeli.
Tüm yönetim, dışa aktarma, indirme, silme ve yetki değişikliklerini kaydeder.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.core.constants import AuditAction
from app.core.database import Base


class AuditLog(Base):
    """Sistem denetim günlüğü tablosu."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(64), index=True, nullable=False)

    action = Column(String(64), index=True, nullable=False)  # AuditAction enum
    resource_type = Column(String(64), nullable=True)        # "camera", "recording", "user" vb.
    resource_id = Column(String(64), nullable=True)

    details_json = Column(Text, default="{}", nullable=False)
    ip_address = Column(String(64), nullable=True)

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
