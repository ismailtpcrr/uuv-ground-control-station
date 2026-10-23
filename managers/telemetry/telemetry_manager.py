from PySide6.QtCore import QObject, Signal, QTimer
from .base_telemetry_manager import BaseTelemetryManager
from models import TelemetryData
from network import BaseCommunicator
from core import BaseLogger

class TelemetryManager(QObject, BaseTelemetryManager):
    """
    Araçtan gelen ham telemetri verilerini dinler, 
    TelemetryData modeline çevirir ve arayüze (UI) fırlatır.
    """
    
    # Kendi iç sinyalimiz. UI bu sinyale bağlanıp veriyi havada kapacak.
    _telemetry_signal_internal = Signal(TelemetryData)

    def __init__(self, communicator: BaseCommunicator, logger: BaseLogger):
        super().__init__()
        self.communicator = communicator
        self.logger = logger
        
        # MİMARİ DÜZELTME: Timer kaldırıldı. 
        # TelemetryManager artık "aktif toplayıcı" değil, "pasif işleyici" (Processor).
        self._is_running = False
        
        # YENİ ZIRH: Ağdan gelen aynı uyarıların yankılarını engellemek için hafıza
        self._last_status_msg = ""

    def start_telemetry_loop(self):
        """Arayüz uyumluluğu için tutuldu, sadece bayrağı günceller."""
        self._is_running = True
        self.logger.log_info("Telemetri işleme birimi aktif edildi.")

    def stop_telemetry_loop(self):
        """İşleme birimini durdurur ve arayüz çağrılarına yanıt verir."""
        self._is_running = False
        self.logger.log_info("Telemetri işleme birimi durduruldu.")

    def handle_incoming_data(self, raw_data: dict):
        """
        Dışarıdan (ConnectionManager'dan) gelen ham veriyi işler.
        Ağ katmanına kendisi dokunmaz (SRP & Anti-Race Condition).
        """
        if not self._is_running or not raw_data:
            return

        try:
            # --- ZIRH: JSON'dan gelen sözlük yapısındaki motorları, temiz bir Listeye çevir ---
            raw_motors = raw_data.get("motors", {})
            clean_motor_list = [0.0] * 6
            for key, val in raw_motors.items():
                if str(key).isdigit() and int(key) < 6:
                    clean_motor_list[int(key)] = float(val)

       # --- MİMARİ ZIRH: STATUSTEXT KONTROLÜ VE LOGLAMA (Kara Kutu) ---
            status_msg = raw_data.get("status_msg", "")
            msg_type = raw_data.get("msg_type", "")
            
            # YENİ ZIRH: Yankı Filtresi (Debounce)
            if status_msg:
                if status_msg != self._last_status_msg:
                    # Yeni bir kriz! Hafızaya al, UI'a ve Loglara gönder.
                    self._last_status_msg = status_msg
                    print(f"\n[GÜMRÜK MEMURU] Kargo sınırı başarıyla geçti! Mesaj: {status_msg}")
                    
                    # Gelen mesajın ciddiyetine göre log seviyesini belirle
                    if msg_type == "CRITICAL" or msg_type == "ERROR":
                        self.logger.log_error(f"Jetson Uyarı: {status_msg}")
                    elif msg_type == "WARNING":
                        self.logger.log_warning(f"Jetson Uyarı: {status_msg}")
                    else:
                        self.logger.log_info(f"Jetson Mesajı: {status_msg}")
                else:
                    # Aynı mesajın yankısı (TTL) gelmeye devam ediyor. UI'ı ve logları spamlama!
                    # UI fırlatmasın diye DTO'ya gidecek değişkeni boşaltıyoruz.
                    status_msg = ""
            else:
                # Jetson uyarı yollamayı kesti, her şey normale döndü. Hafızayı sıfırla.
                self._last_status_msg = ""

            # Gelen ham veriyi SAF DTO modelimize (TelemetryData) dönüştür
            telemetry = TelemetryData(
                depth=raw_data.get("depth", 0.0),
                temperature=raw_data.get("temperature", 0.0),
                battery_level=raw_data.get("battery", 100.0), # 'battery_level' yerine Jetson'ın yolladığı 'battery' anahtarı
                voltage=raw_data.get("voltage", 0.0),
                current_a=raw_data.get("current_a", 0.0),     # YENİ EKLENEN
                heading=raw_data.get("heading", 0.0),         # YENİ EKLENEN
                pitch=raw_data.get("pitch", 0.0),             # YENİ EKLENEN
                roll=raw_data.get("roll", 0.0),               # YENİ EKLENEN
                is_connected=raw_data.get("is_connected", True),
                is_armed=raw_data.get("armed", False),        # YENİ EKLENEN
                status_msg=status_msg,                        # YENİ (STATUSTEXT): GCS arayüzüne (UI) uçurulacak hata mesajı
                msg_type=msg_type,                            # YENİ (STATUSTEXT): Uyarı seviyesi
                motor_speeds=clean_motor_list                 # YENİ EKLENEN: Temizlenmiş motor listesi
            )
            
            # Hazırlanan paketi UI'a fırlat
            self._telemetry_signal_internal.emit(telemetry)
                
        except Exception as e:
            self.logger.log_error(f"Telemetri ayrıştırma hatası: {e}")

    def get_telemetry_signal(self):
        """UI katmanının bağlanacağı sinyali dışa açar."""
        return self._telemetry_signal_internal