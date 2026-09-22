"""
LocalVision NVR - Bölge (ROI), Çizgi (Tripwire) ve Takip Testleri.
"""

import time
import pytest
from app.core.constants import EventType
from app.services.ai_detector import DetectionBox
from app.services.zone_analyzer import ZoneAnalyzer


def test_polygon_roi_intrusion():
    """Çokgen bölgeye giren nesnenin tespiti test edilir."""
    analyzer = ZoneAnalyzer()

    # (100, 100) ile (300, 300) arasındaki kare bölge
    roi_zones = [{
        "name": "Yasak Alan",
        "points": [[100, 100], [300, 100], [300, 300], [100, 300]]
    }]

    # Bölge içinde nesne
    inside_det = DetectionBox(
        x1=150, y1=150, x2=200, y2=200,
        confidence=0.9, class_name="person", is_person=True, is_vehicle=False
    )
    # Bölge dışında nesne
    outside_det = DetectionBox(
        x1=400, y1=400, x2=450, y2=450,
        confidence=0.9, class_name="person", is_person=True, is_vehicle=False
    )

    events_inside = analyzer.check_zone_and_line_events([inside_det], roi_zones, [])
    assert len(events_inside) == 1
    assert events_inside[0]["event_type"] == EventType.ZONE_INTRUSION.value
    assert events_inside[0]["rule_name"] == "Yasak Alan"

    events_outside = analyzer.check_zone_and_line_events([outside_det], roi_zones, [])
    assert len(events_outside) == 0


def test_tripwire_line_crossing():
    """Sanal çizgi geçiş geometrisi test edilir."""
    analyzer = ZoneAnalyzer()

    # Dikey çizgi: (200, 50) -> (200, 350)
    tripwires = [{
        "name": "Giriş Çizgisi",
        "line": [[200, 50], [200, 350]]
    }]

    # 1. Adım: Nesne solda (180, 200)
    det_step1 = DetectionBox(
        x1=160, y1=180, x2=200, y2=220,  # center: (180, 200)
        confidence=0.88, class_name="person", is_person=True, is_vehicle=False
    )
    tracked1 = analyzer.update_tracks([det_step1])
    analyzer.check_zone_and_line_events(tracked1, [], tripwires)

    # 2. Adım: Nesne sağa geçti (220, 200)
    det_step2 = DetectionBox(
        x1=200, y1=180, x2=240, y2=220,  # center: (220, 200)
        confidence=0.89, class_name="person", is_person=True, is_vehicle=False
    )
    tracked2 = analyzer.update_tracks([det_step2])
    events = analyzer.check_zone_and_line_events(tracked2, [], tripwires)

    assert len(events) >= 1
    assert any(e["event_type"] == EventType.LINE_CROSSED.value for e in events)


def test_iou_calculation():
    """Kesişim/Birleşim (IoU) hesaplaması doğrulanır."""
    boxA = [0, 0, 100, 100]
    boxB = [50, 0, 150, 100]

    iou = ZoneAnalyzer._calculate_iou(boxA, boxB)
    assert round(iou, 2) == 0.33

    # Tam çakışma
    assert ZoneAnalyzer._calculate_iou(boxA, boxA) == 1.0
    # Sıfır çakışma
    boxC = [200, 200, 300, 300]
    assert ZoneAnalyzer._calculate_iou(boxA, boxC) == 0.0
