"""
LocalVision NVR - Geçmiş Kayıtlar ve Zaman Çizelgesi API'si (Recordings API).
- Segmentli MP4 kayıtlarının zaman çizelgesinde taranması
- HTML5 Video Range Streaming (/stream)
- Güvenli indirme ve SHA-256 doğrulamalı filigranlı dışa aktarma (/export)
- Denetim günlüğü kaydı
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_camera_access, get_current_user, require_roles
from app.core.constants import AuditAction, UserRole
from app.core.database import get_db
from app.models.audit import AuditLog
from app.models.camera import Camera
from app.models.recording import Recording
from app.models.user import User
from app.services.backup_svc import backup_service

router = APIRouter(prefix="/api/recordings", tags=["Geçmiş Kayıtlar"])


class ExportRequest(BaseModel):
    add_watermark: bool = True
    notes: Optional[str] = None


class RecordingBookmarkRequest(BaseModel):
    is_protected: bool
    is_bookmarked: bool


@router.get("")
async def list_recordings(
    camera_id: int,
    date: Optional[str] = None,  # "YYYY-MM-DD"
    limit: int = Query(100, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Belirli bir kameranın zaman çizelgesi kayıt segmentlerini listeler."""
    if not check_camera_access(current_user, camera_id):
        raise HTTPException(status_code=403, detail="Bu kameranın kayıtlarını görme yetkiniz yok.")

    stmt = select(Recording).where(Recording.camera_id == camera_id).order_by(Recording.start_time.desc())

    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            stmt = stmt.where(Recording.start_time >= datetime.combine(target_date, datetime.min.time()))
            stmt = stmt.where(Recording.start_time <= datetime.combine(target_date, datetime.max.time()))
        except ValueError:
            raise HTTPException(status_code=400, detail="Tarih formatı YYYY-MM-DD olmalıdır.")

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    recordings = result.scalars().all()

    return [
        {
            "id": r.id,
            "camera_id": r.camera_id,
            "file_name": r.file_name,
            "file_size_mb": round(r.file_size_bytes / (1024 ** 2), 2),
            "duration_seconds": r.duration_seconds,
            "start_time": r.start_time.isoformat(),
            "end_time": r.end_time.isoformat() if r.end_time else None,
            "recording_mode": r.recording_mode,
            "has_ai_event": r.has_ai_event,
            "is_bookmarked": r.is_bookmarked,
            "is_protected": r.is_protected,
            "stream_url": f"/api/recordings/{r.id}/stream",
            "download_url": f"/api/recordings/{r.id}/download"
        }
        for r in recordings
    ]


@router.get("/{recording_id}/stream")
async def stream_recording(
    recording_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Tarayıcıda akıcı oynatma için video dosyasını sunar (HTTP 206 Partial Content destekler)."""
    stmt = select(Recording).where(Recording.id == recording_id)
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")

    file_p = Path(rec.file_path)
    if not file_p.exists():
        raise HTTPException(status_code=404, detail="Video dosyası diskte bulunamadı.")

    return FileResponse(
        str(file_p),
        media_type="video/mp4",
        filename=rec.file_name
    )


@router.get("/{recording_id}/download")
async def download_recording(
    recording_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Kayıt dosyasını orijinal haliyle indirir ve denetim günlüğüne yazar."""
    stmt = select(Recording).where(Recording.id == recording_id)
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")

    if not check_camera_access(current_user, rec.camera_id):
        raise HTTPException(status_code=403, detail="Yetkiniz yok.")

    file_p = Path(rec.file_path)
    if not file_p.exists():
        raise HTTPException(status_code=404, detail="Dosya diskte mevcut değil.")

    # Denetim günlüğü
    client_ip = request.client.host if request.client else "unknown"
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=AuditAction.RECORDING_DOWNLOAD.value,
        resource_type="recording",
        resource_id=str(recording_id),
        details_json=json.dumps({"file_name": rec.file_name, "size_bytes": rec.file_size_bytes}),
        ip_address=client_ip
    )
    db.add(audit)
    await db.commit()

    return FileResponse(
        str(file_p),
        media_type="application/octet-stream",
        filename=rec.file_name
    )


@router.post("/{recording_id}/export")
async def export_recording(
    recording_id: int,
    payload: ExportRequest,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OPERATOR])),
    db: AsyncSession = Depends(get_db)
):
    """Videoya filigran ekler, SHA-256 doğrulama özeti üretir ve dışa aktarır."""
    stmt = select(Recording).where(Recording.id == recording_id)
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")

    cam_stmt = select(Camera).where(Camera.id == rec.camera_id)
    cam_result = await db.execute(cam_stmt)
    cam = cam_result.scalar_one_or_none()
    cam_name = cam.name if cam else f"Camera_{rec.camera_id}"

    export_res = backup_service.export_video(
        source_path=rec.file_path,
        camera_name=cam_name,
        add_watermark=payload.add_watermark,
        notes=payload.notes
    )

    # Denetim günlüğü
    client_ip = request.client.host if request.client else "unknown"
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=AuditAction.RECORDING_EXPORT.value,
        resource_type="recording",
        resource_id=str(recording_id),
        details_json=json.dumps(export_res),
        ip_address=client_ip
    )
    db.add(audit)
    await db.commit()

    return {
        "status": "ok",
        "message": "Video başarıyla dışa aktarıldı ve SHA-256 özeti oluşturuldu.",
        "details": export_res
    }


@router.post("/{recording_id}/bookmark")
async def bookmark_recording(
    recording_id: int,
    payload: RecordingBookmarkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Kaydı korumalı yer imi olarak işaretler (otomatik silinmeyi önler)."""
    stmt = select(Recording).where(Recording.id == recording_id)
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")

    rec.is_protected = payload.is_protected
    rec.is_bookmarked = payload.is_bookmarked
    await db.commit()

    return {
        "status": "ok",
        "is_protected": rec.is_protected,
        "is_bookmarked": rec.is_bookmarked
    }


@router.delete("/{recording_id}")
async def delete_recording(
    recording_id: int,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Kayıt dosyasını ve indeksini kalıcı olarak siler."""
    stmt = select(Recording).where(Recording.id == recording_id)
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")

    file_p = Path(rec.file_path)
    if file_p.exists():
        try:
            file_p.unlink()
        except Exception as e:
            logger.error(f"Dosya silinemedi: {e}")

    await db.delete(rec)

    # Denetim günlüğü
    client_ip = request.client.host if request.client else "unknown"
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=AuditAction.RECORDING_DELETE.value,
        resource_type="recording",
        resource_id=str(recording_id),
        details_json=json.dumps({"file_name": rec.file_name}),
        ip_address=client_ip
    )
    db.add(audit)
    await db.commit()

    return {"status": "ok", "message": "Kayıt dosyası kalıcı olarak silindi."}
