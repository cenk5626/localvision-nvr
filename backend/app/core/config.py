"""
LocalVision NVR - Sistem Yapılandırması (Pydantic Settings).
Tüm hassas veriler ortam değişkenlerinden okunur (.env); varsayılanlar güvenli şekilde atanır.
"""

import os
from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import SystemDefaults


class Settings(BaseSettings):
    """Uygulama ayarları."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Temel Uygulama Bilgileri
    APP_NAME: str = "LocalVision NVR"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    OFFLINE_ONLY: bool = True  # Dış internete bağımlılığı engelle

    # Ağ ve Portlar
    HOST: str = "0.0.0.0"
    PORT: int = SystemDefaults.DEFAULT_API_PORT
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    # Güvenlik ve Şifreleme Anahtarları
    # Üretim ortamında .env dosyasından güçlü anahtarlar verilmelidir.
    JWT_SECRET_KEY: str = Field(
        default="localvision_nvr_secure_jwt_token_secret_key_change_in_prod_2026",
        description="JWT imzalama anahtarı"
    )
    JWT_ALGORITHM: str = "HS256"
    AES_SECRET_KEY: str = Field(
        default="localvision_aes_256_gcm_32byte_master_secret_key!",  # 32 bytes
        description="Kamera parolalarını şifreleme anahtarı (AES-256)"
    )

    # Veritabanı (Varsayılan: Yerel SQLite WAL, PostgreSQL destekler)
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/localvision.db"

    # Depolama Yolları
    DATA_DIR: Path = Path("./data")
    STORAGE_DIR: Path = Path("./data/recordings")
    SNAPSHOTS_DIR: Path = Path("./data/snapshots")
    EXPORTS_DIR: Path = Path("./data/exports")
    MODELS_DIR: Path = Path("./models")
    TEMP_DIR: Path = Path("./data/temp")

    # İlk Kurulum Yönetici Hesabı
    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_PASSWORD: str = "Admin*LocalVision2026!"
    FIRST_ADMIN_EMAIL: str = "admin@localvision.local"

    # Yapay Zeka Ayarları
    AI_ENABLED: bool = True
    AI_USE_GPU: bool = True
    AI_MODEL_NAME: str = "yolov8n.onnx"
    AI_FALLBACK_TO_OPENCV: bool = True


# Tekil ayar nesnesi (Singleton)
settings = Settings()

# Gerekli dizinlerin otomatik oluşturulması
for directory in [
    settings.DATA_DIR,
    settings.STORAGE_DIR,
    settings.SNAPSHOTS_DIR,
    settings.EXPORTS_DIR,
    settings.MODELS_DIR,
    settings.TEMP_DIR
]:
    directory.mkdir(parents=True, exist_ok=True)
