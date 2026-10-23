import logging
import os
from datetime import datetime
from .base_logger import BaseLogger

class FileLogger(BaseLogger):
    """
    BaseLogger arayüzünden türeyen ve tüm kayıtları 'logs' klasörünün 
    içindeki .txt dosyalarına yazan asıl sınıfımız (Concrete Class).
    """

    def __init__(self):
        # 1. Klasör ve dosya yolu hazırlığı
        if not os.path.exists("logs"):
            os.makedirs("logs")

        today_str = datetime.now().strftime("%d-%m-%Y")
        log_file_path = f"logs/system_logs_{today_str}.txt"

        # 2. Sınıfa özel Logger oluşturma (Global basicConfig yerine)
        self.logger = logging.getLogger("UUV_GCS_Logger")
        self.logger.setLevel(logging.INFO)

        # 3. Dosya yazıcı (FileHandler) ve formatlayıcı (Formatter) ayarı
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        formatter = logging.Formatter(
            fmt="[%(asctime)s] - [%(levelname)s] - %(message)s",
            datefmt="%H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        
        # Handler'ı ekle (Eğer daha önce eklenmemişse - Singleton benzeri koruma)
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)

    def _force_flush(self):
        """Hafızadaki veriyi diske gönderir ama thread'i kilitlemez."""
        for handler in self.logger.handlers:
            # Sadece flush() yeterlidir. fsync() yüksek FPS'li GCS'lerde UI'ı dondurabilir.
            handler.flush()

    def log_info(self, message: str):
        self.logger.info(message)
        self._force_flush()

    def log_warning(self, message: str):
        self.logger.warning(message)
        self._force_flush()

    def log_error(self, message: str):
        self.logger.error(message)
        self._force_flush()