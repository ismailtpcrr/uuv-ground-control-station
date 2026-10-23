from PySide6.QtCore import QObject, Signal
from models import JoystickData
from core import BaseLogger, BaseGamepadReader
from .base_joystick_manager import BaseJoystickManager

class JoystickManager(QObject, BaseJoystickManager):
    """
    Joystick yönetim merkezi. 
    Donanım (GamepadReader) katmanından gelen ham fiziksel veriyi alıp sisteme (Sinyal olarak) dağıtır.
    """

    # UI (Arayüz) katmanının dinleyeceği sinyaller
    _connection_signal_out = Signal(bool)
    _live_data_signal_out = Signal(list, list, bool) # UI'a canlı veri (axes, buttons, is_armed) fırlatır
    
    # ADAPTER SİNYALİ: Veriyi ağa değil, orkestra şefi üzerinden ConnectionManager'a fırlatır.
    joystick_data_signal = Signal(JoystickData)

    # MİMARİ DÜZELTME: Communicator bağımlılığı silindi. JoystickManager artık ağdan habersiz (SRP)!
    def __init__(self, reader: BaseGamepadReader, logger: BaseLogger):
        super().__init__() 
        
        self.reader = reader
        self.logger = logger

        # --- KABLOLAMA (Sinyal Bağlantıları) ---
        if hasattr(self.reader, 'data_ready'):
            self.reader.data_ready.connect(self.update_from_gamepad)
            
        if hasattr(self.reader, 'connection_changed'):
            self.reader.connection_changed.connect(self.handle_gamepad_connection)

    # --- SİNYAL YAKALAYICI (Gamepad'in fiziksel durumu) ---
    def handle_gamepad_connection(self, is_connected: bool):
        """Gamepad takıldığında veya çıktığında tetiklenir."""
        if is_connected:
            self.logger.log_info("Gamepad sisteme bağlandı.")
        else:
            self.logger.log_warning("Gamepad bağlantısı koptu! Lütfen kontrol edin.")
        
        self._connection_signal_out.emit(is_connected)

    # --- KÖPRÜ METODU (Veriyi paketleme ve UI Güncelleme) ---
    def update_from_gamepad(self, axes: list, buttons: list):
        """Reader'dan veriyi alır, UI'a fırlatır ve yön komutlarını araca yollar."""
        
        # 1. Canlı veriyi UI (Arayüz) katmanına fırlat
        # Gerçek Arm durumu artık MainWindow -> Header üzerinden yönetildiği için dummy (False) yollanır.
        self._live_data_signal_out.emit(axes, buttons, False)

        # 2. Araca gitmesi için modeli oluştur ve Sınır Kapısına fırlat!
        joy_data = JoystickData(axes=axes, buttons=buttons)
        joy_data.is_armed = False # Kumanda artık bu yetkiye sahip değil.
        
        self.joystick_data_signal.emit(joy_data)

    # --- SİNYAL GETTER METOTLARI ---
    def get_connection_signal(self):
        """UI katmanının kumanda durumunu izlemek için alacağı sinyal."""
        return self._connection_signal_out

    def get_live_data_signal(self):
        """UI katmanının canlı verileri (Kokpit) izlemek için alacağı sinyal."""
        return self._live_data_signal_out