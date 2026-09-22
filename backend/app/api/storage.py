"""
LocalVision NVR - Depolama, Kota ve NAS Yedekleme API'si.
- Disk sağlığı, toplam ve boş alan analizi
- Saklama politikası (Retention policy) yönetimi
- Anlık otomatik budama tetikleme
- NAS (SMB/NFS) yedekleme senkronizasyonu
"""

import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.config import settings
from app.core.constants import AuditAction, SystemDefaults, UserRole
from app.core.database import get_db
from app.models.audit import AuditLog
from app.models.storage_policy import StoragePolicy
from app.models.user import User
from app.services.backup_svc import backup_service
from app.services.retention_svc import retention_service

router = APIRouter(prefix="/api/storage", tags=["Depolama & Yedekleme"])


class PolicyUpdateRequest(BaseModel):
    retention_days: int
    max_disk_usage_gb: int
    min_free_disk_percent: int
    auto_prune_enabled: bool
    nas_backup_enabled: bool
    nas_mount_path: Optional[str] = None
    nas_backup_schedule: str = "daily"


class NasBackupRequest(BaseModel):
    nas_path: str


@router.get("/status")
async def get_storage_status(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OPERATOR])),
    db: AsyncSession = Depends(get_db)
):
    """Disk kullanım durumunu ve kamera bazlı tüketimi döndürür."""
    disk_info = retention_service.get_disk_usage()

    # Kamera bazlı disk kullanımını tara
    camera_usages = []
    if settings.STORAGE_DIR.exists():
        for cam_dir in settings.STORAGE_DIR.iterdir():
            if cam_dir.is_dir() and cam_dir.name.startswith("camera_"):
                try:
                    cam_id = int(cam_dir.name.split("_")[1])
                    # Klasör boyutunu hesapla
                    total_cam_bytes = sum(f.stat().st_size for f in cam_dir.rglob("*.mp4") if f.is_file())
                    camera_usages.append({
                        "camera_id": cam_id,
                        "used_mb": round(total_cam_bytes / (1024 ** 2), 2),
                        "used_gb": round(total_cam_bytes / (1024 ** 3), 2)
                    })
                except Exception:
                    pass

    return {
        "disk": disk_info,
        "cameras": camera_usages,
        "storage_path": str(settings.STORAGE_DIR.resolve())
    }


@router.get("/policy")
async def get_storage_policy(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OPERATOR])),
    db: AsyncSession = Depends(get_db)
):
    """Mevcut saklama ve yedekleme politikasını döner."""
    stmt = select(StoragePolicy).order_by(StoragePolicy.id.asc())
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()

    if not policy:
        # Varsayılan politika oluştur
        policy = StoragePolicy()
        db.add(policy)
        await db.commit()
        await db.refresh(policy)

    return {
        "retention_days": policy.retention_days,
        "max_disk_usage_gb": policy.max_disk_usage_gb,
        "min_free_disk_percent": policy.min_free_disk_percent,
        "auto_prune_enabled": policy.auto_prune_enabled,
        "nas_backup_enabled": policy.nas_backup_enabled,
        "nas_mount_path": policy.nas_mount_path,
        "nas_backup_schedule": policy.nas_backup_schedule,
        "last_backup_at": policy.last_backup_at.isoformat() if policy.last_backup_at else None,
        "last_prune_at": policy.last_prune_at.isoformat() if policy.last_prune_at else None
    }


@router.put("/policy")
async def update_storage_policy(
    payload: PolicyUpdateRequest,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Saklama ve yedekleme politikasını günceller."""
    stmt = select(StoragePolicy).order_by(StoragePolicy.id.asc())
    result = await db.execute(stmt)
    policy = result.scalar_one_or_none()
    if not policy:
        policy = StoragePolicy()
        db.add(policy)

    for k, v in payload.model_dump().items():
        setattr(policy, k, v)

    await db.commit()

    # Denetim günlüğü
    client_ip = request.client.host if request.client else "unknown"
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=AuditAction.SETTINGS_CHANGE.value,
        resource_type="storage_policy",
        details_json=json.dumps(payload.model_dump()),
        ip_address=client_ip
    )
    db.add(audit)
    await db.commit()

    return {"status": "ok", "message": "Depolama politikası güncellendi."}


@router.post("/prune-now")
async def trigger_prune(
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Manuel olarak eski ve süresi dolmuş kayıtları temizleme döngüsü başlatır."""
    deleted_count, freed_bytes = await retention_service.run_retention_cycle()
    return {
        "status": "ok",
        "deleted_files": deleted_count,
        "freed_mb": round(freed_bytes / (1024 ** 2), 2),
        "message": f"Temizlik tamamlandı: {deleted_count} eski dosya silindi."
    }


@router.post("/backup-nas")
async def trigger_nas_backup(
    payload: NasBackupRequest,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Kayıtları belirtilen NAS klasörüne senkronize eder."""
    try:
        res = backup_service.sync_to_nas(payload.nas_path)

        client_ip = request.client.host if request.client else "unknown"
        audit = AuditLog(
            user_id=current_user.id,
            username=current_user.username,
            action=AuditAction.BACKUP_TRIGGER.value,
            resource_type="nas_backup",
            details_json=json.dumps(res),
            ip_address=client_ip
        )
        db.add(audit)
        await db.commit()

        return {
            "status": "ok",
            "message": f"NAS yedeklemesi tamamlandı: {res['backed_up_files']} dosya aktarıldı ({res['total_mb']} MB).",
            "details": res
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Yedekleme hatası: {str(e)}")
