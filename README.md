# UUV Yer Kontrol İstasyonu (Ground Control Station)

İnsansız sualtı aracı (UUV) için geliştirilmiş, PySide6 tabanlı masaüstü yer kontrol istasyonu. Araçtaki Jetson ile ZeroMQ üzerinden haberleşir; gamepad ile aracı yönetir, kamera görüntüsünü ve telemetri verilerini gösterir.

## Özellikler

- **Gamepad ile kontrol:** İleri/geri, sağ/sol, derinlik ve yaw komutları araca gönderilir. Gamepad takılıp çıkarıldığında otomatik algılanır.
- **ARM / DISARM:** Arayüzdeki butona 3 saniye basılı tutarak motor yetkisi istenir. Gerçek durumu araç belirler; arayüz sadece Jetson'dan gelen telemetriye göre güncellenir.
- **Bağlantı takibi (heartbeat):** İlk bağlantıda 4 saniye, bağlantı kurulduktan sonra 1,5 saniye veri gelmezse bağlantı koptu sayılır ve sistem güvenli moda geçer.
- **Telemetri:** Pil, voltaj, motor hızları ve araçtan gelen uyarı mesajları (INFO / WARNING / CRITICAL) gösterilir.
- **Kamera görüntüsü:** OpenCV ile ayrı bir thread'de okunur, arayüzü dondurmaz.
- **Motor testi:** 6 motor ayrı ayrı test edilebilir.
- **Loglama:** Sistem olayları `logs/` klasörüne günlük dosyalar halinde yazılır.

## Proje Yapısı

```
├── main.py            # Uygulamanın başlangıç noktası, tüm bileşenleri birbirine bağlar
├── fake_jetson.py     # Test için aracı taklit eden simülatör
├── core/              # Donanım katmanı: gamepad okuma, kamera, loglama
├── network/           # Haberleşme katmanı (ZeroMQ)
├── models/            # Veri modelleri: joystick, telemetri, komut
├── managers/          # İş mantığı: bağlantı, joystick, video, telemetri yöneticileri
└── ui/                # Arayüz: ana pencere, üst bar, yan menü ve sayfalar
```

Her katman bir temel sınıf (`Base...`) üzerinden tanımlanır. Böylece örneğin ZeroMQ yerine başka bir haberleşme yöntemi eklemek için sadece yeni bir `BaseCommunicator` sınıfı yazmak yeterlidir.

## Kurulum

Python 3.9 veya üzeri gerekir.

```bash
git clone https://github.com/ismailtpcrr/uuv-ground-control-station.git
cd uuv-ground-control-station

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Çalıştırma

### Simülatör ile test

Gerçek araç olmadan denemek için iki ayrı terminal açın:

```bash
# 1. terminal: araç simülatörü (5555 portunu dinler)
python fake_jetson.py

# 2. terminal: yer kontrol istasyonu
python main.py
```

Arayüzde **Sisteme Bağlan** butonuna basın. Simülatördeki pil seviyesini `fake_jetson.py` içindeki `FAKE_BATTERY_LEVEL` değişkeninden değiştirebilirsiniz:

- `20`'nin üstü: ARM talebi kabul edilir.
- `20` ve altı: ARM talebi reddedilir ve arayüzde "Low Battery" uyarısı çıkar.

### Gerçek araç ile

Varsayılan hedef adres `127.0.0.1:5555`'tir. Araca bağlanmak için [ui/main_window.py](ui/main_window.py) içindeki `target_host` ve `target_port` değerlerini aracın adresine göre değiştirin.

## Kullanılan Teknolojiler

- [PySide6](https://doc.qt.io/qtforpython-6/): arayüz
- [pyzmq](https://pyzmq.readthedocs.io/): araçla haberleşme
- [OpenCV](https://opencv.org/): kamera görüntüsü
- [pygame](https://www.pygame.org/): gamepad okuma
