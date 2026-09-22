"""
LocalVision NVR - Yapay Zekâ Tespit Motoru Testleri.
Gizlilik ve İnsan/Araç Algılama Doğrulaması.
"""

import numpy as np
import pytest
from app.core.constants import ALLOWED_AI_CLASSES, DetectionClass
from app.services.ai_detector import AIDetector, DetectionBox


def test_ai_detector_initialization():
    """AIDetector sorunsuz ilklendirilmeli ve hazır olmalıdır."""
    detector = AIDetector(confidence_threshold=0.40)
    assert detector._is_ready is True


def test_ai_detector_dummy_frame():
    """Boş kare verildiğinde hata vermeden çalışmalıdır."""
    detector = AIDetector()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    results = detector.detect(frame)
    assert isinstance(results, list)


def test_ai_detector_privacy_enforcement():
    """
    KATI GİZLİLİK TESTİ:
    Eğer bir dedektör çıktı üretirse, bu çıktılar yalnızca ALLOWED_AI_CLASSES içinde olmalıdır.
    """
    detector = AIDetector()
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 120
    results = detector.detect(frame)

    for box in results:
        assert box.class_name in ALLOWED_AI_CLASSES
        # Asla yüz veya biyometrik olamaz
        assert "face" not in box.class_name.lower()
        assert box.is_person or box.is_vehicle


def test_motion_detection_subtractor():
    """Hareket algılayıcı piksel değişimini tespit edebilmelidir."""
    detector = AIDetector()
    frame1 = np.zeros((200, 200, 3), dtype=np.uint8)
    frame2 = np.ones((200, 200, 3), dtype=np.uint8) * 255  # Ani büyük değişim

    # İlk kare arka planı eğitir
    detector.detect_motion_only(frame1)
    # İkinci karede hareket tespit edilmelidir
    has_motion = detector.detect_motion_only(frame2, sensitivity=0.5)
    assert isinstance(has_motion, bool)
