"""
LocalVision NVR - Çekirdek Sabitler ve Numaralandırmalar (Enums).
Kullanıcı Kuralı: "magic number / string kontrolü: önemli değerler sabit veya enum olarak tanımlanmalı"
Bu modül sistemdeki tüm roller, durumlar, olay türleri, eşikler ve ağ sabitlerini tip güvenli olarak tanımlar.
"""

from enum import Enum, IntEnum, StrEnum
from typing import Final, List, Set


# ============================================================================
# KULLANICI ROLLERİ VE YETKİLENDİRME (RBAC)
# ============================================================================
class UserRole(StrEnum):
    """Sistem kullanıcı rolleri."""
    ADMIN = "admin"            # Tam yetkili sistem yöneticisi
    OPERATOR = "operator"      # Kameraları izleyebilir, yönlendirebilir, dışa aktarabilir
    VIEWER = "viewer"          # Yalnızca yetkili kameraları canlı izleyebilir ve geçmişi görebilir
    USER = "user"              # Kısıtlı son kullanıcı (yalnızca izinli kameralar ve kendi yer imleri)


# ============================================================================
# KAMERA DURUMLARI VE BAĞLANTI TİPLERİ
# ============================================================================
class CameraStatus(StrEnum):
    """Kamera canlı bağlantı sağlık durumları."""
    ONLINE = "online"          # Akış sorunsuz alınıyor
    OFFLINE = "offline"        # Bağlantı koptu veya ulaşılamıyor
    CONNECTING = "connecting"  # Bağlantı kurulmaya çalışılıyor
    ERROR = "error"            # Kimlik doğrulama veya codec hatası


class CameraSourceType(StrEnum):
    """Kamera kaynak protokolü / giriş tipi."""
    RTSP = "rtsp"              # Standart IP Kamera RTSP akışı (rtsp://...)
    WEBCAM = "webcam"          # Bilgisayarın dahili/harici web kamerası (Index 0, 1, DirectShow/V4L2)
    ONVIF = "onvif"            # ONVIF Profile S/T keşfedilmiş kamera
    FILE_LOOP = "file_loop"    # Sentetik test ve demo için döngüsel video dosyası


class VideoCodec(StrEnum):
    """Desteklenen video çözücü formatları."""
    H264 = "h264"
    H265 = "h265"
    MJPEG = "mjpeg"
    UNKNOWN = "unknown"


# ============================================================================
# KAYIT MODLARI VE TETİKLEYİCİLER
# ============================================================================
class RecordingMode(StrEnum):
    """Kameraya ait kayıt stratejileri."""
    CONTINUOUS = "continuous"      # 7/24 Kesintisiz kayıt
    MOTION = "motion"              # Yalnızca hareket algılandığında
    PERSON_ONLY = "person_only"    # Yalnızca insan algılandığında (Gizlilik odaklı)
    VEHICLE_ONLY = "vehicle_only"  # Yalnızca araç algılandığında
    AI_ANY = "ai_any"              # İnsan veya araç algılandığında
    SCHEDULED = "scheduled"        # Zaman planına göre kayıt
    MANUAL = "manual"              # Operatör tarafından elle başlatılan kayıt
    DISABLED = "disabled"          # Kayıt kapalı


# ============================================================================
# OLAY TÜRLERİ VE YAPAY ZEKA TESPİT SINIFLARI
# ============================================================================
class EventType(StrEnum):
    """Yapay zekâ ve algılama olay türleri."""
    PERSON_DETECTED = "person_detected"    # İnsan algılandı
    VEHICLE_DETECTED = "vehicle_detected"  # Araç algılandı
    MOTION_DETECTED = "motion_detected"    # Piksel hareket algılandı
    LINE_CROSSED = "line_crossed"          # Tanımlı sanal çizgi geçildi (Tripwire)
    ZONE_INTRUSION = "zone_intrusion"      # Yasaklı çokgen alana girildi (ROI)
    DWELL_ALERT = "dwell_alert"            # Bölgede uzun süre kalındı (Loitering)


class DetectionClass(StrEnum):
    """
    Sistemin tespit etmesine izin verilen nesneler (COCO İndeksleri ile eşlenir).
    KATİ GİZLİLİK KURALI: Yüz tanıma veya biyometrik sınıf bulunmaz!
    """
    PERSON = "person"          # COCO id 0
    BICYCLE = "bicycle"        # COCO id 1
    CAR = "car"                # COCO id 2
    MOTORCYCLE = "motorcycle"  # COCO id 3
    BUS = "bus"                # COCO id 5
    TRUCK = "truck"            # COCO id 7


# İzin verilen yapay zekâ sınıfları kümesi (Güvenlik filtresi)
ALLOWED_AI_CLASSES: Final[Set[str]] = {
    DetectionClass.PERSON.value,
    DetectionClass.BICYCLE.value,
    DetectionClass.CAR.value,
    DetectionClass.MOTORCYCLE.value,
    DetectionClass.BUS.value,
    DetectionClass.TRUCK.value,
}

VEHICLE_CLASSES: Final[Set[str]] = {
    DetectionClass.BICYCLE.value,
    DetectionClass.CAR.value,
    DetectionClass.MOTORCYCLE.value,
    DetectionClass.BUS.value,
    DetectionClass.TRUCK.value,
}


# ============================================================================
# DENETİM GÜNLÜĞÜ (AUDIT LOG) EYLEMLERİ
# ============================================================================
class AuditAction(StrEnum):
    """Güvenlik ve KVKK gereği kayıt altına alınan kullanıcı eylemleri."""
    AUTH_LOGIN = "auth_login"
    AUTH_LOGOUT = "auth_logout"
    AUTH_LOGIN_FAILED = "auth_login_failed"
    CAMERA_CREATE = "camera_create"
    CAMERA_UPDATE = "camera_update"
    CAMERA_DELETE = "camera_delete"
    RECORDING_VIEW = "recording_view"
    RECORDING_DOWNLOAD = "recording_download"
    RECORDING_EXPORT = "recording_export"
    RECORDING_DELETE = "recording_delete"
    BOOKMARK_CREATE = "bookmark_create"
    BOOKMARK_REMOVE = "bookmark_remove"
    RETENTION_PRUNE = "retention_prune"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    SETTINGS_CHANGE = "settings_change"
    BACKUP_TRIGGER = "backup_trigger"


# ============================================================================
# SİSTEM, BELLEK VE DEPOLAMA SABİTLERİ (MAGIC NUMBER KONTROLÜ)
# ============================================================================
class SystemDefaults(IntEnum):
    """Sayısal sistem varsayılanları ve limitleri."""
    # Ağ ve Portlar
    DEFAULT_API_PORT = 8000
    DEFAULT_FRONTEND_PORT = 5173
    DEFAULT_RTSP_PORT = 554
    DEFAULT_ONVIF_PORT = 80

    # Tampon ve Süre Sabitleri (Saniye)
    PRE_EVENT_BUFFER_SECONDS = 5       # Olay öncesi halka bellek tamponu (saniye)
    POST_EVENT_BUFFER_SECONDS = 10     # Olay sonrası kayıt tamponu (saniye)
    SEGMENT_DURATION_SECONDS = 60      # Sürekli kayıt dosya segment uzunluğu (saniye)
    RING_BUFFER_MAX_SECONDS = 15       # Halka belleğin saklayacağı azami süre (saniye)
    DEFAULT_LIVE_FPS = 20              # Varsayılan canlı yayın FPS değeri
    DEFAULT_AI_FPS = 5                 # Varsayılan yapay zeka analiz FPS değeri
    MAX_DWELL_SECONDS = 30             # Bölgede bekleme alarmı eşiği (saniye)

    # Ağ Zaman Aşımları ve Yeniden Bağlanma (Saniye)
    SOCKET_TIMEOUT_SECONDS = 5
    RECONNECT_INITIAL_DELAY_SECONDS = 3
    RECONNECT_MAX_DELAY_SECONDS = 30
    MAX_RECONNECT_ATTEMPTS = 10

    # Depolama ve Kota Eşikleri
    DEFAULT_RETENTION_DAYS = 14        # Varsayılan kayıt saklama süresi (gün)
    MIN_FREE_DISK_PERCENT = 10         # Acil silme tetikleyecek asgari boş disk oranı (%)
    CRITICAL_FREE_DISK_PERCENT = 5     # Kayıt durduracak kritik boş disk oranı (%)
    DEFAULT_CAMERA_QUOTA_GB = 50       # Kamera başına varsayılan kota (GB)

    # Güvenlik ve Oturum
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
    MAX_FAILED_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_MINUTES = 15
    BCRYPT_SALT_ROUNDS = 12


class SystemThresholds:
    """Ondalıklı eşik değerleri (Float sabitler)."""
    DEFAULT_AI_CONFIDENCE: Final[float] = 0.45      # Asgari AI tespit güven skoru
    DEFAULT_MOTION_SENSITIVITY: Final[float] = 0.20 # Hareket algılama duyarlılığı (0.0 - 1.0)
    IOU_TRACK_THRESHOLD: Final[float] = 0.30        # Kısa süreli anonim takip çakışma oranı
