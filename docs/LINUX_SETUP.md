# LocalVision NVR — Linux Sunucu Kurulum Rehberi (Ubuntu / Debian)

Bu rehber, **LocalVision NVR** sistemini yerel bir Linux sunucusunda (Ubuntu 22.04 / 24.04 LTS veya Debian 12) doğrudan yerel servis olarak veya **Docker Compose** ile kurma adımlarını açıklar.

---

## 1. Yöntem: Docker Compose ile Kurulum (Önerilen)

Docker kurulu bir Linux sunucuda sistemi tek komutla ayağa kaldırabilirsiniz.

### Adım 1: Depoyu Sunucuya Kopyalayın
```bash
cd /opt
git clone <repo_url> localvision-nvr
cd localvision-nvr
```

### Adım 2: Docker Compose ile Başlatın
```bash
docker compose -f docker/docker-compose.yml up -d --build
```

### Adım 3: Durumu Kontrol Edin
```bash
docker compose -f docker/docker-compose.yml ps
docker logs -f localvision_backend
```
Sistem `http://<Sunucu_IP_Adresi>` adresinden yayına başlayacaktır.

---

## 2. Yöntem: Yerel Python & Systemd Servisi Olarak Kurulum

### Adım 1: Sistem Bağımlılıklarını Yükleyin
```bash
sudo apt update && sudo apt install -y \
  python3 \
  python3-pip \
  python3-venv \
  nodejs \
  npm \
  libgl1 \
  libglib2.0-0 \
  ffmpeg
```

### Adım 2: Sanal Ortam ve Python Paketleri
```bash
cd /opt/localvision-nvr
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Adım 3: Frontend Derlemesi
```bash
cd /opt/localvision-nvr/frontend
npm install
npm run build
```

### Adım 4: Systemd Servisi Oluşturun
`/etc/systemd/system/localvision.service`:
```ini
[Unit]
Description=LocalVision NVR Backend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/localvision-nvr/backend
ExecStart=/opt/localvision-nvr/venv/bin/python run_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Servisi etkinleştirin ve başlatın:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now localvision.service
```

---

## 3. Güvenlik Duvarı (UFW) Yapılandırması
```bash
# Yerel ağdan erişim için:
sudo ufw allow 8000/tcp comment "LocalVision API"
sudo ufw allow 80/tcp comment "LocalVision Web"
```
