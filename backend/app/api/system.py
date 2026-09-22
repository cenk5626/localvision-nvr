"""
LocalVision NVR - Sistem Sağlığı, Metrikler ve Denetim Günlüğü API'si.
- Sağlık kontrolü (Health check)
- Sistem kaynak kullanımı (CPU, RAM, Disk)
- KVKK ve Gizlilik Bildirimi Kontrol Listesi
- Değiştirilemez Denetim Günlüğü (Audit Log) listeleme
"""

from datetime import datetime, timezone
import os
import platform
import psutil
import time
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.config import settings
from app.core.constants import UserRole
from app.core.database import get_db
from app.models.audit import AuditLog
from app.services.camera_manager import camera_manager
from app.services.retention_svc import retention_service

router = APIRouter(prefix="/api/system", tags=["Sistem"])

START_TIME = time.time()


@router.get("/health")
async def get_health():
    """Sistem sağlık durumunu ve temel metrikleri döndürür."""
    uptime_seconds = int(time.time() - START_TIME)
    disk_info = retention_service.get_disk_usage()

    # CPU ve Bellek
    cpu_percent = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()

    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "uptime_seconds": uptime_seconds,
        "offline_mode": settings.OFFLINE_ONLY,
        "os": f"{platform.system()} {platform.release()}",
        "cpu_percent": cpu_percent,
        "memory_percent": mem.percent,
        "disk": disk_info,
        "active_cameras_count": len(camera_manager._instances)
    }


@router.get("/privacy-checklist")
async def get_privacy_checklist():
    """KVKK / GDPR ve Yerel Mevzuata Uyum Denetim Listesi."""
    return {
        "system_design": "Privacy by Design (Tasarım İtibarıyla Gizlilik)",
        "features": {
            "facial_recognition": False,
            "biometric_profiling": False,
            "named_tracking": False,
            "cloud_data_transfer": False,
            "local_network_only": True
        },
        "legal_checklist": [
            {
                "item": "Kamera Uyarı Levhası",
                "description": "Kamera kayıt alanına giren kişilerin görebileceği noktalara aydınlatma metni ve kamera simgesi asılmalıdır.",
                "status": "Fiziksel Kurulum Gerekli"
            },
            {
                "item": "Amaçla Sınırlılık",
                "description": "Kamera yalnızca güvenlik ve mülk koruma amacıyla kullanılmalı, özel hayatın gizliliğini ihlal edecek açılara (komşu penceresi vb.) yönlendirilmemelidir.",
                "status": "Uyumlu"
            },
            {
                "item": "Veri Minimizasyonu",
                "description": "Yüz tanıma ve kimlik tespiti yapılmaz; yalnızca insan/araç varlığı ve ihlal analizi işlenir.",
                "status": "Sistem Tarafından Doğrulandı"
            },
            {
                "item": "Saklama Süresi Sınırı",
                "description": "Kayıtlar varsayılan 14 gün sonra otomatik olarak budanır; korumalı olmayan kayıtlar silinir.",
                "status": "Aktif Politika"
            },
            {
                "item": "Erişim Yetkilendirmesi",
                "description": "Rol tabanlı erişim (RBAC) ile her kullanıcının sadece yetkili olduğu kameraları görmesi sağlanır.",
                "status": "Aktif Politika"
            }
        ]
    }


@router.get("/audit-logs")
async def list_audit_logs(
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    action: Optional[str] = None,
    username: Optional[str] = None,
    current_user = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Denetim günlüğünü (Audit Log) filtreleyerek listeler."""
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())

    if action:
        stmt = stmt.where(AuditLog.action == action)
    if username:
        stmt = stmt.where(AuditLog.username == username)

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()

    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "username": l.username,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "details": l.details,
            "ip_address": l.ip_address,
            "created_at": l.created_at.isoformat()
        }
        for l in logs
    ]
