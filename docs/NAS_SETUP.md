# LocalVision NVR — NAS Kurulum Rehberi (Synology / QNAP / TrueNAS)

Bu rehber, **LocalVision NVR** sistemini Docker destekleyen popüler Ağ Depolama (NAS) cihazlarında çalıştırma ve kayıt hedeflerini NAS depolama havuzlarına bağlama adımlarını içerir.

---

## 1. Synology DSM (Container Manager) Kurulumu

### Adım 1: Klasör Yapısını Hazırlayın
Synology DSM **File Station** üzerinde aşağıdaki paylaşılan klasörü oluşturun:
- `/volume1/docker/localvision`
- `/volume1/docker/localvision/data`
- `/volume1/docker/localvision/data/recordings`
- `/volume1/docker/localvision/models`

### Adım 2: Docker Compose Projesi Ekleyin
1. Synology DSM menüsünden **Container Manager** uygulamasını açın.
2. Sol menüden **Project (Proje)** sekmesine gelin ve **Oluştur (Create)** butonuna tıklayın.
3. Proje Adı: `localvision-nvr`
4. Yol: `/volume1/docker/localvision`
5. Kaynak: `docker-compose.yml yükle` veya aşağıdaki metni yapıştırın:

```yaml
version: '3.8'

services:
  backend:
    image: localvision_backend:latest
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    container_name: localvision_backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - /volume1/docker/localvision/data:/app/backend/data
      - /volume1/docker/localvision/models:/app/models
    environment:
      - OFFLINE_ONLY=true
      - DATABASE_URL=sqlite+aiosqlite:///./data/localvision.db

  frontend:
    image: localvision_frontend:latest
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend
    container_name: localvision_frontend
    restart: unless-stopped
    ports:
      - "8080:80"
    depends_on:
      - backend
```

6. Projeyi başlatın. Web paneline `http://<Synology_IP>:8080` adresinden erişebilirsiniz.

---

## 2. QNAP (Container Station) Kurulumu

1. QNAP QTS menüsünden **Container Station** uygulamasını açın.
2. **Applications (Uygulamalar)** sekmesinden **Create (Oluştur)** butonuna basın.
3. Uygulama Adı: `localvision`
4. YAML içeriği olarak yukarıdaki Docker Compose tanımını girin.
5. Volume eşlemelerini QNAP paylaşımlı klasörünüzle (`/share/CACHEDEV1_DATA/localvision`) eşleştirin.

---

## 3. NAS Depolama & SMB / NFS Yedekleme Entegrasyonu

LocalVision NVR, ana kayıtlarını doğrudan yerel diskte tutarken isteğe bağlı olarak ikincil bir NAS paylaşımına otomatik kopyalama (senkronizasyon) yapabilir.

1. Web paneline giriş yapın (`admin`).
2. **Depolama** sekmesine geçin.
3. **Ağ Depolama / NAS Yedekleme** alanında:
   - **NAS Paylaşım Yolu:**
     - Windows UNC yolu: `\\192.168.1.50\guvenlik_yedek`
     - Linux / Mount yolu: `/mnt/nas/guvenlik_yedek`
   - **Zaman Planı:** Günlük (Her gece) veya Haftalık seçin.
4. **"NAS'a Şimdi Yedekle"** butonuna basarak anlık aktarımı test edin.
