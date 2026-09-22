# LocalVision NVR — Windows 10/11 Kurulum ve Kullanım Rehberi

Bu rehber, **LocalVision NVR** sistemini Windows 10 veya Windows 11 üzerinde yerel olarak çalıştırma ve **bilgisayarınızın dahili/harici web kamerasını (Camera 0)** anında güvenlik kamerası olarak kullanma adımlarını içerir.

---

## 1. Ön Gereksinimler

Sisteminizde aşağıdaki araçların yüklü olması yeterlidir:
- **Python 3.11 veya 3.12** (Yüklerken *"Add Python to PATH"* kutucuğunu işaretleyin)
- **Node.js v18 veya üzeri** (v20+ önerilir)

---

## 2. Tek Tıkla Başlatma (En Kolay Yol)

Proje ana dizininde bulunan **`start_windows.bat`** dosyasına çift tıklayın:
1. Betik sistem gereksinimlerini denetler.
2. Backend API ve Video Motorunu (Port 8000) ayrı bir konsol penceresinde başlatır.
3. Frontend Web Yönetim Panelini (Port 5173) başlatır.
4. Tarayıcınızda otomatik olarak `http://localhost:5173` adresini açar.

---

## 3. Manuel Başlatma Adımları (PowerShell veya CMD)

### Adım 1: Backend Servisini Başlatın
```powershell
# Proje ana dizininde:
cd "c:\Users\cenke\OneDrive\Desktop\kamera insan yakalama"

# Gerekli kütüphaneleri yükleyin (Daha önce yapılmadıysa):
pip install -r backend/requirements.txt

# Backend'i çalıştırın:
python backend/run_server.py
```
> Backend başarıyla açıldığında `http://localhost:8000/docs` adresinden Swagger API arayüzüne erişebilirsiniz.

### Adım 2: Frontend Yönetim Panelini Başlatın
Ayrı bir terminal penceresi açın:
```powershell
cd "c:\Users\cenke\OneDrive\Desktop\kamera insan yakalama\frontend"

# Bağımlılıkları yükleyin:
npm install

# Geliştirme sunucusunu başlatın:
npm run dev
```
> Web paneline `http://localhost:5173` adresinden ulaşabilirsiniz.

---

## 4. Bilgisayarınızın Web Kamerası ile Canlı Test Yapma

LocalVision NVR, ilk açılışta bilgisayarınızın web kamerasını (`Camera 0 - DirectShow`) otomatik olarak sisteme ekler.

1. `http://localhost:5173` adresine gidin.
2. Giriş bilgileriyle oturum açın:
   - **Kullanıcı Adı:** `admin`
   - **Parola:** `Admin*LocalVision2026!`
3. **Canlı İzleme** sekmesine tıklayın. Bilgisayarınızın kamerasından canlı 20 FPS video akışını göreceksiniz.
4. Kameranın karşısına geçtiğinizde:
   - Yapay zekâ sizi anında yeşil kutu ve `person` etiketiyle tespit edecektir.
   - **Olay Merkezi** sekmesine anlık bir olay (küçük resim snapshot ve 5 saniye öncesini içeren video klibi) eklenecektir.
5. **Kameralar** sekmesinden *"Bölgeleri Çiz"* butonuna basarak kameranız üzerinde çokgen bir yasak alan (ROI) veya sanal çizgi (Tripwire) çizebilir, çizgiye yaklaştığınızda alarm tetiklendiğini test edebilirsiniz.

---

## 5. RTSP / ONVIF IP Kamera Ekleme

1. **Kameralar** sekmesinde **"Yeni Kamera Ekle"** butonuna tıklayın.
2. Eğer kameranız ağa bağlıysa **"Ağdaki ONVIF Kameraları Tara"** butonuna basın; kamera otomatik tespit edilecektir.
3. Manuel eklemek için:
   - Kaynak Türü: `RTSP Akışı`
   - RTSP URL: `rtsp://kullanici:sifre@192.168.1.150:554/stream1`
   - **"Akışı Test Et"** butonuna basarak çözünürlük ve bağlantıyı doğrulayın.
   - **"Kamerayı Ekle"** butonuna basarak kaydedin.

---

## 6. Windows Güvenlik Duvarı İpuçları

Aynı yerel ağdaki (Wi-Fi veya Ethernet) telefon, tablet veya diğer bilgisayarlardan sisteme girmek için:
1. Windows Güvenlik Duvarı'ndan **8000** ve **5173** portlarına yerel ağda izin verin.
2. Diğer cihazınızın tarayıcısından `http://<Bilgisayar_IP_Adresiniz>:5173` adresine girin.
