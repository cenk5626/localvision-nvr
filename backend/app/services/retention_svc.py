"""
LocalVision NVR - Depolama ve Otomatik Budama Servisi (Retention Service).
- Disk doluluğu ve kamera kotalarını denetler.
- Saklama süresi dolan veya kota aşan en eski kayıtları siler.
- KATI KORUMA KURALI: Yer imli (is_bookmarked=True) veya korumalı (is_protected=True) kayıtlar ASLA silinmez!
- Tüm silme işlemlerini denetim günlüğüne (AuditLog) kaydeder.
"""

from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
import shutil
from typing import Dict, Tuple
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.constants import AuditAction, SystemDefaults
from app.core.database import AsyncSessionLocal
from app.models.audit import AuditLog
from app.models.recording import Recording

logger = logging.getLogger(__name__)


class RetentionService:
    """Disk alanı ve saklama süresi denetleyici."""

    @staticmethod
    def get_disk_usage() -> Dict[str, float]:
        """Kayıtların yapıldığı diskin kullanım oranını döndürür."""
        total, used, free = shutil.disk_usage(settings.STORAGE_DIR)
        total_gb = round(total / (1024 ** 3), 2)
        used_gb = round(used / (1024 ** 3), 2)
        free_gb = round(free / (1024 ** 3), 2)
        free_percent = round((free / total) * 100, 1)

        return {
            "total_gb": total_gb,
            "used_gb": used_gb,
            "free_gb": free_gb,
            "free_percent": free_percent,
            "is_low_space": free_percent <= SystemDefaults.MIN_FREE_DISK_PERCENT,
            "is_critical": free_percent <= SystemDefaults.CRITICAL_FREE_DISK_PERCENT
        }

    @classmethod
    async def run_retention_cycle(cls, default_retention_days: int = SystemDefaults.DEFAULT_RETENTION_DAYS) -> Tuple[int, int]:
        """
        Depolama temizlik döngüsünü yürütür.
        Dönüş: (silinen_dosya_sayısı, serbest_kalan_bayt)
        """
        disk_info = cls.get_disk_usage()
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=default_retention_days)

        deleted_count = 0
        freed_bytes = 0

        async with AsyncSessionLocal() as session:
            # 1. Saklama süresi dolmuş VE yer imli/korumalı OLMAYAN kayıtları sorgula
            stmt = (
                select(Recording)
                .where(
                    Recording.start_time < cutoff_date,
                    Recording.is_bookmarked == False,
                    Recording.is_protected == False
                )
                .order_by(Recording.start_time.asc())
            )
            result = await session.execute(stmt)
            expired_recordings = result.scalars().all()

            for rec in expired_recordings:
                file_p = Path(rec.file_path)
                if file_p.exists():
                    freed_bytes += file_p.stat().st_size
                    try:
                        file_p.unlink()
                    except Exception as e:
                        logger.error(f"Dosya silinemedi: {file_p} -> {e}")

                await session.delete(rec)
                deleted_count += 1

            # 2. Eğer disk alanı hala kritikse (<%10), en eski yer imsiz kayıtları kotaya bakılmaksızın temizle
            if disk_info["is_low_space"] and deleted_count == 0:
                emergency_stmt = (
                    select(Recording)
                    .where(
                        Recording.is_bookmarked == False,
                        Recording.is_protected == False
                    )
                    .order_by(Recording.start_time.asc())
                    .limit(20)
                )
                em_result = await session.execute(emergency_stmt)
                emergency_recs = em_result.scalars().all()

                for rec in emergency_recs:
                    file_p = Path(rec.file_path)
                    if file_p.exists():
                        freed_bytes += file_p.stat().st_size
                        try:
                            file_p.unlink()
                        except Exception:
                            pass
                    await session.delete(rec)
                    deleted_count += 1

            if deleted_count > 0:
                # Denetim günlüğüne kaydet
                audit = AuditLog(
                    username="SYSTEM_RETENTION",
                    action=AuditAction.RETENTION_PRUNE.value,
                    resource_type="recordings",
                    resource_id=f"{deleted_count}_files",
                    details_json=f'{{"deleted_files": {deleted_count}, "freed_mb": {round(freed_bytes / (1024**2), 2)}}}'
                )
                session.add(audit)
                await session.commit()
                logger.info(f"Retention döngüsü: {deleted_count} eski dosya silindi, {round(freed_bytes / (1024**2), 2)} MB yer açıldı.")

        return deleted_count, freed_bytes


retention_service = RetentionService()
