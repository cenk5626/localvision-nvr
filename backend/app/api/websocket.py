"""
LocalVision NVR - WebSocket Canlı Olay ve Bildirim Kanalı.
Frontend istemcilerine anlık insan/araç tespit ve kural ihlallerini iletir.
"""

import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.camera_manager import camera_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ws", tags=["WebSocket"])


@router.websocket("/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """Canlı olay bildirimleri ve kamera durum güncellemelerini yayınlar."""
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    camera_manager.register_event_subscriber(queue)

    try:
        # Karşılama mesajı gönder
        await websocket.send_json({
            "type": "connection_established",
            "message": "LocalVision NVR gerçek zamanlı olay akışına bağlandı."
        })

        while True:
            # Kuyruktan yeni olay bekle
            event_payload = await queue.get()
            await websocket.send_json(event_payload)

    except WebSocketDisconnect:
        logger.info("WebSocket istemcisi bağlantıyı kapattı.")
    except Exception as e:
        logger.error(f"WebSocket hatası: {e}")
    finally:
        camera_manager.unregister_event_subscriber(queue)
