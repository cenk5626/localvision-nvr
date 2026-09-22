"""
LocalVision NVR - Dışa Aktarma ve NAS Yedekleme Servisi (Backup & Export Service).
- Video kliplerini ve kayıtları dışa aktarır (MP4)
- İsteğe bağlı zaman damgası ve kamera adı filigranı (watermark) ekler
- Adli ve denetim güvenliği için SHA-256 bütünlük özeti dosyası üretir (.sha256)
- Yerel klasör veya bağlı NAS (SMB / NFS) hedeflerine otomatik yedekleme yapar
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional
import cv2

from app.core.config import settings
from app.core.constants import AuditAction
from app.core.database import AsyncSessionLocal
from app.core.security import security
from app.models.audit import AuditLog
from app.models.recording import Recording

logger = logging.getLogger(__name__)


class BackupExportService:
    """Video dışa aktarma ve NAS yedekleme yöneticisi."""

    @staticmethod
    def export_video(
        source_path: Path | str,
        camera_name: str,
        add_watermark: bool = True,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Kayıt veya olay klibini dışa aktarır; isteğe bağlı filigran ve SHA-256 özeti ekler.
        """
        src = Path(source_path)
        if not src.exists():
            raise FileNotFoundError(f"Kaynak video dosyası bulunamadı: {src}")

        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        export_filename = f"EXPORT_{camera_name}_{timestamp_str}.mp4"
        export_path = settings.EXPORTS_DIR / export_filename

        if not add_watermark:
            # Doğrudan kopyala (Stream copy / zero CPU)
            shutil.copy2(src, export_path)
        else:
            # Filigran (Zaman damgası, kamera adı ve sistem adı) ekleyerek yeniden kodla
            cap = cv2.VideoCapture(str(src))
            if not cap.isOpened():
                raise RuntimeError(f"Video açılamadı: {src}")

            fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(export_path), fourcc, fps, (w, h))

            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                # Alt şerit filigranı (Semi-transparent banner)
                watermark_text = f"LocalVision NVR | Kamera: {camera_name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                cv2.rectangle(frame, (10, h - 45), (w - 10, h - 10), (0, 0, 0), -1)
                cv2.putText(
                    frame,
                    watermark_text,
                    (20, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA
                )
                writer.write(frame)

            cap.release()
            writer.release()

        # SHA-256 bütünlük özetini hesapla
        sha256_hash = security.calculate_sha256(export_path)

        # Yanına .sha256 doğrulama dosyasını yaz
        checksum_file = export_path.with_suffix(".mp4.sha256")
        checksum_file.write_text(f"{sha256_hash}  {export_filename}\n", encoding="utf-8")

        # Metaveri dosyasını yaz (.json)
        meta_file = export_path.with_suffix(".mp4.json")
        meta_content = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "camera_name": camera_name,
            "filename": export_filename,
            "sha256": sha256_hash,
            "has_watermark": add_watermark,
            "notes": notes or ""
        }
        meta_file.write_text(json.dumps(meta_content, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info(f"Video dışa aktarıldı: {export_filename} (SHA256: {sha256_hash[:16]}...)")

        return {
            "export_file": str(export_path),
            "filename": export_filename,
            "sha256": sha256_hash,
            "size_bytes": export_path.stat().st_size
        }

    @staticmethod
    def sync_to_nas(nas_destination_path: str) -> Dict[str, Any]:
        """
        Yerel kayıt dizinini bağlı NAS klasörüne yedekler.
        """
        nas_dir = Path(nas_destination_path)
        if not nas_dir.exists():
            raise FileNotFoundError(f"NAS hedef dizinine erişilemiyor: {nas_destination_path}")

        backed_up_files = 0
        total_bytes = 0

        # Sadece son 3 günün kayıtlarını ve tüm olay kliplerini aktar
        for item in settings.STORAGE_DIR.rglob("*.mp4"):
            rel_path = item.relative_to(settings.STORAGE_DIR)
            dest_file = nas_dir / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            if not dest_file.exists() or dest_file.stat().st_size != item.stat().st_size:
                shutil.copy2(item, dest_file)
                backed_up_files += 1
                total_bytes += item.stat().st_size

        return {
            "backed_up_files": backed_up_files,
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / (1024 ** 2), 2),
            "nas_path": str(nas_dir)
        }


backup_service = BackupExportService()
