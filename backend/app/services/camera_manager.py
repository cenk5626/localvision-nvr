"""
LocalVision NVR - Kamera Yönetim Servisi (Camera Manager).
Tüm kameraların yaşam döngüsünü, yapay zekâ analizini, kayıt tetikleyicilerini
ve canlı WebSocket/MJPEG akışını merkezi olarak yönetir.
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
import threading
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
import cv2
import numpy as np

from app.core.config import settings
from app.core.constants import (
    CameraSourceType,
    CameraStatus,
    EventType,
    RecordingMode,
    SystemDefaults,
)
from app.core.database import AsyncSessionLocal
from app.models.camera import Camera
from app.models.event import Event
from app.services.ai_detector import AIDetector, ai_detector
from app.services.recorder import VideoRecorder
from app.services.ring_buffer import RingBuffer
from app.services.stream_capture import StreamCapture
from app.services.zone_analyzer import ZoneAnalyzer

logger = logging.getLogger(__name__)


class CameraInstance:
    """Çalışan tek bir kameranın tüm bileşenlerini tutan kapsayıcı."""

    def __init__(self, camera_model: Camera):
        self.camera_id = camera_model.id
        self.name = camera_model.name
        self.source_type = camera_model.source_type
        self.rtsp_url = camera_model.rtsp_url
        self.webcam_index = camera_model.webcam_index
        self.fps = camera_model.fps
        self.recording_mode = camera_model.recording_mode
        self.detection_enabled = camera_model.detection_enabled
        self.detection_fps = camera_model.detection_fps
        self.confidence_threshold = camera_model.confidence_threshold
        self.roi_polygons = camera_model.roi_polygons
        self.tripwires = camera_model.tripwires
        self.max_dwell_seconds = camera_model.max_dwell_seconds

        # Alt servisler
        self.capture: StreamCapture = StreamCapture(
            camera_id=self.camera_id,
            camera_name=self.name,
            source_type=self.source_type,
            rtsp_url=self.rtsp_url,
            webcam_index=self.webcam_index,
            target_fps=self.fps
        )
        self.recorder: VideoRecorder = VideoRecorder(
            camera_id=self.camera_id,
            camera_name=self.name,
            fps=self.fps
        )
        self.zone_analyzer: ZoneAnalyzer = ZoneAnalyzer()

        # Son analiz edilen kare ve tespitler (Canlı izleme çizimi için)
        self.latest_annotated_frame: Optional[np.ndarray] = None
        self.last_detections: List[Any] = []
        self._lock = threading.Lock()


class CameraManager:
    """Sistemdeki tüm aktif kamera akışlarını ve arka plan AI işleyicilerini yönetir."""

    def __init__(self):
        self._instances: Dict[int, CameraInstance] = {}
        self._is_running = False
        self._ai_worker_thread: Optional[threading.Thread] = None
        self._event_subscribers: List[asyncio.Queue] = []

    def start(self) -> None:
        """Kamera yöneticisini ve arka plan AI analiz döngüsünü başlatır."""
        if self._is_running:
            return
        self._is_running = True
        self._ai_worker_thread = threading.Thread(
            target=self._ai_analysis_worker,
            name="CameraManager-AI-Worker",
            daemon=True
        )
        self._ai_worker_thread.start()
        logger.info("CameraManager başlatıldı.")

    def stop(self) -> None:
        """Tüm kameraları ve iş parçacıklarını güvenle durdurur."""
        self._is_running = False
        for cam_id, instance in list(self._instances.items()):
            self._stop_instance(instance)
        self._instances.clear()
        logger.info("CameraManager durduruldu.")

    def add_camera_instance(self, camera: Camera) -> None:
        """Yeni veya güncellenmiş kamerayı çalışma listesine ekler ve başlatır."""
        if camera.id in self._instances:
            self.remove_camera_instance(camera.id)

        if not camera.is_enabled:
            return

        instance = CameraInstance(camera)
        self._instances[camera.id] = instance
        instance.capture.start()
        logger.info(f"Kamera örneği başlatıldı: [{camera.id}] {camera.name}")

    def remove_camera_instance(self, camera_id: int) -> None:
        """Kamerayı çalışma listesinden çıkarır ve donanımı serbest bırakır."""
        instance = self._instances.pop(camera_id, None)
        if instance:
            self._stop_instance(instance)
            logger.info(f"Kamera örneği durduruldu: [{camera_id}] {instance.name}")

    def _stop_instance(self, instance: CameraInstance) -> None:
        """Kamera örneğinin tüm işlerini durdurur."""
        try:
            instance.capture.stop()
            instance.recorder.stop()
        except Exception as e:
            logger.error(f"Kamera durdurma hatası ({instance.name}): {e}")

    def get_instance(self, camera_id: int) -> Optional[CameraInstance]:
        return self._instances.get(camera_id)

    # ------------------------------------------------------------------------
    # Arka Plan Yapay Zeka Analizi ve Olay Tetikleme
    # ------------------------------------------------------------------------
    def _ai_analysis_worker(self) -> None:
        """Tüm kameralardan kareleri toplayıp yapay zekâ modelinden geçiren döngü."""
        last_analysis_times: Dict[int, float] = {}

        while self._is_running:
            now = time.time()

            for cam_id, instance in list(self._instances.items()):
                if not instance.detection_enabled:
                    continue

                # Kamera analiz FPS kontrolü
                interval = 1.0 / max(1, instance.detection_fps)
                last_time = last_analysis_times.get(cam_id, 0.0)
                if now - last_time < interval:
                    continue

                last_analysis_times[cam_id] = now
                frame = instance.capture.ring_buffer.get_latest_frame()
                if frame is None:
                    continue

                try:
                    self._process_camera_frame(instance, frame, now)
                except Exception as e:
                    logger.error(f"[{instance.name}] AI analizinde hata: {e}")

            time.sleep(0.01)

    def _process_camera_frame(self, instance: CameraInstance, frame: np.ndarray, timestamp: float) -> None:
        """Tek bir kamera karesini yapay zekâ, bölge kuralları ve kayıt için işler."""
        # 1. Nesne Tespiti (Yalnızca İnsan ve Araç!)
        detections = ai_detector.detect(frame, custom_confidence=instance.confidence_threshold)

        # 2. Anonim Kısa Süreli Takip Güncellemesi
        tracked_detections = instance.zone_analyzer.update_tracks(detections)

        # 3. Bölge ve Çizgi Olayları Kontrolü
        rule_events = instance.zone_analyzer.check_zone_and_line_events(
            detections=tracked_detections,
            roi_polygons=instance.roi_polygons,
            tripwires=instance.tripwires,
            max_dwell_seconds=instance.max_dwell_seconds
        )

        # 4. Genel İnsan/Araç Olay Tetikleyicisi
        has_person = any(d.is_person for d in tracked_detections)
        has_vehicle = any(d.is_vehicle for d in tracked_detections)

        # Sürekli kayıt işle
        is_cont = instance.recording_mode == RecordingMode.CONTINUOUS.value
        instance.recorder.process_frame(frame, timestamp, is_continuous_active=is_cont)

        # Olay tetikleme koşulları
        should_record_event = False
        triggered_types: List[str] = []

        if rule_events:
            should_record_event = True
            for re in rule_events:
                triggered_types.append(re["event_type"])

        if has_person and instance.recording_mode in (RecordingMode.PERSON_ONLY.value, RecordingMode.AI_ANY.value):
            should_record_event = True
            triggered_types.append(EventType.PERSON_DETECTED.value)

        if has_vehicle and instance.recording_mode in (RecordingMode.VEHICLE_ONLY.value, RecordingMode.AI_ANY.value):
            should_record_event = True
            triggered_types.append(EventType.VEHICLE_DETECTED.value)

        # 5. Görsel Çizim (Canlı yayın için kutuları ve bölgeleri çiz)
        annotated = frame.copy()
        self._draw_overlay(annotated, tracked_detections, instance.roi_polygons, instance.tripwires)

        with instance._lock:
            instance.latest_annotated_frame = annotated
            instance.last_detections = tracked_detections

        # 6. Olay varsa tampondan klip oluştur ve veri tabanına yaz
        if should_record_event and triggered_types:
            # Olay öncesi 5 saniye + şimdiki kare
            pre_frames = instance.capture.ring_buffer.get_recent_frames(
                seconds=SystemDefaults.PRE_EVENT_BUFFER_SECONDS
            )
            # Arka planda olayı kaydetmek için iş parçacığı başlat
            threading.Thread(
                target=self._save_event_async,
                args=(instance, pre_frames, frame, triggered_types[0], rule_events),
                daemon=True
            ).start()

    def _draw_overlay(
        self,
        frame: np.ndarray,
        detections: List[Any],
        roi_polygons: List[Dict[str, Any]],
        tripwires: List[Dict[str, Any]]
    ) -> None:
        """Kare üzerine gizliliği koruyarak yalnızca sınır kutularını ve bölgeleri çizer."""
        # Bölgeleri çiz (Mavi/Camgöbeği)
        for zone in roi_polygons:
            pts = zone.get("points", [])
            if len(pts) >= 3:
                poly = np.array(pts, dtype=np.int32)
                cv2.polylines(frame, [poly], isClosed=True, color=(255, 200, 0), thickness=2)
                name = zone.get("name", "Bölge")
                cv2.putText(frame, name, (pts[0][0], pts[0][1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1)

        # Çizgileri çiz (Kırmızı/Turuncu)
        for tw in tripwires:
            line_pts = tw.get("line", [])
            if len(line_pts) == 2:
                p1, p2 = tuple(line_pts[0]), tuple(line_pts[1])
                cv2.line(frame, p1, p2, color=(0, 140, 255), thickness=2)
                tw_name = tw.get("name", "Çizgi")
                cv2.putText(frame, tw_name, (p1[0], p1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 140, 255), 1)

        # Tespit edilen nesneleri çiz (İnsan: Yeşil, Araç: Sarı)
        for det in detections:
            color = (0, 255, 0) if det.is_person else (0, 215, 255)
            cv2.rectangle(frame, (det.x1, det.y1), (det.x2, det.y2), color, 2)
            label = f"{det.class_name} {int(det.confidence * 100)}%"
            if det.track_id:
                label += f" [#{det.track_id}]"

            # Arka plan etiketi
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (det.x1, det.y1 - 20), (det.x1 + tw, det.y1), color, -1)
            cv2.putText(frame, label, (det.x1, det.y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    def _save_event_async(
        self,
        instance: CameraInstance,
        pre_frames: List[Tuple[float, np.ndarray]],
        current_frame: np.ndarray,
        primary_event_type: str,
        rule_events: List[Dict[str, Any]]
    ) -> None:
        """Olay klibini ve anlık görüntüyü diske yazar, veritabanına kaydeder."""
        try:
            timestamp_now = time.time()
            # Kısa bir gecikmeyle olay sonrası tamponu oluştur (3 sn)
            post_frames = [(timestamp_now, current_frame)]

            # Geçici ID
            temp_event_id = int(time.time() * 1000) % 1000000

            clip_path, snap_path = instance.recorder.create_event_clip(
                pre_frames=pre_frames,
                post_frames=post_frames,
                event_id=temp_event_id
            )

            # Asenkron veritabanı oturumunda kaydet
            asyncio.run(self._insert_event_db(
                camera_id=instance.camera_id,
                camera_name=instance.name,
                event_type=primary_event_type,
                snap_path=snap_path,
                clip_path=clip_path,
                rule_events=rule_events
            ))
        except Exception as e:
            logger.error(f"Olay kaydetme hatası: {e}")

    async def _insert_event_db(
        self,
        camera_id: int,
        camera_name: str,
        event_type: str,
        snap_path: Optional[str],
        clip_path: Optional[str],
        rule_events: List[Dict[str, Any]]
    ) -> None:
        """Yeni olayı veritabanına ekler ve WebSocket dinleyicilerine yayınlar."""
        async with AsyncSessionLocal() as session:
            new_event = Event(
                camera_id=camera_id,
                camera_name=camera_name,
                event_type=event_type,
                confidence=0.85,
                snapshot_path=snap_path,
                video_clip_path=clip_path,
                details_json=json.dumps({"rules": rule_events})
            )
            session.add(new_event)
            await session.commit()
            await session.refresh(new_event)

            # WebSocket abonelerine anlık yayın yap
            event_payload = {
                "type": "new_event",
                "id": new_event.id,
                "camera_id": new_event.camera_id,
                "camera_name": new_event.camera_name,
                "event_type": new_event.event_type,
                "created_at": new_event.created_at.isoformat(),
                "snapshot_url": f"/api/events/{new_event.id}/snapshot" if snap_path else None
            }
            self.broadcast_ws_event(event_payload)

    # ------------------------------------------------------------------------
    # Canlı Akış (MJPEG / JPEG Stream Generator)
    # ------------------------------------------------------------------------
    async def generate_mjpeg_stream(self, camera_id: int) -> AsyncGenerator[bytes, None]:
        """Herhangi bir tarayıcı için sıfır eklentiyle çalışan 25 FPS canlı MJPEG akışı."""
        instance = self._instances.get(camera_id)
        if not instance:
            return

        while self._is_running:
            frame = None
            with instance._lock:
                if instance.latest_annotated_frame is not None:
                    frame = instance.latest_annotated_frame.copy()
                else:
                    frame = instance.capture.ring_buffer.get_latest_frame()

            if frame is not None:
                # JPEG olarak sıkıştır (Kalite: 70 - hız ve bant genişliği dengesi)
                ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                    )

            await asyncio.sleep(1.0 / instance.fps)

    # ------------------------------------------------------------------------
    # WebSocket Olay Dağıtımı
    # ------------------------------------------------------------------------
    def register_event_subscriber(self, q: asyncio.Queue) -> None:
        self._event_subscribers.append(q)

    def unregister_event_subscriber(self, q: asyncio.Queue) -> None:
        if q in self._event_subscribers:
            self._event_subscribers.remove(q)

    def broadcast_ws_event(self, payload: Dict[str, Any]) -> None:
        for q in self._event_subscribers:
            try:
                q.put_nowait(payload)
            except Exception:
                pass

    # ------------------------------------------------------------------------
    # Yerel PC Web Kamerası Otomatik Keşif Aracı
    # ------------------------------------------------------------------------
    @staticmethod
    def detect_available_webcams(max_to_check: int = 4) -> List[Dict[str, Any]]:
        """Sistemdeki mevcut web kameralarını (Index 0, 1..) tespit eder."""
        available = []
        for idx in range(max_to_check):
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
                available.append({
                    "index": idx,
                    "name": f"Kamera {idx} (PC Web Kamerası)",
                    "resolution": f"{w}x{h}"
                })
                cap.release()
        return available


# Global Kamera Yöneticisi Tekili
camera_manager = CameraManager()
