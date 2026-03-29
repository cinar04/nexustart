# NEXUS Start Menu v3.0

## Dosya Yapısı (Modüler)

```
nexus_v3/
├── main.py           ← Çalıştırılacak ana dosya
├── config.py         ← Ayarlar, DataManager, i18n, stil yardımcıları
├── animations.py     ← Tüm animasyon sınıfları
├── threads.py        ← Arka plan thread'leri
├── widgets.py        ← Özellik widget'leri
├── settings_panel.py ← Hızlı Ayarlar paneli
├── requirements.txt  ← Python bağımlılıkları
└── BUILD.bat         ← Kurulum & çalıştırma betiği
```

## Kurulum

```bat
pip install -r requirements.txt
python main.py
```

## v3.0 Yeni Özellikler

### 🎨 Animasyon & Tasarım (20 adet)
- Açılış/kapanış fade+scale animasyonu
- Ripple tıklama efekti
- LED kenar nabız animasyonu
- Tile bounce (sekme) animasyonu
- Pin yıldız patlaması (StarBurst)
- Toast bildirim animasyonu (köşeden kayar)
- Müzik çubuğu animasyonu (5 bar dalgası)
- Analog saat widget'i
- Skeleton loading ekranı
- Gece gökyüzü yıldız arka planı
- Neon glow hover efekti
- Karanlık mod geçişi (smooth fade)
- Selamlama metni (Günaydın / İyi akşamlar)
- Odak & DnD modu göstergesi
- LED nabız üst çizgi
- Favoriler bölümü (animasyonlu tile)
- Analog saat (analog + dijital saat dilimi)
- Tag badge animasyonu tile üzerinde
- Staggered tile yükleme (skeleton → tiles)
- Ripple overlay (tüm ana pencere)

### ⚙️ Özellikler (61 adet)
- Klasör grupları (drag & drop uygulamalar)
- Hızlı notlar (kalıcı metin editörü)
- Yapılacaklar listesi (checkbox + sil)
- Geri sayım sayacı (tarihe kadar)
- Pomodoro zamanlayıcı (25/5 dk)
- Pano geçmişi (izle + kopyala)
- Emoji arama & kopyala
- Renk toplayıcı (HEX/RGB/HSL + palette kaydet)
- Birim dönüştürücü (6 kategori)
- Para birimi dönüştürücü (anlık kur)
- Hesap makinesi (tam operatörlü)
- Disk kullanım göstergesi
- Ağ hızı monitörü (↓↑)
- Pil durumu widget'i
- Favoriler bölümü
- Uygulama kullanım istatistiği (bugün N kez)
- Takvim widget'i (önceki/sonraki ay)
- Komut istemi başlatıcı (CMD/PS/WT/Git Bash)
- Web arama kısayolları (6 arama motoru)
- Hızlı URL aç
- Yedekleme & geri yükleme (JSON)
- İkon boyutu değiştirme (küçük/orta/büyük)
- Dil desteği (Türkçe / English)
- Güncelleme kontrolü (arka planda)
- Hızlı restart/shutdown/uyku butonları
- Selamlama mesajı (saate göre)
- QR kod üreteci
- Şifre üreteci (özelleştirilebilir)
- Çoklu saat dilimi (9 şehir)
- Arama geçmişi (otomatik kayıt)
- Klavye navigasyonu (ESC, ok tuşları)
- Odak modu (menüyü açık tutar)
- Rahatsız etme modu (toast gizler)
- Uygulamalara alias & tag
- Uygulama istatistikleri
- 5 günlük hava tahmini
- Güneş doğuş/batış saati
- Toast bildirimi sistemi
- Pano izleyici (otomatik yakalar)
- Neon glow mod (ayarlardan)
- Gece gökyüzü tema (ayarlardan)
- Açılış animasyonu açma/kapama
- Renk paleti kaydet
- Ekran saydamlık kaydırıcısı
- Hava durumu şehir & birim ayarı
- LED renk presets (6 hazır)
- Özel ana & ikincil renk seçici
- Uygulama tag'leri (#iş #oyun)
- Son kullanılan uygulama + bugün kaç kez
- Tüm uygulamalar listesi (etiketle)
- Dosya arama (Desktop/Docs/Downloads)
- Sistem bilgisi (CPU/RAM/Disk/Net/Pil)
- Windows başlangıcına ekle
- Duvar kağıdı seçici
- Görevi sonlandır (sağ tık)
- Favorilere ekle (sağ tık)
- Klasör konumunu aç (sağ tık)
- Kilitle / Yeniden Başlat / Kapat
- System tray (çift tık aç/kapat)
- Global Ctrl+Space kısayolu

## Kısayollar
- `Ctrl+Space` — Menüyü aç/kapat
- `ESC` — Menüyü kapat
- `↑↓←→` — Arama kutusuna odaklan
