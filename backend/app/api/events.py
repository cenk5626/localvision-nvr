"""
LocalVision NVR - Olay Merkezi API'si (Events API).
- İnsan, araç, bölge ve çizgi ihlali olaylarını listeleme ve filtreleme
- Olay anlık görüntüleri (JPEG) ve video klipleri (MP4) sunumu
- Olay yer imleri (Bookmark) ve koruma
"""

from datetime import datetime
import json
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_camera_access, get_current_user
from app.core.database import get_db
from app.models.event import Event
from app.models.user import User

router = APIRouter(prefix="/api/events", tags=["Olay Merkezi"])


class BookmarkRequest(BaseModel):
    is_bookmarked: bool
    bookmark_note: Optional[str] = None


@router.get("")
async def list_events(
    camera_id: Optional[int] = None,
    event_type: Optional[str] = None,
    is_bookmarked: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Filtrelenmiş olay listesini ve küçük önizleme bağlantılarını döner."""
    stmt = select(Event).order_by(Event.created_at.desc())

    if camera_id:
        if not check_camera_access(current_user, camera_id):
            raise HTTPException(status_code=403, detail="Bu kameranın olaylarını görme yetkiniz yok.")
        stmt = stmt.where(Event.camera_id == camera_id)

    if event_type:
        stmt = stmt.where(Event.event_type == event_type)

    if is_bookmarked is not None:
        stmt = stmt.where(Event.is_bookmarked == is_bookmarked)

    if start_date:
        stmt = stmt.where(Event.created_at >= start_date)

    if end_date:
        stmt = stmt.where(Event.created_at <= end_date)

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    events = result.scalars().all()

    # Kullanıcı izin filtrelemesi
    user_allowed_cams = current_user.allowed_camera_ids
    is_admin_or_op = current_user.role in ("admin", "operator")

    filtered = []
    for ev in events:
        if not is_admin_or_op and user_allowed_cams and ev.camera_id not in user_allowed_cams:
            continue

        filtered.append({
            "id": ev.id,
            "camera_id": ev.camera_id,
            "camera_name": ev.camera_name,
            "event_type": ev.event_type,
            "confidence": ev.confidence,
            "temporary_track_id": ev.temporary_track_id,
            "has_snapshot": bool(ev.snapshot_path and Path(ev.snapshot_path).exists()),
            "has_clip": bool(ev.video_clip_path and Path(ev.video_clip_path).exists()),
            "snapshot_url": f"/api/events/{ev.id}/snapshot" if ev.snapshot_path else None,
            "clip_url": f"/api/events/{ev.id}/clip" if ev.video_clip_path else None,
            "is_bookmarked": ev.is_bookmarked,
            "bookmark_note": ev.bookmark_note,
            "details": ev.details,
            "created_at": ev.created_at.isoformat()
        })

    return filtered


@router.get("/{event_id}")
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Tek bir olayın ayrıntılarını döndürür."""
    stmt = select(Event).where(Event.id == event_id)
    result = await db.execute(stmt)
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Olay bulunamadı.")

    if not check_camera_access(current_user, ev.camera_id):
        raise HTTPException(status_code=403, detail="Bu olaya erişim yetkiniz yok.")

    return {
        "id": ev.id,
        "camera_id": ev.camera_id,
        "camera_name": ev.camera_name,
        "event_type": ev.event_type,
        "confidence": ev.confidence,
        "snapshot_url": f"/api/events/{ev.id}/snapshot" if ev.snapshot_path else None,
        "clip_url": f"/api/events/{ev.id}/clip" if ev.video_clip_path else None,
        "is_bookmarked": ev.is_bookmarked,
        "bookmark_note": ev.bookmark_note,
        "details": ev.details,
        "created_at": ev.created_at.isoformat()
    }


@router.post("/{event_id}/bookmark")
async def toggle_event_bookmark(
    event_id: int,
    payload: BookmarkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Olayı yer imine ekler veya kaldırır (silinmeye karşı koruma)."""
    stmt = select(Event).where(Event.id == event_id)
    result = await db.execute(stmt)
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Olay bulunamadı.")

    ev.is_bookmarked = payload.is_bookmarked
    if payload.bookmark_note is not None:
        ev.bookmark_note = payload.bookmark_note

    await db.commit()
    return {"status": "ok", "is_bookmarked": ev.is_bookmarked}


@router.get("/{event_id}/snapshot")
async def get_event_snapshot(
    event_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Olayın JPEG önizleme resmini sunar."""
    stmt = select(Event).where(Event.id == event_id)
    result = await db.execute(stmt)
    ev = result.scalar_one_or_none()
    if not ev or not ev.snapshot_path:
        raise HTTPException(status_code=404, detail="Snapshot bulunamadı.")

    snap_file = Path(ev.snapshot_path)
    if not snap_file.exists():
        raise HTTPException(status_code=404, detail="Snapshot dosyası diskte bulunamadı.")

    return FileResponse(str(snap_file), media_type="image/jpeg")


@router.get("/{event_id}/clip")
async def get_event_clip(
    event_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Olayın MP4 video klibini sunar."""
    stmt = select(Event).where(Event.id == event_id)
    result = await db.execute(stmt)
    ev = result.scalar_one_or_none()
    if not ev or not ev.video_clip_path:
        raise HTTPException(status_code=404, detail="Video klibi bulunamadı.")

    clip_file = Path(ev.video_clip_path)
    if not clip_file.exists():
        raise HTTPException(status_code=404, detail="Klip dosyası diskte bulunamadı.")

    return FileResponse(
        str(clip_file),
        media_type="video/mp4",
        filename=clip_file.name
    )
