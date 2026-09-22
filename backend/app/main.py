"""
LocalVision NVR - Ana Uygulama Başlangıç Noktası (FastAPI Application).
- Asenkron Lifespan: DB başlatma, kamera yöneticisi, otomatik webcam seed
- CORS ve Güvenlik Başlıkları
- REST ve WebSocket API rotalarının kaydı
- Otomatik ilk kurulum yönetici ve PC web kamerası hazırlığı
"""

import asyncio
from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api import auth, cameras, events, recordings, storage, system, users, websocket
from app.core.config import settings
from app.core.constants import (
    CameraSourceType,
    CameraStatus,
    RecordingMode,
    SystemDefaults,
    SystemThresholds,
)
from app.core.database import AsyncSessionLocal, init_db
from app.models.camera import Camera
from app.services.camera_manager import camera_manager
from app.services.retention_svc import retention_service

# Yapılandırılmış Loglama
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("LocalVisionNVR")


async def periodic_retention_task():
    """Her 6 saatte bir otomatik disk temizlik döngüsü yürütür."""
    while True:
        try:
            await asyncio.sleep(6 * 3600)
            logger.info("Periyodik depolama budama döngüsü çalıştırılıyor...")
            await retention_service.run_retention_cycle()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Periyodik retention hatası: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama açılış ve kapanış yaşam döngüsü."""
    logger.info("LocalVision NVR başlatılıyor...")

    # 1. Veritabanını ve ilk yöneticiyi hazırla
    await init_db()
    logger.info("Veritabanı tabloları hazırlandı.")

    # 2. Kamera yöneticisini başlat
    camera_manager.start()

    # 3. Mevcut kameraları veritabanından yükle veya ilk PC web kamerasını otomatik ekle
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Camera))
        existing_cams = result.scalars().all()

        if not existing_cams:
            # Kullanıcının bilgisayar kamerasıyla doğrudan test edebilmesi için demo kamera oluştur
            logger.info("Sistemde kamera bulunamadı; Test için PC Web Kamerası 0 otomatik ekleniyor...")
            demo_cam = Camera(
                name="Bilgisayar Kameram (Webcam 0)",
                description="Test ve anında izleme için otomatik oluşturulan yerel kamera",
                source_type=CameraSourceType.WEBCAM.value,
                webcam_index=0,
                fps=SystemDefaults.DEFAULT_LIVE_FPS,
                recording_mode=RecordingMode.CONTINUOUS.value,
                detection_enabled=True,
                detection_fps=SystemDefaults.DEFAULT_AI_FPS,
                confidence_threshold=SystemThresholds.DEFAULT_AI_CONFIDENCE,
                is_enabled=True
            )
            session.add(demo_cam)
            await session.commit()
            await session.refresh(demo_cam)
            existing_cams = [demo_cam]

        for cam in existing_cams:
            if cam.is_enabled:
                camera_manager.add_camera_instance(cam)

    # 4. Periyodik arka plan temizleme görevini başlat
    retention_bg = asyncio.create_task(periodic_retention_task())

    yield

    # Kapanış
    logger.info("LocalVision NVR kapatılıyor...")
    retention_bg.cancel()
    camera_manager.stop()


# FastAPI Uygulama Tanımı
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Kapsamlı, yerel ağ odaklı ve gizlilik tasarımlı IP Kamera Video Güvenlik Sistemi (NVR/VMS).",
    lifespan=lifespan
)

# CORS Yapılandırması
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Yerel ağ içi tüm tarayıcılardan erişim
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Hata Yakalayıcı
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"İşlenmemiş API Hatası ({request.url.path}): {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Sunucu içi hata: {str(exc)}"}
    )

# Rotaları Kaydet
app.include_router(auth.router)
app.include_router(cameras.router)
app.include_router(events.router)
app.include_router(recordings.router)
app.include_router(storage.router)
app.include_router(users.router)
app.include_router(system.router)
app.include_router(websocket.router)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs_url": "/docs",
        "privacy": "Privacy-by-Design, No biometric ID or facial recognition"
    }
