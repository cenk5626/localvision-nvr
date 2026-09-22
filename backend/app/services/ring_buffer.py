"""
LocalVision NVR - Halka Bellek (Circular Ring Buffer).
Olay öncesi (pre-event) ve anlık canlı yayın için son N saniyelik video karelerini RAM'de tutar.
Thread-safe (iş parçacığı güvenli) kilit mekanizması ile çalışır.
"""

from collections import deque
import threading
import time
from typing import List, Optional, Tuple
import numpy as np

from app.core.constants import SystemDefaults


class FramePacket:
    """Tek bir video karesi ve metaverisi."""
    __slots__ = ("frame", "timestamp", "frame_idx")

    def __init__(self, frame: np.ndarray, timestamp: float, frame_idx: int):
        self.frame = frame
        self.timestamp = timestamp
        self.frame_idx = frame_idx


class RingBuffer:
    """Sabit süreli dairesel video tampon belleği."""

    def __init__(self, max_seconds: int = SystemDefaults.RING_BUFFER_MAX_SECONDS, fps: int = SystemDefaults.DEFAULT_LIVE_FPS):
        self.max_seconds = max_seconds
        self.fps = max(1, fps)
        self.max_frames = self.max_seconds * self.fps
        self._buffer: deque[FramePacket] = deque(maxlen=self.max_frames)
        self._lock = threading.Lock()
        self._frame_counter: int = 0

    def add_frame(self, frame: np.ndarray, timestamp: Optional[float] = None) -> None:
        """Yeni bir kareyi halka belleğe ekler."""
        if frame is None:
            return
        ts = timestamp if timestamp is not None else time.time()
        with self._lock:
            self._frame_counter += 1
            # Hafif kopya ile referansı sakla
            packet = FramePacket(frame=frame.copy(), timestamp=ts, frame_idx=self._frame_counter)
            self._buffer.append(packet)

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Canlı yayın veya anlık görüntü için son kareyi döndürür."""
        with self._lock:
            if not self._buffer:
                return None
            return self._buffer[-1].frame.copy()

    def get_recent_frames(self, seconds: float = SystemDefaults.PRE_EVENT_BUFFER_SECONDS) -> List[Tuple[float, np.ndarray]]:
        """
        Şimdiki andan geriye doğru istenen saniye kadar kareleri döndürür.
        Olay öncesi tampon (pre-event buffer) için kullanılır.
        """
        now = time.time()
        cutoff_time = now - seconds
        with self._lock:
            # Belirlenen zaman eşiğinden sonraki tüm kareleri topla
            selected: List[Tuple[float, np.ndarray]] = []
            for packet in self._buffer:
                if packet.timestamp >= cutoff_time:
                    selected.append((packet.timestamp, packet.frame.copy()))
            return selected

    def clear(self) -> None:
        """Tamponu temizler."""
        with self._lock:
            self._buffer.clear()

    @property
    def current_size(self) -> int:
        with self._lock:
            return len(self._buffer)
