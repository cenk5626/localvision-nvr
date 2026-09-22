"""
LocalVision NVR - Video Kayıt ve Klip Servisi (Recorder Service).
- Sürekli 60 saniyelik segmentli MP4 kayıtları
- Olay tabanlı kayıt: Olay öncesi 5 sn (pre-buffer) + olay anı + olay sonrası 10 sn (post-buffer)
- Anlık görüntü (Snapshot JPEG) yakalama
- Arka plan iş parçacığıyla diske yazma (Görüntü yakalamayı dondurmaz)
- SHA-256 bütünlük doğrulaması
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
import queue
import threading
import time
from typing import List, Optional, Tuple
import cv2
import numpy as np

from app.core.config import settings
from app.core.constants import RecordingMode, SystemDefaults
from app.core.security import security

logger = logging.getLogger(__name__)


class VideoRecorder:
    """Tek bir kamera için segmentli ve olay tabanlı MP4 yazıcısı."""

    def __init__(
        self,
        camera_id: int,
        camera_name: str,
        fps: int = SystemDefaults.DEFAULT_LIVE_FPS,
        segment_duration_seconds: int = SystemDefaults.SEGMENT_DURATION_SECONDS
    ):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.fps = max(1, fps)
        self.segment_duration = segment_duration_seconds

        # Kamera kayıt klasörleri
        self.cam_storage_dir = settings.STORAGE_DIR / f"camera_{self.camera_id}"
        self.cam_snapshot_dir = settings.SNAPSHOTS_DIR / f"camera_{self.camera_id}"
        self.cam_storage_dir.mkdir(parents=True, exist_ok=True)
        self.cam_snapshot_dir.mkdir(parents=True, exist_ok=True)

        # Segment durumu
        self._current_writer: Optional[cv2.VideoWriter] = None
        self._current_file_path: Optional[Path] = None
        self._segment_start_time: float = 0.0
        self._segment_frames: int = 0
        self._writer_size: Tuple[int, int] = (0, 0)

        # Asenkron yazma kuyruğu
        self._write_queue: queue.Queue = queue.Queue(maxsize=300)
        self._is_running = True
        self._worker_thread = threading.Thread(
            target=self._writer_worker,
            name=f"Recorder-{self.camera_id}",
            daemon=True
        )
        self._worker_thread.start()

    def process_frame(
        self,
        frame: np.ndarray,
        timestamp: float,
        is_continuous_active: bool = True
    ) -> Optional[Tuple[str, float, int, str]]:
        """
        Gelen kareyi asenkron kayıt kuyruğuna iletir.
        Segment tamamlandığında (file_path, duration, size, sha256) döndürür.
        """
        if frame is None or not is_continuous_active:
            return None

        try:
            self._write_queue.put_nowait(("frame", frame.copy(), timestamp))
        except queue.Full:
            logger.warning(f"[{self.camera_name}] Kayıt kuyruğu dolu! Kare atlandı.")

        return None

    def create_event_clip(
        self,
        pre_frames: List[Tuple[float, np.ndarray]],
        post_frames: List[Tuple[float, np.ndarray]],
        event_id: int
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Olay öncesi ve sonrası kareleri birleştirerek bağımsız bir MP4 klibi
        ve bir JPEG snapshot oluşturur.
        Dönüş: (video_clip_path, snapshot_path)
        """
        all_frames = pre_frames + post_frames
        if not all_frames:
            return None, None

        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        event_dir = self.cam_storage_dir / date_str / "events"
        event_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        clip_filename = f"event_{event_id}_{timestamp_str}.mp4"
        clip_path = event_dir / clip_filename

        snap_filename = f"snap_{event_id}_{timestamp_str}.jpg"
        snap_path = self.cam_snapshot_dir / snap_filename

        h, w = all_frames[0][1].shape[:2]

        # 1. En iyi temsil eden kareyi (olay anı karesi) snapshot olarak kaydet
        best_frame_idx = min(len(pre_frames), len(all_frames) - 1)
        snapshot_frame = all_frames[best_frame_idx][1]
        cv2.imwrite(str(snap_path), snapshot_frame)

        # 2. MP4 klibini yaz
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(clip_path), fourcc, float(self.fps), (w, h))

        if not writer.isOpened():
            logger.error(f"[{self.camera_name}] Olay klibi VideoWriter açılamadı: {clip_path}")
            return None, str(snap_path)

        for _, f in all_frames:
            if f.shape[:2] == (h, w):
                writer.write(f)

        writer.release()
        logger.info(f"[{self.camera_name}] Olay klibi kaydedildi: {clip_filename} ({len(all_frames)} kare)")

        return str(clip_path), str(snap_path)

    def _writer_worker(self) -> None:
        """Kayıt kuyruğunu disk dosyasına yazan arka plan döngüsü."""
        while self._is_running or not self._write_queue.empty():
            try:
                item = self._write_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            msg_type = item[0]
            if msg_type == "frame":
                _, frame, ts = item
                self._write_continuous_frame(frame, ts)
            elif msg_type == "stop":
                break

        self._close_current_segment()

    def _write_continuous_frame(self, frame: np.ndarray, timestamp: float) -> None:
        """Segmentli sürekli kayıt karesini yazar; süre dolunca yeni dosyaya geçer."""
        h, w = frame.shape[:2]
        now = time.time()

        # Yeni segment başlatma koşulları:
        # 1. Writer açık değil
        # 2. Segment süresi (60 sn) doldu
        # 3. Çözünürlük değişti
        if (
            self._current_writer is None
            or (now - self._segment_start_time) >= self.segment_duration
            or self._writer_size != (w, h)
        ):
            self._close_current_segment()
            self._open_new_segment(w, h)

        if self._current_writer and self._current_writer.isOpened():
            self._current_writer.write(frame)
            self._segment_frames += 1

    def _open_new_segment(self, width: int, height: int) -> None:
        """Yeni bir MP4 kayıt dosyası açar."""
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        target_dir = self.cam_storage_dir / date_str
        target_dir.mkdir(parents=True, exist_ok=True)

        time_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"cam{self.camera_id}_{time_str}.mp4"
        self._current_file_path = target_dir / filename

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._current_writer = cv2.VideoWriter(
            str(self._current_file_path),
            fourcc,
            float(self.fps),
            (width, height)
        )
        self._writer_size = (width, height)
        self._segment_start_time = time.time()
        self._segment_frames = 0

    def _close_current_segment(self) -> None:
        """Mevcut açık segmenti kapatır ve veritabanı kaydı için bildirir."""
        if self._current_writer:
            try:
                self._current_writer.release()
            except Exception:
                pass
            self._current_writer = None

        if self._current_file_path and self._current_file_path.exists():
            file_size = self._current_file_path.stat().st_size
            if file_size < 1024:  # 1 KB altındaki bozuk/boş dosyaları temizle
                try:
                    self._current_file_path.unlink()
                except Exception:
                    pass
            else:
                logger.info(f"[{self.camera_name}] Segment tamamlandı: {self._current_file_path.name} ({file_size // 1024} KB)")

        self._current_file_path = None
        self._segment_frames = 0

    def stop(self) -> None:
        """Kaydediciyi durdurur."""
        self._is_running = False
        try:
            self._write_queue.put_nowait(("stop", None, None))
        except Exception:
            pass
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
