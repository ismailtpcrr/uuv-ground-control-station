import pygame
from PySide6.QtCore import QObject, Signal, QTimer
from .base_gamepad_reader import BaseGamepadReader

class GamepadReader(QObject, BaseGamepadReader):
    data_ready = Signal(list, list)
    connection_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.joystick = None
        
        pygame.init()
        pygame.joystick.init()

        self._is_connected = False 
        self._disconnect_grace_period = 0 
        self._rescan_timer = 0            
        
        self._needs_reinit = False
        # --- UYANMA KALKANI: Yarım saniye (10 döngü) boyunca 0.0 sıfırlanmasını engeller ---
        self._ignore_reads = 0 
        
        self._last_axes = [0.0] * 6
        self._last_buttons = [0] * 14
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.read_data)

    def start(self):
        self.timer.start(50) 

    def stop(self):
        self.timer.stop()
        if self.joystick:
            self.joystick.quit()
        pygame.quit()

    def is_running(self) -> bool:
        return self.timer.isActive()

    def read_data(self):
        try:
            for event in pygame.event.get():
                if event.type == pygame.JOYDEVICEADDED:
                    self._needs_reinit = True
        except Exception:
            pass

        try:
            current_device_count = pygame.joystick.get_count()
        except Exception:
            current_device_count = 0

        is_physically_present = (current_device_count > 0)

        # DURUM A: DONANIM FİZİKSEL OLARAK BAĞLI
        if is_physically_present:
            self._disconnect_grace_period = 0 

            # --- ZOMBİ TEMİZLİĞİ VE KALKAN ---
            if self._needs_reinit and self._is_connected:
                self._needs_reinit = False
                try:
                    if self.joystick:
                        self.joystick.quit()
                    self.joystick = pygame.joystick.Joystick(0)
                    self.joystick.init()
                    # Pygame uyandı! İlk 10 döngü (yarım saniye) boyunca ona GÜVENME!
                    self._ignore_reads = 10 
                except Exception:
                    pass

            if not self._is_connected:
                try:
                    self.joystick = pygame.joystick.Joystick(0)
                    self.joystick.init()
                    self._is_connected = True
                    self.connection_changed.emit(True) 
                except Exception:
                    pass
            else:
                # --- KALKAN DEVREDE Mİ? ---
                if self._ignore_reads > 0:
                    self._ignore_reads -= 1
                    # Pygame kendine gelene kadar HAFIZADAKİ sağlam veriyi yolla (Sıfırlanmayı %100 çözer)
                    self.data_ready.emit(self._last_axes, self._last_buttons)
                else:
                    try:
                        axes = [round(self.joystick.get_axis(i), 2) for i in range(self.joystick.get_numaxes())]
                        buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]
                        
                        self._last_axes = axes
                        self._last_buttons = buttons
                        self.data_ready.emit(axes, buttons)
                    except Exception:
                        self.data_ready.emit(self._last_axes, self._last_buttons)

        # DURUM B: DONANIM YOK (Veya USB Temassızlığı Var)
        else:
            if self._is_connected:
                # DÜZELTME: Tanımlı olan değişken ismini kullanıyoruz.
                self._disconnect_grace_period += 1
                
                # MİMARİ NOT: 1 saniye (20 döngü) boyunca 'son sağlam veriyi' koru.
                # Bu süre, USB kablosundaki anlık oynamaları (flicker) hissettirmez.
                if self._disconnect_grace_period >= 20: 
                    # MİMARİ DÜZELTME (SRP): Core katmanı log basmaz, sadece donanımı kapatıp sinyal fırlatır!
                    # "Bağlantı Koptu" logunu atmak, sinyali yakalayan JoystickManager'ın işidir.
                    if self.joystick:
                        self.joystick.quit()
                        self.joystick = None
                        
                    self._is_connected = False
                    self.connection_changed.emit(False) 
                    self._disconnect_grace_period = 0
                    self._emit_empty_data() # ACİL DURUM: Motorları sustur!
                else:
                    # 1 saniyelik tolerans süresi içinde son veriyi göndermeye devam et
                    # Bu sayede 'anlık 0 olma' sorunu yaşamazsın.
                    self.data_ready.emit(self._last_axes, self._last_buttons)
            else:
                self._emit_empty_data()
                
                self._rescan_timer += 1
                if self._rescan_timer >= 20: 
                    pygame.joystick.quit()
                    pygame.joystick.init()
                    self._rescan_timer = 0

    def _emit_empty_data(self):
        self.data_ready.emit([0.0] * 6, [0] * 14)