# LocalVision NVR — Gizlilik ve Yasal Uyum Rehberi (Privacy Checklist)

LocalVision NVR, temelinden itibaren **Tasarım İtibarıyla Gizlilik (Privacy by Design)** ilkeleri gözetilerek mimarileştirilmiştir. Bu doküman, sistemin gizlilik sınırlarını ve kameraların kurulduğu mülklerde (ev, apartman, işyeri, depo) uyulması gereken yasal yükümlülükleri içerir.

---

## 1. Sistemin Yerleşik Gizlilik Sınırları

LocalVision NVR kaynak kodunda ve yapay zekâ motorunda aşağıdaki katı sınırlar uygulanmaktadır:

| Güvenlik / Gizlilik Unsuru | Durum | Teknik Açıklama |
|---|---|---|
| **Yüz Tanıma (Facial Recognition)** | ❌ **KESİNLİKLE YOK** | Yüz veri tabanı, yüz öznitelik vektörü veya yüz tanıma modeli bulunmaz. |
| **Biyometrik Kimlik Tespiti** | ❌ **KESİNLİKLE YOK** | Kişilerin biyometrik verileri işlenmez. |
| **İsimle Kişi Takibi** | ❌ **KESİNLİKLE YOK** | İsimle kişi takip özelliği içermez. |
| **Kısa Süreli Anonim Takip** | ✔️ **SADECE ANLIK** | Yalnızca aynı kamera içinde çizgi geçişi ve bekleme süresi hesabı için geçici `track_id` tutulur; 3 saniye sonra bellekten tamamen silinir. |
| **Bulut Veri Aktarımı** | ❌ **KESİNLİKLE YOK** | Tüm video işleme, depolama ve analiz %100 yerel ağda (offline) gerçekleşir. |
| **Kamera Parolaları Güvenliği** | ✔️ **AES-256-GCM** | Kamera şifreleri veritabanında asla açık metin tutulmaz, yerel anahtarla şifrelenir. |
| **Kullanıcı Parolaları** | ✔️ **BCRYPT** | Bcrypt (tuzlu) algoritmasıyla hashlenir. |
| **Değiştirilemez Denetim Günlüğü** | ✔️ **AKTİF** | Her izleme, indirme, silme ve yetki değişikliği denetim günlüğüne kaydedilir. |

---

## 2. Yasal Mevzuat ve Saha Uygulama Kontrol Listesi (KVKK / GDPR)

Bir mülke IP kamera kurarken ve işletirken veri sorumlusu (mülk sahibi veya yönetici) olarak aşağıdaki yasal gereklilikleri yerine getirmeniz önerilir:

### 1. Aydınlatma Yükümlülüğü ve Uyarı Levhaları
- [ ] **Kamera Simgeli Uyarı Levhası:** Kameraların kayıt yaptığı alanların giriş noktalarına (apartman kapısı, mağaza girişi vb.) herkesin görebileceği şekilde *"Bu alan güvenlik amacıyla 7/24 kamera ile izlenmektedir"* levhası asılmalıdır.
- [ ] **Aydınlatma Metni:** Talep edilmesi durumunda incelenebilmesi için veri sorumlusunun adını, amacını ve saklama süresini belirten bir bilgilendirme metni bulundurulmalıdır.

### 2. Amaçla Sınırlılık ve Kamera Açıları
- [ ] **Özel Hayatın Korunması:** Kameralar yalnızca mülk güvenliği amacıyla yönlendirilmelidir.
- [ ] **Komşu Mülk Sınırları:** Kameralar komşu evin balkonunu, penceresini veya iç mekanını görmemelidir; yalnızca kendi bahçeniz veya kapı girişiniz açıda olmalıdır.
- [ ] **Özel Alan Yasağı:** Soyunma odası, tuvalet, dinlenme alanı gibi mahrem alanlara kesinlikle kamera konulamaz.

### 3. Veri Minimizasyonu ve Saklama Süresi
- [ ] **Süre Sınırı:** Kayıtlar ihtiyaçtan uzun süre saklanmamalıdır (LocalVision NVR varsayılan olarak **14 gün** saklama süresi uygular).
- [ ] **Otomatik Budama:** Saklama süresi dolmuş veya kotası aşılmış kayıtlar sistem tarafından otomatik ve geri alınamaz şekilde imha edilir.

### 4. Erişim Yetkilendirmesi (RBAC)
- [ ] Sistem Yöneticisi (Admin) parolasını güçlü tutun.
- [ ] İzleme yapacak personele yalnızca ihtiyaç duyduğu kameralar için `Operatör` veya `İzleyici` yetkisi tanımlayın.
- [ ] Personel işten ayrıldığında kullanıcı hesabını derhal devre dışı bırakın.

### 5. Video Delillerinin Dışa Aktarımı
- [ ] Bir olay veya adli vaka durumunda video dışa aktarılırken sistemin sağladığı **SHA-256 bütünlük doğrulaması** ve **zaman damgalı filigran** özelliğini kullanın. Bu sayede videonun tahrif edilmediği adli makamlara kanıtlanabilir.
