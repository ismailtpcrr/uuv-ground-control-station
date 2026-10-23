from PySide6.QtCore import Signal, QObject
from .base_video_manager import BaseVideoManager
from core import BaseLogger, BaseVideoStreamer

class VideoManager(QObject, BaseVideoManager):
    """
    Video akışını yöneten sınıf. 
    Arayüz (UI) ile donanım (Streamer) arasındaki orkestra şefi.
    """
    
    # Kendi iç sinyalimiz. UI sadece buna bağlanır.
    _frame_signal_internal = Signal(object)

    def __init__(self, streamer: BaseVideoStreamer, logger: BaseLogger):
        # QObject'in başlatılması (Sinyaller ve MRO için zorunlu)
        super().__init__() 
        self.streamer = streamer
        self.logger = logger

        # KABLOLAMA: İşçiden gelen her kareyi Manager'ın kendi kanalına aktarıyoruz.
        if hasattr(self.streamer, 'frame_ready'):
            self.streamer.frame_ready.connect(self._frame_signal_internal.emit)

    def start_video(self):
        # DIP UYUMU: is_running() anayasal metodunu kullanıyoruz
        if not self.streamer.is_running():
            self.streamer.start()
            self.logger.log_info("Yer istasyonu video dinleme servisi başlatıldı.")
        else:
            self.logger.log_warning("Video dinleme servisi zaten aktif.")

    def stop_video(self):
        # İşçiyi güvenle durdur
        if self.streamer.is_running():
            self.streamer.stop()
            self.logger.log_info("Yer istasyonu video dinleme servisi kapatıldı.")

    # --- MİMARİ BÜTÜNLÜK: Property silindi, Saf OOP Getter metodu geldi ---
    def get_frame_signal(self):
        """
        BaseVideoManager arayüzünün (Getter) uygulanması.
        UI: manager.get_frame_signal().connect(my_func)
        """
        return self._frame_signal_internal