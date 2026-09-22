"""
LocalVision NVR - Güvenlik ve Kriptografi Testleri.
- Bcrypt Parola Hashleme & Doğrulama
- AES-256-GCM Kamera Parolası Şifreleme & Çözme
- JWT Token Üretimi & Çözümleme
- SHA-256 Dosya Bütünlük Doğrulama
"""

from datetime import timedelta
from pathlib import Path
import tempfile
import pytest
from app.core.constants import UserRole
from app.core.security import SecurityManager, security


def test_password_hashing():
    """Bcrypt parola hashleme ve doğrulaması test edilir."""
    raw_password = "SecurePassword2026!"
    hashed = security.hash_password(raw_password)

    assert hashed != raw_password
    assert hashed.startswith("$2b$")
    assert security.verify_password(raw_password, hashed) is True
    assert security.verify_password("WrongPassword123", hashed) is False


def test_aes_gcm_camera_password_encryption():
    """AES-256-GCM kamera parolasını şifreler ve aslına çözer."""
    cam_secret = "RTSP_Cam_Secret_99#"
    encrypted = security.encrypt_secret(cam_secret)

    assert encrypted != cam_secret
    assert len(encrypted) > 20

    decrypted = security.decrypt_secret(encrypted)
    assert decrypted == cam_secret


def test_jwt_token_creation_and_decoding():
    """JWT erişim jetonu üretimi ve rol doğrulaması test edilir."""
    username = "test_operator"
    role = UserRole.OPERATOR

    token = security.create_access_token(
        subject=username,
        role=role,
        extra_claims={"user_id": 42}
    )

    payload = security.decode_access_token(token)
    assert payload["sub"] == username
    assert payload["role"] == UserRole.OPERATOR.value
    assert payload["user_id"] == 42


def test_jwt_expired_token_rejection():
    """Süresi dolmuş jeton reddedilmelidir."""
    token = security.create_access_token(
        subject="expired_user",
        role=UserRole.VIEWER,
        expires_delta=timedelta(seconds=-10)  # Geçmişte sonlanmış
    )

    with pytest.raises(ValueError, match="Oturum süresi doldu"):
        security.decode_access_token(token)


def test_sha256_file_checksum():
    """Dosya bütünlük özeti (SHA-256) hesaplaması doğrulanır."""
    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        f.write(b"LocalVision Video Export Integrity Content")
        temp_path = f.name

    try:
        checksum = security.calculate_sha256(temp_path)
        assert len(checksum) == 64
        # Aynı içerik için deterministik olmalı
        checksum2 = security.calculate_sha256(temp_path)
        assert checksum == checksum2
    finally:
        Path(temp_path).unlink(missing_ok=True)
