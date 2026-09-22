# LocalVision NVR — REST & WebSocket API Referansı

LocalVision NVR, tüm işlevlerini RESTful HTTP endpoint'leri ve gerçek zamanlı WebSocket kanalı üzerinden sunar.
Etkileşimli Swagger dokümantasyonuna sistem çalışırken `http://localhost:8000/docs` adresinden erişebilirsiniz.

---

## 1. Kimlik Doğrulama (Authentication)

### Giriş Yap ve Jeton Al
- **Endpoint:** `POST /api/auth/login`
- **İstek Gövdesi:**
```json
{
  "username": "admin",
  "password": "Admin*LocalVision2026!"
}
```
- **Örnek cURL:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin", "password":"Admin*LocalVision2026!"}'
```
- **Cevap:**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "admin",
  "role": "admin",
  "allowed_camera_ids": []
}
```

### Profil Bilgilerini Al
- **Endpoint:** `GET /api/auth/me`
- **Başlık:** `Authorization: Bearer <TOKEN>`

---

## 2. Kameralar (Cameras)

### Kamera Listesi
- **Endpoint:** `GET /api/cameras`
- **Başlık:** `Authorization: Bearer <TOKEN>`

### Yeni Kamera Ekle
- **Endpoint:** `POST /api/cameras`
- **Örnek cURL (PC Web Kamerası):**
```bash
curl -X POST http://localhost:8000/api/cameras \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PC Kameram",
    "source_type": "webcam",
    "webcam_index": 0,
    "fps": 20,
    "recording_mode": "continuous",
    "detection_enabled": true
  }'
```

### Bağlantıyı Test Et (Kaydetmeden Önce)
- **Endpoint:** `POST /api/cameras/test-connection`
```json
{
  "source_type": "webcam",
  "webcam_index": 0
}
```

### Bilgisayara Bağlı Web Kameralarını Keşfet
- **Endpoint:** `GET /api/cameras/discover-webcams`

### Yerel Ağdaki ONVIF Kameraları Keşfet
- **Endpoint:** `GET /api/cameras/discover-onvif`

### Canlı Düşük Gecikmeli MJPEG Akışı
- **Endpoint:** `GET /api/cameras/{camera_id}/live.mjpeg`
> Bu endpoint doğrudan HTML `<img src="/api/cameras/1/live.mjpeg" />` etiketi ile tarayıcıda sıfır eklentiyle canlı görüntü verir.

---

## 3. Olay Merkezi (Events)

### Olayları Filtrele ve Listele
- **Endpoint:** `GET /api/events?camera_id=1&event_type=person_detected&limit=50`
- **Cevap:**
```json
[
  {
    "id": 12,
    "camera_id": 1,
    "camera_name": "PC Kameram",
    "event_type": "person_detected",
    "confidence": 0.92,
    "snapshot_url": "/api/events/12/snapshot",
    "clip_url": "/api/events/12/clip",
    "is_bookmarked": false,
    "created_at": "2026-09-13T02:00:00Z"
  }
]
```

### Olayı Yer İmine Ekle / Çıkar
- **Endpoint:** `POST /api/events/{event_id}/bookmark`
```json
{
  "is_bookmarked": true,
  "bookmark_note": "Şüpheli giriş denemesi"
}
```

---

## 4. Geçmiş Kayıtlar (Recordings)

### Zaman Çizelgesi Kayıt Segmentleri
- **Endpoint:** `GET /api/recordings?camera_id=1&date=2026-09-13`

### Kayıt Oynatma (Video Range Streaming)
- **Endpoint:** `GET /api/recordings/{recording_id}/stream`
> HTTP 206 Partial Content desteği ile tarayıcıda ileri/geri sarma destekler.

### Videoyu Filigran ve SHA-256 İle Dışa Aktar
- **Endpoint:** `POST /api/recordings/{recording_id}/export`
```json
{
  "add_watermark": true,
  "notes": "Adli makamlara teslim edilecek kopya"
}
```

---

## 5. Depolama & Yedekleme (Storage)

### Disk Durumu ve Kotalar
- **Endpoint:** `GET /api/storage/status`

### Süresi Dolanları Şimdi Temizle (Prune Now)
- **Endpoint:** `POST /api/storage/prune-now`

### NAS Yedekleme Tetikle
- **Endpoint:** `POST /api/storage/backup-nas`
```json
{
  "nas_path": "\\\\192.168.1.50\\guvenlik_yedek"
}
```

---

## 6. Sistem & Metrikler (System)

### Sistem Sağlık Kontrolü
- **Endpoint:** `GET /api/system/health`

### Gizlilik Kontrol Listesi
- **Endpoint:** `GET /api/system/privacy-checklist`

### Denetim Günlükleri (Audit Logs)
- **Endpoint:** `GET /api/system/audit-logs?limit=50`

---

## 7. Gerçek Zamanlı WebSocket Kanalı

- **WebSocket URL:** `ws://localhost:8000/api/ws/events`
- Sistemde yeni bir insan/araç veya kural ihlali oluştuğunda anlık JSON paketi iletir:
```json
{
  "type": "new_event",
  "id": 15,
  "camera_id": 1,
  "camera_name": "PC Kameram",
  "event_type": "person_detected",
  "created_at": "2026-09-13T02:05:00Z",
  "snapshot_url": "/api/events/15/snapshot"
}
```
