"""
LocalVision NVR - Sunucu Başlatıcı.
Windows, Linux ve NAS ortamlarında backend servisini ayağa kaldırır.
"""

import os
import sys
from pathlib import Path
import uvicorn

# backend kök dizinini Python arama yoluna ekle
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from app.core.config import settings

if __name__ == "__main__":
    print("=" * 65)
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    print("  Yerel Ağ Odaklı & Gizlilik Tasarımlı Video Güvenlik Sistemi")
    print(f"  API Adresi: http://{settings.HOST}:{settings.PORT}")
    print(f"  Swagger Dokümantasyonu: http://localhost:{settings.PORT}/docs")
    print("=" * 65)

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_level="info"
    )
