"""
LocalVision NVR - Depolama ve Otomatik Budama (Retention) Testleri.
Yer imli ve korumalı kayıtların silinmeme garantisi.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import pytest
from app.core.constants import RecordingMode
from app.core.database import AsyncSessionLocal, init_db
from app.models.camera import Camera
from app.models.recording import Recording
from app.services.retention_svc import retention_service


@pytest.mark.asyncio
async def test_disk_usage_metrics():
    """Disk metrikleri hesaplama testi."""
    usage = retention_service.get_disk_usage()
    assert "total_gb" in usage
    assert "used_gb" in usage
    assert "free_gb" in usage
    assert "free_percent" in usage
    assert 0 <= usage["free_percent"] <= 100


@pytest.mark.asyncio
async def test_protected_bookmark_retention():
    """
    KATI KORUMA TESTİ:
    Süresi dolmuş olsa bile yer imli (is_bookmarked=True) kayıtlar asla silinmemelidir!
    """
    await init_db()

    async with AsyncSessionLocal() as session:
        # Geçici kamera oluştur
        cam = Camera(name="Test Retention Cam", source_type="webcam")
        session.add(cam)
        await session.commit()
        await session.refresh(cam)

        # 1. Eski normal kayıt (Silinmeli)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"old video content")
            expired_path = f.name

        old_rec = Recording(
            camera_id=cam.id,
            file_path=expired_path,
            file_name="old_video.mp4",
            file_size_bytes=100,
            start_time=datetime.now(timezone.utc) - timedelta(days=30),  # 30 gün önce
            is_bookmarked=False,
            is_protected=False
        )

        # 2. Eski YER İMLİ kayıt (KORUNMALI)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"protected bookmark video content")
            bookmarked_path = f.name

        bookmarked_rec = Recording(
            camera_id=cam.id,
            file_path=bookmarked_path,
            file_name="bookmarked_video.mp4",
            file_size_bytes=100,
            start_time=datetime.now(timezone.utc) - timedelta(days=30),  # 30 gün önce
            is_bookmarked=True,   # Yer İmli!
            is_protected=True     # Korumalı!
        )

        session.add_all([old_rec, bookmarked_rec])
        await session.commit()
        old_id = old_rec.id
        bookmarked_id = bookmarked_rec.id

    # Retention döngüsünü 14 günlük saklama politikası ile çalıştır
    deleted_count, freed_bytes = await retention_service.run_retention_cycle(default_retention_days=14)

    assert deleted_count >= 1

    # Veritabanını kontrol et
    async with AsyncSessionLocal() as session:
        # Normal eski kayıt silinmiş olmalı
        res_old = await session.get(Recording, old_id)
        assert res_old is None

        # Yer imli kayıt veritabanında DURUYOR olmalı
        res_bookmarked = await session.get(Recording, bookmarked_id)
        assert res_bookmarked is not None
        assert res_bookmarked.is_bookmarked is True

    # Yer imli dosya diskte de duruyor olmalı
    assert Path(bookmarked_path).exists() is True

    # Temizlik
    Path(bookmarked_path).unlink(missing_ok=True)
    Path(expired_path).unlink(missing_ok=True)
