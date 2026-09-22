"""
LocalVision NVR - Depolama ve Yedekleme Politikası Modeli.
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from app.core.constants import SystemDefaults
from app.core.database import Base


class StoragePolicy(Base):
    """Depolama, saklama süresi ve NAS yedekleme ayarları."""
    __tablename__ = "storage_policies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Genel Saklama Politikası
    retention_days = Column(Integer, default=SystemDefaults.DEFAULT_RETENTION_DAYS, nullable=False)
    max_disk_usage_gb = Column(Integer, default=500, nullable=False)
    min_free_disk_percent = Column(Integer, default=SystemDefaults.MIN_FREE_DISK_PERCENT, nullable=False)
    auto_prune_enabled = Column(Boolean, default=True, nullable=False)

    # NAS Yedekleme Politikası
    nas_backup_enabled = Column(Boolean, default=False, nullable=False)
    nas_mount_path = Column(String(512), nullable=True)  # "\\\\nas\\nvr_backup" veya "/mnt/nas"
    nas_backup_schedule = Column(String(64), default="daily", nullable=False)  # "daily", "weekly"
    nas_keep_backup_count = Column(Integer, default=7, nullable=False)

    last_backup_at = Column(DateTime(timezone=True), nullable=True)
    last_prune_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
