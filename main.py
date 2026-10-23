import sys
from PySide6.QtWidgets import QApplication

# Katmanlı mimariden gerekli sınıfları içe aktarıyoruz
from core import FileLogger, VideoStreamer, GamepadReader
from network import ZmqCommunicator
from managers import JoystickManager, ConnectionManager, VideoManager, TelemetryManager
from ui import MainWindow

def main():
    """Uygulamanın başlangıç noktası (Composition Root)."""
    
    # 0. ADIM: Qt Uygulamasını Başlat (Sinyallerin çalışması için en başta olmalıdır)
    app = QApplication(sys.argv)
    
    # 1. ADIM: Ortak Hizmetleri Başlat (Loglama)
    logger = FileLogger()
    logger.log_info("--- GCS Sistemi Başlatılıyor ---")

    # 2. ADIM: Altyapı ve İşçileri Kur
    communicator = ZmqCommunicator()
    video_streamer = VideoStreamer(camera_source=0)
    gamepad_reader = GamepadReader()
    
    # 3. ADIM: İş Mantığı Yöneticilerini Oluştur (Managers)
    # DİKKAT: Önce cihazlar (yöneticiler) var edilmeli ki sonra kabloları bağlayabilelim.
    
    # MİMARİ TEMİZLİK: JoystickManager artık ağa dokunmuyor, 'communicator' bağımlılığı silindi!
    joystick_manager = JoystickManager(reader=gamepad_reader, logger=logger)
    
    connection_manager = ConnectionManager(communicator=communicator, logger=logger)
    video_manager = VideoManager(streamer=video_streamer, logger=logger)
    telemetry_manager = TelemetryManager(communicator=communicator, logger=logger)

    # --- SİNYAL BAĞLANTILARI VE İŞÇİLERİ BAŞLATMA ---
    
    # 1. KABLO (KOMUT AKIŞI): Joystick'ten gelen veriyi ConnectionManager'a yolla.
    joystick_manager.joystick_data_signal.connect(connection_manager.on_joystick_data_received)

    # 2. KABLO (TELEMETRİ AKIŞI): ConnectionManager'ın yakaladığı ham veriyi işlenmesi için TelemetryManager'a pasla.
    # MİMARİ NOT: Bu bağlantı, ZMQ hattındaki veri çakışmasını engelleyen ana lehimdir.
    connection_manager.raw_data_received.connect(telemetry_manager.handle_incoming_data)

    # (MİMARİ TEMİZLİK: 3. Kablo olan sahte Fail-Safe zırhı tamamen kaldırıldı. Gerçek zırh Manager'ın içinde.)

    # İşçiyi (Thread) arka planda çalışmaya başlat
    gamepad_reader.start()

    # 4. ADIM: Arayüzü Başlat (UI)
    # Arayüze kullanacağı yöneticileri teslim ediyoruz.
    window = MainWindow(
        joystick_manager = joystick_manager, 
        connection_manager = connection_manager,
        video_manager = video_manager,
        telemetry_manager = telemetry_manager
    )
    window.show()
    
    logger.log_info("Kullanıcı arayüzü başarıyla yüklendi.")
    
    # Uygulama döngüsünü başlat (Pencere kapatılana kadar kod burada bekler).
    exit_code = app.exec()
    
    # --- KAPANIŞ PROSEDÜRÜ ---
    # Uygulama kapanırken arkada çalışan işçileri güvenle durdur
    gamepad_reader.stop() 
    video_manager.stop_video()
    telemetry_manager.stop_telemetry_loop()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()