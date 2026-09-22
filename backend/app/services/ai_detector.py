"""
LocalVision NVR - Yapay Zekâ ve Olay Algılama Motoru.
KATI GİZLİLİK: Sadece İnsan (person) ve Araç (car, motorcycle, bus, truck, bicycle) tespit edilir.
Yüz tanıma, yüz veri tabanı veya biyometrik profil çıkarma fonksiyonları KESİNLİKLE YASAKTIR.
GPU varsa otomatik hızlandırılır; yoksa optimize CPU çekirdeği ile çalışır.
"""

from dataclasses import dataclass
import logging
import time
from typing import List, Optional, Tuple
import cv2
import numpy as np

from app.core.config import settings
from app.core.constants import (
    ALLOWED_AI_CLASSES,
    DetectionClass,
    SystemThresholds,
    VEHICLE_CLASSES,
)

logger = logging.getLogger(__name__)


@dataclass
class DetectionBox:
    """Tek bir tespit kutusu ve metaverisi."""
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    class_name: str  # "person" veya "car", "truck" vb.
    is_person: bool
    is_vehicle: bool
    track_id: Optional[int] = None

    @property
    def center(self) -> Tuple[int, int]:
        return int((self.x1 + self.x2) / 2), int((self.y1 + self.y2) / 2)

    @property
    def bbox(self) -> List[int]:
        return [self.x1, self.y1, self.x2, self.y2]


class AIDetector:
    """YOLOv8 ve OpenCV DNN tabanlı nesne tespit motoru."""

    def __init__(self, confidence_threshold: float = SystemThresholds.DEFAULT_AI_CONFIDENCE):
        self.confidence_threshold = confidence_threshold
        self._model = None
        self._onnx_session = None
        self._is_ready = False
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=False)
        self._init_detector()

    def _init_detector(self) -> None:
        """Tespit motorunu ilklendirir (YOLOv8 / ONNX / CPU-GPU)."""
        # 1. Ultralytics YOLOv8 kontrolü
        try:
            from ultralytics import YOLO
            # Küçük, hızlı ve gizlilik dostu YOLOv8n modeli
            model_path = settings.MODELS_DIR / settings.AI_MODEL_NAME
            if not model_path.exists():
                # Varsayılan nano model (6 MB)
                self._model = YOLO("yolov8n.pt")
            else:
                self._model = YOLO(str(model_path))

            self._is_ready = True
            logger.info("AIDetector: Ultralytics YOLOv8 başarıyla yüklendi (GPU/CPU otomatik).")
            return
        except Exception as e:
            logger.warning(f"AIDetector: Ultralytics yüklenemedi: {e}. Alternatif deneniyor...")

        # 2. ONNX Runtime doğrudan oturumu
        try:
            import onnxruntime as ort
            onnx_path = settings.MODELS_DIR / "yolov8n.onnx"
            if onnx_path.exists():
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if settings.AI_USE_GPU else ["CPUExecutionProvider"]
                self._onnx_session = ort.InferenceSession(str(onnx_path), providers=providers)
                self._is_ready = True
                logger.info("AIDetector: ONNX Runtime oturumu hazır.")
                return
        except Exception as e:
            logger.warning(f"AIDetector: ONNX Runtime başlatılamadı: {e}")

        logger.info("AIDetector: OpenCV piksel ve kontur analiz modu devrede (Çevrimdışı temel mod).")
        self._is_ready = True

    def detect(self, frame: np.ndarray, custom_confidence: Optional[float] = None) -> List[DetectionBox]:
        """
        Kare üzerinde insan ve araç tespiti yapar.
        KATI GİZLİLİK FİLTRESİ: İzin verilen sınıflar dışındaki nesneler yok sayılır.
        """
        if frame is None or not self._is_ready:
            return []

        threshold = custom_confidence if custom_confidence is not None else self.confidence_threshold
        results_list: List[DetectionBox] = []

        # 1. Ultralytics YOLO modeli varsa
        if self._model is not None:
            try:
                # Sadece izin verilen COCO sınıflarını filtrele (0: person, 1: bicycle, 2: car, 3: motorcycle, 5: bus, 7: truck)
                allowed_coco_indices = [0, 1, 2, 3, 5, 7]
                preds = self._model(frame, conf=threshold, classes=allowed_coco_indices, verbose=False)

                for result in preds:
                    boxes = result.boxes
                    if boxes is None:
                        continue
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        conf = float(box.conf[0].item())
                        cls_name = result.names.get(cls_id, "unknown")

                        # Katı filtre
                        if cls_name not in ALLOWED_AI_CLASSES:
                            continue

                        xyxy = box.xyxy[0].tolist()
                        x1, y1, x2, y2 = map(int, xyxy)

                        is_person = (cls_name == DetectionClass.PERSON.value)
                        is_veh = (cls_name in VEHICLE_CLASSES)

                        results_list.append(DetectionBox(
                            x1=x1, y1=y1, x2=x2, y2=y2,
                            confidence=round(conf, 2),
                            class_name=cls_name,
                            is_person=is_person,
                            is_vehicle=is_veh
                        ))
                return results_list
            except Exception as e:
                logger.error(f"YOLO tespit hatası: {e}")

        # 2. Model henüz inmemişse veya çevrimdışı basit moddaysa: MOG2 hareket ve insan silueti kontur analizi
        return self._detect_motion_fallback(frame)

    def _detect_motion_fallback(self, frame: np.ndarray) -> List[DetectionBox]:
        """
        Derin öğrenme modeli bulunmadığında veya GPU/CPU kısıtında
        hareketli siluetleri insan/araç adayları olarak analiz eder.
        """
        results: List[DetectionBox] = []
        try:
            fg_mask = self._bg_subtractor.apply(frame)
            # Gürültüyü temizle
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            cleaned_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            h, w = frame.shape[:2]
            min_area = int((w * h) * 0.005)  # En az %0.5 büyüklük

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < min_area:
                    continue
                x, y, cw, ch = cv2.boundingRect(cnt)
                aspect_ratio = float(ch) / float(cw)

                # İnsan oranı genelde dikey (aspect_ratio > 1.3), araçlar daha yataydır
                is_person = aspect_ratio >= 1.2
                is_vehicle = not is_person
                cls_name = DetectionClass.PERSON.value if is_person else DetectionClass.CAR.value

                results.append(DetectionBox(
                    x1=x, y1=y, x2=x + cw, y2=y + ch,
                    confidence=0.75,
                    class_name=cls_name,
                    is_person=is_person,
                    is_vehicle=is_vehicle
                ))
        except Exception as e:
            logger.error(f"Fallback analiz hatası: {e}")

        return results

    def detect_motion_only(self, frame: np.ndarray, sensitivity: float = SystemThresholds.DEFAULT_MOTION_SENSITIVITY) -> bool:
        """Piksel hareket analizi yapar (True/False)."""
        if frame is None:
            return False
        try:
            fg_mask = self._bg_subtractor.apply(frame)
            non_zero = cv2.countNonZero(fg_mask)
            total_pixels = frame.shape[0] * frame.shape[1]
            motion_ratio = float(non_zero) / float(total_pixels)
            # Eşik ile karşılaştır
            threshold = (1.0 - sensitivity) * 0.05 + 0.002
            return motion_ratio > threshold
        except Exception:
            return False


# Global tespit motoru tekili (Lazy initialization)
ai_detector = AIDetector()
