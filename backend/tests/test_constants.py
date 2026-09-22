"""
LocalVision NVR - Sabitler ve Gizlilik Kuralları Birim Testleri.
Kullanıcı Kuralı: "magic number / string kontrolü: önemli değerler sabit veya enum olarak tanımlanmalı"
Gizlilik Kuralı: Yüz tanıma ve biyometri kesinlikle yasaktır!
"""

import pytest
from app.core.constants import (
    ALLOWED_AI_CLASSES,
    AuditAction,
    CameraSourceType,
    CameraStatus,
    DetectionClass,
    EventType,
    RecordingMode,
    SystemDefaults,
    SystemThresholds,
    UserRole,
    VEHICLE_CLASSES,
)


def test_user_roles_enum():
    """Kullanıcı rolleri eksiksiz ve beklenen değerlerde olmalıdır."""
    assert UserRole.ADMIN == "admin"
    assert UserRole.OPERATOR == "operator"
    assert UserRole.VIEWER == "viewer"
    assert UserRole.USER == "user"
    assert len(UserRole) == 4


def test_privacy_boundaries_in_ai_classes():
    """
    KATI GİZLİLİK TESTİ:
    Sistemde asla 'face', 'identity', 'person_name' veya biyometrik sınıf bulunmamalıdır!
    """
    for cls_name in ALLOWED_AI_CLASSES:
        assert "face" not in cls_name.lower(), "Yüz tanıma sınıfı tespit edildi! Yasaktır."
        assert "bio" not in cls_name.lower(), "Biyometrik sınıf tespit edildi! Yasaktır."
        assert "identity" not in cls_name.lower(), "Kimlik sınıfı tespit edildi! Yasaktır."

    # İzin verilen sınıflar yalnızca insan ve araç olmalıdır
    assert DetectionClass.PERSON.value in ALLOWED_AI_CLASSES
    assert DetectionClass.CAR.value in ALLOWED_AI_CLASSES
    assert DetectionClass.TRUCK.value in ALLOWED_AI_CLASSES


def test_system_defaults_no_magic_numbers():
    """Tüm portlar, tampon süreleri ve limitler SystemDefaults içinde sabit olmalıdır."""
    assert SystemDefaults.DEFAULT_API_PORT == 8000
    assert SystemDefaults.PRE_EVENT_BUFFER_SECONDS == 5
    assert SystemDefaults.POST_EVENT_BUFFER_SECONDS == 10
    assert SystemDefaults.SEGMENT_DURATION_SECONDS == 60
    assert SystemDefaults.DEFAULT_RETENTION_DAYS == 14
    assert SystemDefaults.MIN_FREE_DISK_PERCENT == 10


def test_camera_status_and_modes():
    """Kamera durumları ve kayıt modları eksiksiz tanımlı olmalıdır."""
    assert CameraStatus.ONLINE == "online"
    assert CameraStatus.OFFLINE == "offline"
    assert CameraSourceType.WEBCAM == "webcam"
    assert CameraSourceType.RTSP == "rtsp"
    assert RecordingMode.CONTINUOUS == "continuous"
    assert RecordingMode.PERSON_ONLY == "person_only"
