"""
LocalVision NVR - Bölge ve Kural Analiz Servisi (Zone & Rule Analyzer).
- Çokgen (Polygon ROI) ihlali (Ray-casting / pointPolygonTest)
- Sanal çizgi geçişi (Tripwire Line Crossing - Kesişim geometrisi)
- Bölgede bekleme süresi (Dwell time / Loitering alert)
- Kısa süreli anonim nesne takibi (IoU Tracker - Kalıcı kimlik içermez!)
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np

from app.core.constants import (
    EventType,
    SystemDefaults,
    SystemThresholds,
)
from app.services.ai_detector import DetectionBox


@dataclass
class TrackedObject:
    """Tek bir kare içi anlık anonim takip nesnesi."""
    track_id: int
    class_name: str
    last_center: Tuple[int, int]
    last_bbox: List[int]
    first_seen: float
    last_seen: float
    history: List[Tuple[int, int]] = field(default_factory=list)
    dwell_zones: Dict[str, float] = field(default_factory=dict)  # zone_name -> enter_time
    dwell_alerted_zones: List[str] = field(default_factory=list)


class ZoneAnalyzer:
    """Kamera algılama bölgelerini, çizgilerini ve olay kurallarını denetleyen motor."""

    def __init__(self, iou_threshold: float = SystemThresholds.IOU_TRACK_THRESHOLD):
        self.iou_threshold = iou_threshold
        self._next_track_id: int = 1
        self._active_tracks: Dict[int, TrackedObject] = {}
        self._last_cleanup: float = time.time()

    def update_tracks(self, detections: List[DetectionBox]) -> List[DetectionBox]:
        """
        Gelen tespitleri IoU algoritması ile önceki karelerle eşleştirir.
        Kalıcı kişi profili oluşturmaz; anlık çizgi geçişi ve bekleme analizi içindir.
        """
        now = time.time()
        updated_detections: List[DetectionBox] = []

        if not self._active_tracks:
            # İlk tespitler, yeni ID ata
            for det in detections:
                tid = self._next_track_id
                self._next_track_id += 1
                det.track_id = tid
                self._active_tracks[tid] = TrackedObject(
                    track_id=tid,
                    class_name=det.class_name,
                    last_center=det.center,
                    last_bbox=det.bbox,
                    first_seen=now,
                    last_seen=now,
                    history=[det.center]
                )
                updated_detections.append(det)
            return updated_detections

        # Mevcut izlerle yeni kutular arasında IoU matrisi hesapla
        track_ids = list(self._active_tracks.keys())
        matched_tracks = set()

        for det in detections:
            best_iou = 0.0
            best_tid: Optional[int] = None

            # 1. IoU ile eşleştir
            for tid in track_ids:
                if tid in matched_tracks:
                    continue
                tr = self._active_tracks[tid]
                iou = self._calculate_iou(det.bbox, tr.last_bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_tid = tid

            # 2. Eğer IoU düşükse ama merkez mesafesi yakınsa (Centroid match)
            best_dist = float("inf")
            if (best_iou < self.iou_threshold or best_tid is None) and track_ids:
                for tid in track_ids:
                    if tid in matched_tracks:
                        continue
                    tr = self._active_tracks[tid]
                    dx = det.center[0] - tr.last_center[0]
                    dy = det.center[1] - tr.last_center[1]
                    dist = (dx * dx + dy * dy) ** 0.5
                    if dist < 80.0 and dist < best_dist:  # 80 piksel içinde
                        best_dist = dist
                        best_tid = tid

            is_matched = (best_tid is not None) and (best_iou >= self.iou_threshold or best_dist < 80.0)
            if is_matched:
                # Eşleşti
                det.track_id = best_tid
                matched_tracks.add(best_tid)
                tr = self._active_tracks[best_tid]
                tr.last_center = det.center
                tr.last_bbox = det.bbox
                tr.last_seen = now
                tr.history.append(det.center)
                if len(tr.history) > 30:
                    tr.history.pop(0)
            else:
                # Yeni nesne
                tid = self._next_track_id
                self._next_track_id += 1
                det.track_id = tid
                self._active_tracks[tid] = TrackedObject(
                    track_id=tid,
                    class_name=det.class_name,
                    last_center=det.center,
                    last_bbox=det.bbox,
                    first_seen=now,
                    last_seen=now,
                    history=[det.center]
                )

            updated_detections.append(det)

        # 3 saniyeden uzun süredir görülmeyen izleri bellekten sil
        if now - self._last_cleanup > 1.0:
            stale = [tid for tid, tr in self._active_tracks.items() if now - tr.last_seen > 3.0]
            for tid in stale:
                del self._active_tracks[tid]
            self._last_cleanup = now

        return updated_detections

    def check_zone_and_line_events(
        self,
        detections: List[DetectionBox],
        roi_polygons: List[Dict[str, Any]],
        tripwires: List[Dict[str, Any]],
        max_dwell_seconds: int = SystemDefaults.MAX_DWELL_SECONDS
    ) -> List[Dict[str, Any]]:
        """
        Bölge ihlalleri, çizgi geçişleri ve bekleme alarmlarını tespit eder.
        Dönen liste her tetiklenen kural için olay detayını içerir.
        """
        now = time.time()
        triggered_events: List[Dict[str, Any]] = []

        for det in detections:
            center = det.center
            tr = self._active_tracks.get(det.track_id) if det.track_id else None

            # 1. Çokgen Bölge (ROI) ve Dwell Time Kontrolü
            for zone in roi_polygons:
                zone_name = zone.get("name", "Bilinmeyen Bölge")
                points = zone.get("points", [])  # [[x, y], [x, y], ...]
                if len(points) < 3:
                    continue

                poly_np = np.array(points, dtype=np.int32)
                # Nokta çokgenin içinde mi? (> 0: içinde, 0: kenarda, < 0: dışında)
                is_inside = cv2.pointPolygonTest(poly_np, (float(center[0]), float(center[1])), False) >= 0

                if is_inside:
                    # Bölge İhlali Olayı
                    triggered_events.append({
                        "event_type": EventType.ZONE_INTRUSION.value,
                        "rule_name": zone_name,
                        "confidence": det.confidence,
                        "class_name": det.class_name,
                        "bbox": det.bbox,
                        "track_id": det.track_id
                    })

                    # Bekleme Süresi (Dwell time / Loitering) Analizi
                    if tr:
                        if zone_name not in tr.dwell_zones:
                            tr.dwell_zones[zone_name] = now
                        else:
                            time_in_zone = now - tr.dwell_zones[zone_name]
                            if time_in_zone >= max_dwell_seconds and zone_name not in tr.dwell_alerted_zones:
                                tr.dwell_alerted_zones.append(zone_name)
                                triggered_events.append({
                                    "event_type": EventType.DWELL_ALERT.value,
                                    "rule_name": f"{zone_name} (Bekleme: {int(time_in_zone)} sn)",
                                    "confidence": det.confidence,
                                    "class_name": det.class_name,
                                    "bbox": det.bbox,
                                    "track_id": det.track_id
                                })
                else:
                    # Bölgeden çıktıysa sıfırla
                    if tr and zone_name in tr.dwell_zones:
                        del tr.dwell_zones[zone_name]

            # 2. Sanal Çizgi Geçişi (Tripwire) Kontrolü
            if tr and len(tr.history) >= 2:
                prev_pt = tr.history[-2]
                curr_pt = tr.history[-1]

                for tw in tripwires:
                    tw_name = tw.get("name", "Bilinmeyen Çizgi")
                    line_pts = tw.get("line", [])  # [[x1, y1], [x2, y2]]
                    if len(line_pts) == 2:
                        l_p1 = tuple(line_pts[0])
                        l_p2 = tuple(line_pts[1])

                        if self._segments_intersect(prev_pt, curr_pt, l_p1, l_p2):
                            triggered_events.append({
                                "event_type": EventType.LINE_CROSSED.value,
                                "rule_name": tw_name,
                                "confidence": det.confidence,
                                "class_name": det.class_name,
                                "bbox": det.bbox,
                                "track_id": det.track_id
                            })

        return triggered_events

    @staticmethod
    def _calculate_iou(box1: List[int], box2: List[int]) -> float:
        """İki dikdörtgen kutu arasındaki Kesişim / Birleşim (IoU) oranını hesaplar."""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        intersection_area = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union_area = area1 + area2 - intersection_area

        if union_area <= 0:
            return 0.0
        return float(intersection_area) / float(union_area)

    @staticmethod
    def _segments_intersect(p1: Tuple[int, int], p2: Tuple[int, int], p3: Tuple[int, int], p4: Tuple[int, int]) -> bool:
        """İki doğru parçasının (p1-p2 ile p3-p4) kesişip kesişmediğini denetler."""
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

        return (ccw(p1, p3, p4) != ccw(p2, p3, p4)) and (ccw(p1, p2, p3) != ccw(p1, p2, p4))
