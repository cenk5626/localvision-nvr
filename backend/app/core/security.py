"""
LocalVision NVR - Güvenlik ve Kriptografi Servisi.
- AES-256-GCM: Kamera parolalarının şifreli saklanması
- Bcrypt: Kullanıcı parolalarının güvenli tuzlu hashlenmesi
- PyJWT: Rol tabanlı yetkilendirme jetonları
- SHA-256: Dışa aktarılan video delil bütünlük doğrulaması
"""

import base64
import hashlib
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import bcrypt
import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings
from app.core.constants import SystemDefaults, UserRole


class SecurityManager:
    """Güvenlik, şifreleme ve kimlik doğrulama yöneticisi."""

    def __init__(self):
        # 32 baytlık AES-GCM anahtarını hazırla (SHA256 ile normalize et)
        raw_key = settings.AES_SECRET_KEY.encode("utf-8")
        self._aes_key = hashlib.sha256(raw_key).digest()
        self._aesgcm = AESGCM(self._aes_key)

    # ------------------------------------------------------------------------
    # Parola Yönetimi (Bcrypt)
    # ------------------------------------------------------------------------
    @staticmethod
    def hash_password(plain_password: str) -> str:
        """Kullanıcı parolasını güvenli biçimde hashler."""
        salt = bcrypt.gensalt(rounds=SystemDefaults.BCRYPT_SALT_ROUNDS)
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Kullanıcının girdiği parolayı kayıtlı hash ile doğrular."""
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    # ------------------------------------------------------------------------
    # Gizli Veri Şifreleme (AES-256-GCM - Kamera RTSP/ONVIF Parolaları)
    # ------------------------------------------------------------------------
    def encrypt_secret(self, plain_text: str) -> str:
        """
        Düz metni (örn: kamera parolası) AES-256-GCM ile şifreler.
        Dönüş: Base64 kodlanmış (12 bayt nonce + şifreli metin + tag).
        """
        if not plain_text:
            return ""
        nonce = os.urandom(12)  # 96-bit NIST standard nonce
        encrypted_bytes = self._aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
        payload = nonce + encrypted_bytes
        return base64.b64encode(payload).decode("utf-8")

    def decrypt_secret(self, encrypted_b64: str) -> str:
        """
        AES-256-GCM ile şifrelenmiş metni çözer.
        """
        if not encrypted_b64:
            return ""
        try:
            payload = base64.b64decode(encrypted_b64.encode("utf-8"))
            nonce = payload[:12]
            ciphertext = payload[12:]
            decrypted_bytes = self._aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            raise ValueError(f"Şifreli veri çözülemedi: {e}")

    # ------------------------------------------------------------------------
    # JWT Kimlik Doğrulama Jetonları
    # ------------------------------------------------------------------------
    @staticmethod
    def create_access_token(
        subject: str,
        role: UserRole,
        extra_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Rol ve kullanıcı adı içeren JWT erişim jetonu üretir."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=SystemDefaults.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode: Dict[str, Any] = {
            "sub": subject,
            "role": role.value if isinstance(role, UserRole) else str(role),
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        if extra_claims:
            to_encode.update(extra_claims)

        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def decode_access_token(token: str) -> Dict[str, Any]:
        """JWT erişim jetonunu çözer ve doğrular."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Oturum süresi doldu, lütfen tekrar giriş yapın.")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Geçersiz güvenlik jetonu: {e}")

    # ------------------------------------------------------------------------
    # Video Bütünlük Doğrulama (SHA-256 Checksum)
    # ------------------------------------------------------------------------
    @staticmethod
    def calculate_sha256(file_path: Path | str) -> str:
        """Bir dosyanın SHA-256 bütünlük özetini hesaplar."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")

        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


# Global güvenlik servisi örneği
security = SecurityManager()
