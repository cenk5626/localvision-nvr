# LocalVision NVR — Yerel Ağ Odaklı & Gizlilik Tasarımlı Video Güvenlik Sistemi

<div align="center">
  <h3>Uçtan Uca, Çevrimdışı Çalışabilen, İnsan & Araç Algılamalı Akıllı NVR / VMS</h3>
  <p><b>Ev, Apartman, Ofis ve Depo Güvenliği İçin Tam Kontrol</b></p>
</div>

---

## 🌟 Temel Özellikler

1. **Katı Gizlilik Tasarımı (Privacy by Design):**
   - Yalnızca **insan** (`person`) ve **araç** (`car`, `motorcycle`, `bus`, `truck`) tespiti yapılır.
   - **Yüz tanıma, yüz veritabanı veya biyometrik profil çıkarma kesinlikle bulunmaz.**
   - Nesne takibi yalnızca aynı kamera içindeki çizgi ihlali ve bekleme süresi hesabı için geçici, anonim kimliklerle sınırlıdır.
2. **%100 Çevrimdışı ve Yerel Ağ Çalışma Garantisi:**
   - İnternet bağlantısı kesildiğinde canlı izleme, kayıt, yapay zekâ tespiti ve kullanıcı girişi sıfır aksama ile çalışmaya devam eder.
   - Dışarıya hiçbir veri aktarılmaz; bulut bağımlılığı yoktur.
3. **Kamera Uyumluluğu:**
   - Standart **RTSP** akışları (`rtsp://...`).
   - **ONVIF** Profile S/T cihaz keşfi (WS-Discovery).
   - **Bilgisayarınızın Dahili/Harici Web Kamerası (Webcam 0)** ile anında test edebilme.
   - H.264 / H.265 desteği, otomatik yeniden bağlanma (Exponential Backoff).
4. **Düşük Gecikmeli Canlı Yayın & Çoklu Ekran:**
   - Tarayıcıda ek yazılım/eklenti gerektirmeyen düşük gecikmeli canlı akış.
   - Tekli, 2x2, 3x3 ve 4x4 matris görünümleri.
5. **Segmentli Kayıt & Olay Öncesi Tampon (Ring Buffer):**
   - Sürekli segmentli MP4 kayıtları.
   - Olay tetiklendiğinde olay anından **5 saniye öncesi** ve **10 saniye sonrasını** içeren akıllı olay klipleri.
6. **İleri Düzey Algılama Kuralları:**
   - Kamera üzerinde etkileşimli çokgen yasak alan (ROI) çizimi.
   - Sanal çizgi geçişi (Tripwire).
   - Bölgede uzun süre kalma (Dwell time / Loitering) uyarısı.
7. **Depolama, Kota & Korumalı Yer İmleri:**
   - Kota veya saklama süresi dolduğunda en eski kayıtlar otomatik temizlenir.
   - **Korumalı / Yıldızlı kayıtlar asla silinmez.**
   - Adli kanıt niteliğinde **SHA-256 bütünlük doğrulaması** ve filigranlı MP4 dışa aktarma.
8. **Güvenlik & RBAC:**
   - 4 seviyeli rol yetkilendirmesi: `Sistem Yöneticisi`, `Operatör`, `İzleyici`, `Kullanıcı`.
   - Kamera şifreleri **AES-256-GCM** ile şifrelenir; kullanıcı şifreleri **bcrypt** ile korunur.
   - Değiştirilemez denetim günlüğü (Audit Log).

---

## 🏗️ Sistem Mimarisi

```
+-------------------------------------------------------------+
|                      LocalVision NVR                         |
+-------------------------------------------------------------+
   │
   ├─► [Kameralar]: RTSP, ONVIF, PC Web Kamerası (DirectShow)
   │
   ├─► [Çekirdek Motor]: 
   │     ├─ Stream Ingest (OpenCV / FFmpeg Pipeline)
   │     ├─ Ring Buffer (5 sn pre-event RAM tamponu)
   │     └─ Segmented MP4 Recorder
   │
   ├─► [Yapay Zekâ Servisi]:
   │     ├─ YOLOv8 / ONNX (Yalnızca İnsan & Araç, Yüz YASAK)
   │     └─ Zone Analyzer (ROI Çokgen, Tripwire, Dwell Time)
   │
   ├─► [FastAPI Backend]:
   │     ├─ JWT & AES-256-GCM Güvenlik Katmanı
   │     ├─ RBAC Yetkilendirme & Denetim Günlüğü
   │     └─ SQLite WAL / PostgreSQL Uyumlu Veritabanı
   │
   └─► [React + TypeScript Web Paneli]:
         ├─ Genel Durum & Metrikler
         ├─ 1x1, 2x2, 3x3, 4x4 Canlı İzleme
         ├─ İnteraktif Bölge Çizim Aracı
         ├─ Zaman Çizelgesi & Geçmiş Kayıt Oynatıcı
         └─ Depolama & NAS Senkronizasyon Arayüzü
```

---

## 🚀 Hızlı Başlangıç

### Seçenek 1: Windows 10/11 Üzerinde Tek Tıkla Başlatma

1. Depo ana dizinindeki **`start_windows.bat`** dosyasına çift tıklayın.
2. Tarayıcınızda otomatik olarak açılacak olan `http://localhost:5173` adresine gidin.
3. İlk giriş bilgileri:
   - **Kullanıcı Adı:** `admin`
   - **Parola:** `Admin*LocalVision2026!`
4. Bilgisayarınızın web kamerası otomatik olarak eklenmiş olacaktır. Kameranın karşısına geçerek insan algılamayı anında test edebilirsiniz!

### Seçenek 2: Manuel Başlatma

```bash
# 1. Backend Servisini Başlatın:
cd backend
pip install -r requirements.txt
python run_server.py

# 2. Frontend Panelini Başlatın (Ayrı terminal):
cd frontend
npm install
npm run dev
```

### Seçenek 3: Docker Compose ile Dağıtım (Linux Sunucu / NAS)

```bash
docker compose -f docker/docker-compose.yml up -d --build
```
Web paneline `http://<Sunucu_IP_Adresi>` üzerinden erişebilirsiniz.

### Seçenek 4: Vercel Üzerinde Canlı Web Dağıtımı

LocalVision NVR kullanıcı arayüzü, Vercel üzerinde tek tıkla canlı web sitesi olarak barındırılabilir:

1. Bu depoyu GitHub hesabınıza çatallayın veya içe aktarın (Import).
2. [Vercel Dashboard](https://vercel.com/new)'a gidin ve depoyu seçin.
3. Ayarları kontrol edin:
   - **Root Directory:** `frontend` (veya kök dizin - `vercel.json` otomatik algılar)
   - **Framework Preset:** `Vite`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. **Deploy** butonuna tıklayın.
5. Vercel canlı sitesinde:
   - **✨ Demo Modu (Vercel Vitrin):** Ziyaretçiler backend olmadan simüle kameralar ve canlı olayları anında test edebilir.
   - **Kendi NVR Sunucunuza Bağlanma:** Ayarlar menüsünden kendi ev/ofis NVR backend adresinizi (`VITE_API_URL` veya Cloudflare Tunnel / Ngrok adresi) girerek fiziksel kameralarınızı Vercel web sitenizden güvenle yönetebilirsiniz.


---

## 💻 Bilgisayarınızın Kamerası ile Test Etme

1. Giriş yaptıktan sonra **Canlı İzleme** sekmesine gidin.
2. Sistem, bilgisayarınızın web kamerasını (`Webcam 0`) otomatik açar.
3. Kamera açısında bir insan belirdiğinde:
   - Gerçek zamanlı yeşil tespit kutusu belirir.
   - Olay Merkezi'ne 5 saniye öncesini de içeren MP4 video klibi ve anlık görüntü kaydedilir.
4. **Kameralar** sayfasından *"Bölgeleri Çiz"* butonuna basarak kameranız üzerinde çokgen bir yasak alan çizip ihlal testleri gerçekleştirebilirsiniz.

---

## 🛡️ Güvenlik ve Gizlilik Garantileri

- **Yüz Tanıma ve Biyometri Yasağı:** Sistem kodunda yüz algılama, yüz tanıma veya kişi profilleme bileşenleri bulunmaz.
- **Şifreli Depolama:** Kamera bağlantı parolaları veritabanında AES-256-GCM ile şifreli tutulur.
- **Dışa Aktarma Güvenliği:** İndirilen videolara isteğe bağlı zaman damgası eklenir ve yanında adli geçerlilik için SHA-256 doğrulama özeti (`.sha256`) oluşturulur.
- **Korumalı Kayıtlar:** Depolama alanı azaldığında yalnızca yıldızsız ve saklama süresi dolmuş kayıtlar silinir. Korumalı kayıtlar silinmez.
- **Uzaktan Erişim Uyarısı:** Güvenliğiniz için modeminize port açmayın; uzaktan erişim gerektiğinde WireGuard veya Tailscale VPN kullanın.

---

## 📚 Dokümantasyon Bağlantıları

- [Windows 10/11 Kurulum ve Webcam Test Rehberi](docs/WINDOWS_SETUP.md)
- [Linux Sunucu Kurulum Rehberi](docs/LINUX_SETUP.md)
- [NAS (Synology, QNAP, TrueNAS) Kurulum Rehberi](docs/NAS_SETUP.md)
- [KVKK ve GDPR Gizlilik Denetim Listesi](docs/PRIVACY_CHECKLIST.md)
- [REST ve WebSocket API Referansı](docs/API_REFERENCE.md)
