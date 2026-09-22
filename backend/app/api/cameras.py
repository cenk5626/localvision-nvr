"""
LocalVision NVR - Kamera Yönetimi ve Canlı Akış API'si.
- RTSP, ONVIF ve PC Web Kamerası desteği
- Canlı Düşük Gecikmeli MJPEG Akışı (/live.mjpeg)
- Anlık kare yakalama (/snapshot)
- Bağlantı test aracı ve otomatik donanım keşfi
"""

import io
import json
import logging
from typing import Any, Dict, List, Optional
import cv2
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import check_camera_access, get_current_user, require_roles
from app.core.constants import (
    AuditAction,
    CameraSourceType,
    CameraStatus,
    RecordingMode,
    SystemDefaults,
    SystemThresholds,
    UserRole,
)
from app.core.database import get_db
from app.models.audit import AuditLog
from app.models.camera import Camera
from app.models.user import User
from app.services.camera_manager import camera_manager
from app.services.onvif_discovery import onvif_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cameras", tags=["Kameralar"])


# ----------------------------------------------------------------------------
# Pydantic Şemaları
# ----------------------------------------------------------------------------
class CameraCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    source_type: str = CameraSourceType.RTSP.value
    rtsp_url: Optional[str] = None
    webcam_index: int = 0
    onvif_host: Optional[str] = None
    onvif_port: int = SystemDefaults.DEFAULT_ONVIF_PORT
    username: Optional[str] = None
    password: Optional[str] = None
    fps: int = SystemDefaults.DEFAULT_LIVE_FPS
    recording_mode: str = RecordingMode.CONTINUOUS.value
    retention_days: int = SystemDefaults.DEFAULT_RETENTION_DAYS
    quota_gb: int = SystemDefaults.DEFAULT_CAMERA_QUOTA_GB
    detection_enabled: bool = True
    detection_fps: int = SystemDefaults.DEFAULT_AI_FPS
    confidence_threshold: float = SystemThresholds.DEFAULT_AI_CONFIDENCE
    max_dwell_seconds: int = SystemDefaults.MAX_DWELL_SECONDS
    roi_polygons: List[Dict[str, Any]] = []
    tripwires: List[Dict[str, Any]] = []


class CameraUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    source_type: Optional[str] = None
    rtsp_url: Optional[str] = None
    webcam_index: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    fps: Optional[int] = None
    recording_mode: Optional[str] = None
    retention_days: Optional[int] = None
    quota_gb: Optional[int] = None
    detection_enabled: Optional[bool] = None
    detection_fps: Optional[int] = None
    confidence_threshold: Optional[float] = None
    max_dwell_seconds: Optional[int] = None
    roi_polygons: Optional[List[Dict[str, Any]]] = None
    tripwires: Optional[List[Dict[str, Any]]] = None
    is_enabled: Optional[bool] = None


class TestConnectionRequest(BaseModel):
    source_type: str
    rtsp_url: Optional[str] = None
    webcam_index: int = 0
    username: Optional[str] = None
    password: Optional[str] = None


# ----------------------------------------------------------------------------
# Kamera Listeleme ve Detay
# ----------------------------------------------------------------------------
@router.get("")
async def list_cameras(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Yetkili olunan tüm kameraları ve canlı sağlık durumlarını döndürür."""
    stmt = select(Camera).order_by(Camera.id.asc())
    result = await db.execute(stmt)
    cameras = result.scalars().all()

    filtered = []
    for cam in cameras:
        if not check_camera_access(current_user, cam.id):
            continue

        # Canlı örnekten anlık durum metriklerini al
        instance = camera_manager.get_instance(cam.id)
        live_status = instance.capture.status if instance else CameraStatus.OFFLINE
        actual_fps = instance.capture.actual_fps if instance else 0.0
        width = instance.capture.actual_width if instance else cam.width
        height = instance.capture.actual_height if instance else cam.height

        filtered.append({
            "id": cam.id,
            "name": cam.name,
            "description": cam.description,
            "source_type": cam.source_type,
            "rtsp_url": cam.rtsp_url,
            "webcam_index": cam.webcam_index,
            "status": live_status,
            "is_enabled": cam.is_enabled,
            "fps": cam.fps,
            "actual_fps": actual_fps,
            "width": width,
            "height": height,
            "codec": cam.codec,
            "recording_mode": cam.recording_mode,
            "detection_enabled": cam.detection_enabled,
            "roi_polygons": cam.roi_polygons,
            "tripwires": cam.tripwires,
            "created_at": cam.created_at.isoformat()
        })

    return filtered


@router.get("/discover-webcams")
async def discover_webcams(current_user: User = Depends(get_current_user)):
    """Bilgisayara bağlı yerel web kameralarını tespit eder."""
    webcams = camera_manager.detect_available_webcams()
    return {
        "count": len(webcams),
        "webcams": webcams
    }


@router.get("/discover-onvif")
async def discover_onvif(current_user: User = Depends(get_current_user)):
    """Yerel ağdaki ONVIF kameraları WS-Discovery ile bulur."""
    discovered = onvif_service.discover_cameras(timeout_seconds=2.5)
    return {
        "count": len(discovered),
        "cameras": discovered
    }


@router.post("/test-connection")
async def test_camera_connection(payload: TestConnectionRequest):
    """
    Kaydetmeden önce kamera akış bağlantısını test eder.
    Çözünürlük, FPS ve kare alım başarısını döndürür.
    """
    if payload.source_type == CameraSourceType.WEBCAM.value:
        cap = cv2.VideoCapture(payload.webcam_index, cv2.CAP_DSHOW)
    elif payload.source_type == CameraSourceType.RTSP.value:
        if not payload.rtsp_url:
            raise HTTPException(status_code=400, detail="RTSP URL belirtilmedi.")
        url = payload.rtsp_url
        if payload.username and payload.password and "@" not in url:
            # URL'e kimlik bilgilerini ekle
            prefix = "rtsp://"
            if url.startswith(prefix):
                url = f"{prefix}{payload.username}:{payload.password}@{url[len(prefix):]}"
        cap = cv2.VideoCapture(url)
    else:
        raise HTTPException(status_code=400, detail="Geçersiz kaynak türü.")

    if not cap.isOpened():
        return {
            "success": False,
            "error": "Kamera akışına bağlanılamadı. Lütfen URL, indeks veya kimlik bilgilerini kontrol edin."
        }

    ret, frame = cap.read()
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()

    if not ret or frame is None:
        return {
            "success": False,
            "error": "Kamera açıldı fakat kare okunamadı."
        }

    return {
        "success": True,
        "width": w,
        "height": h,
        "message": f"Bağlantı başarılı! Algılanan çözünürlük: {w}x{h}"
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_camera(
    payload: CameraCreateRequest,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OPERATOR])),
    db: AsyncSession = Depends(get_db)
):
    """Yeni kamera ekler ve akışı başlatır."""
    client_ip = request.client.host if request.client else "unknown"

    new_camera = Camera(
        name=payload.name,
        description=payload.description,
        source_type=payload.source_type,
        rtsp_url=payload.rtsp_url,
        webcam_index=payload.webcam_index,
        onvif_host=payload.onvif_host,
        onvif_port=payload.onvif_port,
        username=payload.username,
        fps=payload.fps,
        recording_mode=payload.recording_mode,
        retention_days=payload.retention_days,
        quota_gb=payload.quota_gb,
        detection_enabled=payload.detection_enabled,
        detection_fps=payload.detection_fps,
        confidence_threshold=payload.confidence_threshold,
        max_dwell_seconds=payload.max_dwell_seconds,
        roi_polygons_json=json.dumps(payload.roi_polygons),
        tripwires_json=json.dumps(payload.tripwires)
    )

    if payload.password:
        new_camera.set_password(payload.password)

    db.add(new_camera)
    await db.commit()
    await db.refresh(new_camera)

    # Canlı yöneticiye ekle
    camera_manager.add_camera_instance(new_camera)

    # Denetim günlüğüne yaz
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=AuditAction.CAMERA_CREATE.value,
        resource_type="camera",
        resource_id=str(new_camera.id),
        details_json=json.dumps({"name": new_camera.name, "source_type": new_camera.source_type}),
        ip_address=client_ip
    )
    db.add(audit)
    await db.commit()

    return {"status": "ok", "id": new_camera.id, "message": "Kamera başarıyla oluşturuldu."}


@router.get("/{camera_id}")
async def get_camera(
    camera_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Kamera detaylarını döndürür."""
    if not check_camera_access(current_user, camera_id):
        raise HTTPException(status_code=403, detail="Bu kameraya erişim yetkiniz yok.")

    stmt = select(Camera).where(Camera.id == camera_id)
    result = await db.execute(stmt)
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(status_code=404, detail="Kamera bulunamadı.")

    return {
        "id": cam.id,
        "name": cam.name,
        "description": cam.description,
        "source_type": cam.source_type,
        "rtsp_url": cam.rtsp_url,
        "webcam_index": cam.webcam_index,
        "username": cam.username,
        "fps": cam.fps,
        "recording_mode": cam.recording_mode,
        "retention_days": cam.retention_days,
        "quota_gb": cam.quota_gb,
        "detection_enabled": cam.detection_enabled,
        "detection_fps": cam.detection_fps,
        "confidence_threshold": cam.confidence_threshold,
        "max_dwell_seconds": cam.max_dwell_seconds,
        "roi_polygons": cam.roi_polygons,
        "tripwires": cam.tripwires,
        "is_enabled": cam.is_enabled,
        "status": cam.status
    }


@router.put("/{camera_id}")
async def update_camera(
    camera_id: int,
    payload: CameraUpdateRequest,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OPERATOR])),
    db: AsyncSession = Depends(get_db)
):
    """Kamera ayarlarını günceller."""
    client_ip = request.client.host if request.client else "unknown"

    stmt = select(Camera).where(Camera.id == camera_id)
    result = await db.execute(stmt)
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(status_code=404, detail="Kamera bulunamadı.")

    update_data = payload.model_dump(exclude_unset=True)
    if "password" in update_data:
        pw = update_data.pop("password")
        if pw:
            cam.set_password(pw)

    if "roi_polygons" in update_data:
        cam.roi_polygons = update_data.pop("roi_polygons")

    if "tripwires" in update_data:
        cam.tripwires = update_data.pop("tripwires")

    for k, v in update_data.items():
        setattr(cam, k, v)

    await db.commit()
    await db.refresh(cam)

    # Canlı örneği yeniden yükle
    camera_manager.add_camera_instance(cam)

    # Denetim günlüğü
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=AuditAction.CAMERA_UPDATE.value,
        resource_type="camera",
        resource_id=str(cam.id),
        details_json=json.dumps({"updated_keys": list(payload.model_dump(exclude_unset=True).keys())}),
        ip_address=client_ip
    )
    db.add(audit)
    await db.commit()

    return {"status": "ok", "message": "Kamera güncellendi."}


@router.delete("/{camera_id}")
async def delete_camera(
    camera_id: int,
    request: Request,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Kamerayı siler ve akışını durdurur."""
    client_ip = request.client.host if request.client else "unknown"

    stmt = select(Camera).where(Camera.id == camera_id)
    result = await db.execute(stmt)
    cam = result.scalar_one_or_none()
    if not cam:
        raise HTTPException(status_code=404, detail="Kamera bulunamadı.")

    cam_name = cam.name
    camera_manager.remove_camera_instance(camera_id)
    await db.delete(cam)
    await db.commit()

    # Denetim günlüğü
    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=AuditAction.CAMERA_DELETE.value,
        resource_type="camera",
        resource_id=str(camera_id),
        details_json=json.dumps({"name": cam_name}),
        ip_address=client_ip
    )
    db.add(audit)
    await db.commit()

    return {"status": "ok", "message": f"{cam_name} kamerası silindi."}


# ----------------------------------------------------------------------------
# Canlı Video ve Anlık Görüntü (MJPEG Stream & Snapshot)
# ----------------------------------------------------------------------------
@router.get("/{camera_id}/live.mjpeg")
async def get_live_mjpeg(
    camera_id: int,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    HTML <img> etiketi ve Canvas için düşük gecikmeli, kesintisiz MJPEG akışı sağlar.
    Tarayıcı bağlantısı koptuğunda sunucu tarafında kaynak otomatik serbest kalır.
    """
    # Token doğrulaması
    if token:
        try:
            security.decode_access_token(token)
        except Exception:
            raise HTTPException(status_code=401, detail="Geçersiz jeton.")

    instance = camera_manager.get_instance(camera_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Kamera akışı aktif değil veya bulunamadı.")

    return StreamingResponse(
        camera_manager.generate_mjpeg_stream(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/{camera_id}/snapshot")
async def get_camera_snapshot(
    camera_id: int,
    current_user: User = Depends(get_current_user)
):
    """Kameranın en son karesini tek bir JPEG görüntüsü olarak döndürür."""
    if not check_camera_access(current_user, camera_id):
        raise HTTPException(status_code=403, detail="Yetkiniz yok.")

    instance = camera_manager.get_instance(camera_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Kamera aktif değil.")

    frame = instance.capture.ring_buffer.get_latest_frame()
    if frame is None:
        raise HTTPException(status_code=503, detail="Henüz görüntü alınamadı.")

    ret, buffer = cv2.imencode(".jpg", frame)
    if not ret:
        raise HTTPException(status_code=500, detail="Görüntü kodlanamadı.")

    return Response(content=buffer.tobytes(), media_type="image/jpeg")
