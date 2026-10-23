from PySide6.QtCore import QTimer, Signal
from network.base_communicator import BaseCommunicator
from core import BaseLogger
from .base_connection_manager import BaseConnectionManager
from models.command_data import CommandData
from models.joystick_data import JoystickData

class ConnectionManager(BaseConnectionManager):
    
    # YENİ: Acil durum kablo kopmasını bildiren özel kırmızı fişek!
    connection_lost_signal = Signal()
    # YENİ: İlk bağlantı denemesinde karşıya hiç ulaşılamadığını bildiren sarı fişek!
    connection_failed_signal = Signal()

    # MİMARİ KİLİT: Ağdan gelen her türlü ham paketi TelemetryManager'a paslamak için kullanılan kanal.
    raw_data_received = Signal(dict)

    def __init__(self, communicator: BaseCommunicator, logger: BaseLogger):
        # KRİTİK DÜZELTME: QObject (Sinyal altyapısı) başlatması için zorunludur.
        super().__init__() 
        
        self.communicator = communicator
        self.logger = logger

        # --- HEARTBEAT (Kalp Atışı) ZAMANLAYICISI ---
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self._check_heartbeat)
        self.is_fully_connected = False  
        
        # --- WATCHDOG (Fail-Safe Bekçisi) ---
        self.missed_heartbeats = 0

        # DONANIM ZIRHI: İki farklı fiziksel duruma özel dinamik toleranslar!
        self.INITIAL_TIMEOUT_LIMIT = 40  # İlk el sıkışma için 4.0 Saniye tolerans
        self.ACTIVE_TIMEOUT_LIMIT = 15   # Araç seyre kalktıktan sonraki kopmalar için 1.5 Saniye!

        # MİMARİ ZIRH: Arayüzden istenen (Talep Edilen) Arm durumu. Gerçek durumu Telemetry belirler!
        self.requested_arm_state = False
        
        # YENİ MİMARİ ZIRH: Jetson ile GCS inatlaşırsa devreye girecek uyum sayacı!
        self.state_mismatch_counter = 0
        


    def connect_to_vehicle(self, host: str, port: int) -> bool:
        try:
            success = self.communicator.connect(host, port)
            
            if success:
                self.logger.log_info(f"Fiziksel hat açıldı: {host}:{port}. Kalp atışı bekleniyor...")
                # YEŞİL FİŞEĞİ HEMEN ATEŞLEMİYORUZ! (Defensive Programming)
                # Karşıdan ilk telemetrinin gelip gelmediğini saniyede 10 kez (100ms) dinlemeye başla
                self.is_fully_connected = False
                self.missed_heartbeats = 0 # Bekçiyi sıfırla
                self.heartbeat_timer.start(100)
            else:
                self.logger.log_error(f"Fiziksel bağlantı kurulamadı: {host}:{port}")
                
            return success
            
        except Exception as e:
            self.logger.log_error(f"Bağlantı işlemi sırasında hata: {e}")
            return False

    def disconnect_vehicle(self):
        """UI tarafındaki kod ile uyumlu olması için ismi güncellendi."""
        # Telsiz kapandığı için önce dinleyiciyi sustur (Fail-Safe)
        self.heartbeat_timer.stop()
        self.is_fully_connected = False
        try:
            self.communicator.disconnect()
            self.logger.log_info("Araç ile bağlantı kesildi.")
        except Exception as e:
            self.logger.log_error(f"Bağlantı kesilirken donanım/ağ hatası: {e}")
        finally:
            # KIRMIZI FİŞEK ATEŞLENDİ: Ağ hata verse bile tüm sistem güvenli moda (Fail-Safe) geçsin!
            self.disconnected_signal.emit()

    def _check_heartbeat(self):
        """
        QTimer tarafından periyodik olarak tetiklenir. ZMQ'dan gelen veriyi dinler.
        Hattın 'Master Listener'ı olarak veriyi yakalar ve ilgili yöneticilere paslar.
        """
        data = self.communicator.receive_data()
        
        if data: 
            self.missed_heartbeats = 0  
            
            # --- YENİ MİMARİ ZIRH: DURUM SENKRONİZASYONU (Auto-Sync) ---
            # GCS'nin inadı ile Jetson'ın gerçeği uyuşmuyor mu?
            actual_arm = data.get("armed", False)
            if self.requested_arm_state != actual_arm:
                self.state_mismatch_counter += 1
                # Ağ gecikmesine (Race Condition) şans vermek için 1 sn (10 döngü) bekle
                if self.state_mismatch_counter > 10:
                    self.requested_arm_state = actual_arm  # GCS gerçeğe boyun eğsin!
            else:
                self.state_mismatch_counter = 0 # Her şey uyumlu, sayacı sıfırla.
            
            # (MİMARİ ZIRH: "system_armed_state" burada EZİLMEYECEK. 
            #  Telemetri sadece UI ışıklarını yakmak için "raw_data_received" üzerinden UI'a gidecek!)
            
            if not self.is_fully_connected:
                self.is_fully_connected = True
                self.logger.log_info("Jetson'dan haber alındı! Sistem aktif.")
                self.connected_signal.emit()
            
            # MİMARİ LEHİMLEME: Ham veriyi TelemetryManager'ın işlemesi için havaya fırlat!
            self.raw_data_received.emit(data)
            
        else:
            # DONANIM ZIRHI: Veri gelmediği her an sayacı artır
            self.missed_heartbeats += 1
            
            # Dinamik Limit: Bağlıysak 1.5 saniye, bağlanmaya çalışıyorsak 4.0 saniye bekle
            current_limit = self.ACTIVE_TIMEOUT_LIMIT if self.is_fully_connected else self.INITIAL_TIMEOUT_LIMIT
            
            if self.missed_heartbeats >= current_limit:
                if not self.is_fully_connected:
                    self.logger.log_error("BAĞLANTI BAŞARISIZ: Jetson'a ulaşılamadı. Tekrar deneyiniz.")
                    self._handle_connection_failed()
                else:
                    self.logger.log_error("KRİTİK HATA: Bağlantı koptu! Sistem acil duruma alınıyor.")
                    self._handle_connection_lost()

    def _handle_connection_failed(self):
        """Sadece ilk el sıkışma (Handshake) başarısız olduğunda çalışır."""
        self.heartbeat_timer.stop()
        self.is_fully_connected = False
        try:
            self.communicator.disconnect()
        except Exception as e:
            pass
        finally:
            # SARI FİŞEK ATEŞLENDİ: UI'a "Hiç bağlanamadı" demesi için
            self.connection_failed_signal.emit()

    def _handle_connection_lost(self):
        """Sadece sistem aktifken kopma olduğunda (Fail-Safe) çalışır."""
        self.heartbeat_timer.stop()
        self.is_fully_connected = False
        try:
            self.communicator.disconnect()
        except Exception as e:
            self.logger.log_error(f"Acil durum kapatmasında hata: {e}")
        finally:
            # KIRMIZI FİŞEK ATEŞLENDİ: UI'a 'Bağlantı Koptu' demesi için
            self.connection_lost_signal.emit()

    def on_joystick_data_received(self, joy_data: JoystickData):
        """
        ADAPTER (Çevirmen) Metodu: Sadece bu sınıf JoystickData'yı tanır.
        Veriyi alır, evrensel kargo kutusuna (CommandData) koyar ve postacıya verir.
        """
        # Eğer gerçek bağlantı yoksa, komut yollayarak ağı şişirme (Fail-Safe)
        if not self.is_fully_connected:
            return

        # --- KUMANDANIN YETKİSİ ALINDI! ---
        # Kumandadan gelen joy_data.is_armed verisi ARTIK YOK SAYILIYOR.
        # Böylece o sinir bozucu 'Race Condition' ve disko topu hatası KÖKÜNDEN ÇÖZÜLDÜ.

        # 1. Ham Gamepad verisini, İDA'nın anladığı evrensel kutuya paketle
        command = CommandData(
            forward_back = joy_data.forward_back,
            left_right = joy_data.left_right,
            up_down = joy_data.up_down,
            yaw = joy_data.yaw,
            armed = self.requested_arm_state # SADECE Arayüzün TALEP ETTİĞİ durum kargoya konur!
        )

        # 2. Kutuyu sözlüğe (dict) çevir ve ZMQ Network katmanına fırlat
        self.communicator.send_data(command.to_dict())

    def send_motor_command(self, motor_index: int, value: float):
        """
        MOTOR TEST KÖPRÜSÜ: Motor test sayfasından gelen veriyi paketler ve Jetson'a yollar.
        """
        if not self.is_fully_connected:
            return

        # Jetson'ın 'Scenario A' olarak beklediği paket formatı
        motor_packet = {
            "motor_index": motor_index,
            "value": round(value, 2)
        }
        
        self.communicator.send_data(motor_packet)
    
    def send_arm_command(self, arm_request: bool):
        """
        ARAYÜZ (FARE) ARM KÖPRÜSÜ: UI üzerinden gelen 3 saniyelik basılı tutma 
        sonucu oluşan Arm/Disarm emrini donanıma iletir.
        """
        if not self.is_fully_connected:
            return

        # MİMARİ VE GÜVENLİK ZIRHI (Safe-Start): 
        # Arayüzden sadece "Arm" emri gelse bile, aracı tehlikeye atmamak için 
        # tüm motor eksenlerini zorunlu olarak 0.0 (durma noktası) gönderiyoruz. 
        # Böylece araç Arm edildiği salise kontrolsüzce fırlamaz.
        
        # UI'dan gelen yetkiyi SADECE TALEP OLARAK kaydet (Gerçek onayı Jetson verecek!)
        self.requested_arm_state = arm_request
        
        arm_packet = {
            "forward_back": 0.0,
            "left_right": 0.0,
            "up_down": 0.0,
            "yaw": 0.0,
            "armed": self.requested_arm_state
        }
        
        self.communicator.send_data(arm_packet)
        self.logger.log_info(f"Jetson'a motor yetki TALEBİ iletildi: {'ARM İSTEĞİ' if arm_request else 'DISARM İSTEĞİ'}")