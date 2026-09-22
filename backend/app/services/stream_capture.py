"""
LocalVision NVR - Video Akış Yakalayıcı (Stream Capture).
- IP Kameralar: RTSP akışı
- Bilgisayar Kamerası: DirectShow / V4L2 Web Kamerası (Index 0, 1...)
- Otomatik yeniden bağlanma (Exponential backoff)
- Kare hızı (FPS) düzenleyici ve sağlık izleyici
"""

import logging
import sys
import threading
import time
from typing import Callable, Optional
import cv2
import numpy as np

from app.core.constants import (
    CameraSourceType,
    CameraStatus,
    SystemDefaults,
)
from app.services.ring_buffer import RingBuffer

logger = logging.getLogger(__name__)


class StreamCapture:
    """Tek bir kamera için asenkron kare alım ve akış sağlayıcı."""

    def __init__(
        self,
        camera_id: int,
        camera_name: str,
        source_type: str = CameraSourceType.RTSP.value,
        rtsp_url: Optional[str] = None,
        webcam_index: int = 0,
        target_fps: int = SystemDefaults.DEFAULT_LIVE_FPS,
        on_status_change: Optional[Callable[[int, CameraStatus, Optional[str]], None]] = None
    ):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.source_type = source_type
        self.rtsp_url = rtsp_url
        self.webcam_index = webcam_index
        self.target_fps = max(1, target_fps)
        self.on_status_change = on_status_change

        self.status = CameraStatus.OFFLINE
        self.error_message: Optional[str] = None
        self.ring_buffer = RingBuffer(
            max_seconds=SystemDefaults.RING_BUFFER_MAX_SECONDS,
            fps=self.target_fps
        )

        # Gerçek zamanlı akış metrikleri
        self.actual_width: int = 0
        self.actual_height: int = 0
        self.actual_fps: float = 0.0
        self.last_frame_time: float = 0.0

        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._cap: Optional[cv2.VideoCapture] = None

    def start(self) -> None:
        """Akış iş parçacığını başlatır."""
        if self._is_running:
            return
        self._is_running = True
        self._thread = threading.Thread(
            target=self._capture_loop,
            name=f"Capture-{self.camera_id}-{self.camera_name}",
            daemon=True
        )
        self._thread.start()
        logger.info(f"[{self.camera_name}] Akış yakalama başlatıldı ({self.source_type}).")

    def stop(self) -> None:
        """Akışı durdurur ve donanım kaynaklarını serbest bırakır."""
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._release_capture()
        self._set_status(CameraStatus.OFFLINE)
        logger.info(f"[{self.camera_name}] Akış durduruldu.")

    def _set_status(self, new_status: CameraStatus, error_msg: Optional[str] = None) -> None:
        """Kamera durumunu günceller ve dinleyiciye bildirir."""
        self.status = new_status
        self.error_message = error_msg
        if self.on_status_change:
            try:
                self.on_status_change(self.camera_id, new_status, error_msg)
            except Exception as e:
                logger.error(f"Durum bildirimi çağrısında hata: {e}")

    def _create_capture(self) -> Optional[cv2.VideoCapture]:
        """Kaynak tipine göre VideoCapture nesnesi oluşturur."""
        try:
            if self.source_type == CameraSourceType.WEBCAM.value:
                cap = None
                # Windows üzerinde DirectShow kamerasını dene
                if sys.platform.startswith("win"):
                    try:
                        cap = cv2.VideoCapture(self.webcam_index, cv2.CAP_DSHOW)
                        if not cap or not cap.isOpened():
                            cap = None
                    except Exception as ex:
                        logger.warning(f"DirectShow backend açılamadı ({ex}), varsayılan deneniyor...")
                        cap = None

                # Varsayılan backend dene
                if cap is None:
                    try:
                        cap = cv2.VideoCapture(self.webcam_index)
                    except Exception as ex:
                        logger.error(f"Varsayılan kamera backend açılamadı: {ex}")
                        return None

                if cap is not None and cap.isOpened():
                    cap.set(cv2.CAP_PROP_FPS, self.target_fps)
                    return cap
                return None

            elif self.source_type == CameraSourceType.RTSP.value:
                if not self.rtsp_url:
                    raise ValueError("RTSP URL belirtilmedi.")
                
                # Düşük gecikmeli RTSP parametreleri
                cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                return cap

            elif self.source_type == CameraSourceType.FILE_LOOP.value:
                if self.rtsp_url:
                    return cv2.VideoCapture(self.rtsp_url)
                return None
        except Exception as e:
            logger.error(f"[{self.camera_name}] VideoCapture oluşturma hatası: {e}")
            return None

        return None

    def _release_capture(self) -> None:
        """VideoCapture nesnesini güvenle kapatır."""
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    def _capture_loop(self) -> None:
        """Sürekli kare alım döngüsü ve bağlantı koruyucu."""
        reconnect_delay = SystemDefaults.RECONNECT_INITIAL_DELAY_SECONDS
        frame_interval = 1.0 / self.target_fps

        frame_count = 0
        fps_calc_start = time.time()

        while self._is_running:
            try:
                self._set_status(CameraStatus.CONNECTING)
                self._cap = self._create_capture()

                if not self._cap or not self._cap.isOpened():
                    raise ConnectionError(
                        f"Kamera açılamadı. Kaynak: {self.source_type} "
                        f"Index: {self.webcam_index if self.source_type == CameraSourceType.WEBCAM.value else self.rtsp_url}"
                    )

                # Başarıyla bağlandı
                self._set_status(CameraStatus.ONLINE)
                reconnect_delay = SystemDefaults.RECONNECT_INITIAL_DELAY_SECONDS

                # Çözünürlük bilgilerini oku
                self.actual_width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
                self.actual_height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)

                while self._is_running:
                    loop_start = time.time()
                    ret, frame = self._cap.read()

                    if not ret or frame is None:
                        # Akış kesildi veya dosya bitti
                        if self.source_type == CameraSourceType.FILE_LOOP.value:
                            # Dosyayı başa sar
                            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            continue
                        logger.warning(f"[{self.camera_name}] Akıştan kare okunamadı, yeniden bağlanılıyor...")
                        break

                    now = time.time()
                    self.last_frame_time = now
                    self.ring_buffer.add_frame(frame, timestamp=now)

                    # FPS ölçümü
                    frame_count += 1
                    elapsed = now - fps_calc_start
                    if elapsed >= 2.0:
                        self.actual_fps = round(frame_count / elapsed, 1)
                        frame_count = 0
                        fps_calc_start = now

                    # Hedef FPS'e göre uyu (CPU aşırı yüklenmesini önle)
                    process_time = time.time() - loop_start
                    sleep_time = frame_interval - process_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)

            except Exception as e:
                logger.error(f"[{self.camera_name}] Akış hatası: {e}")
                self._set_status(CameraStatus.ERROR, str(e))

            finally:
                self._release_capture()

            if self._is_running:
                # Üstel geri çekilme ile yeniden bağlanmayı bekle
                self._set_status(CameraStatus.OFFLINE, f"Yeniden bağlanılıyor ({reconnect_delay} sn)...")
                time.sleep(reconnect_delay)
                reconnect_delay = min(
                    reconnect_delay * 2,
                    SystemDefaults.RECONNECT_MAX_DELAY_SECONDS
                )
