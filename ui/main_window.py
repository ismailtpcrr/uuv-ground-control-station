from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QStackedWidget, QApplication

from managers import BaseJoystickManager, BaseConnectionManager, BaseVideoManager, BaseTelemetryManager

# --- BİLEŞENLERİMİZ (COMPONENTS & VIEWS) ---
from .components.header_widget import HeaderWidget
from .components.sidebar_widget import SidebarWidget
from .views.gamepad_view import GamepadView  
from .views.camera_view import CameraView
from .views.motor_test_view import MotorTestView  
from .views.settings_view import SettingsView     

# --- ANA PENCERE (KOKPİT V4 - ANA EKRAN MANTIĞI) ---

class MainWindow(QMainWindow):
    def __init__(self, joystick_manager: BaseJoystickManager, connection_manager: BaseConnectionManager, video_manager: BaseVideoManager, telemetry_manager: BaseTelemetryManager):
        super().__init__()
        self.joystick_manager = joystick_manager
        self.connection_manager = connection_manager
        self.video_manager = video_manager
        self.telemetry_manager = telemetry_manager
        
        self.setWindowTitle("UUV Ground Control Station - Tactical Minimalist")
        self.resize(1400, 800) 
        self.setStyleSheet("background-color: #121212; color: #CCCCCC;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.is_camera_running = False
        self.is_vehicle_connected = False
        self.should_show_video = False 

        self.target_host = "127.0.0.1"
        self.target_port = 5555
        self.drawer_ratio = 0.13

        # MİMARİ ZIRH: Header'a ebeveynini (self) tanıtıyoruz ki, içindeki Toast MainWindow'da süzülebilsin.
        self.header = HeaderWidget(parent=self) 
        self.header.menu_clicked.connect(self.toggle_drawer)
        self.header.connect_clicked.connect(self.on_connect_clicked)
        self.header.arm_ui_command.connect(self.on_ui_arm_requested)
        self.main_layout.addWidget(self.header)

        self.body_layout = QHBoxLayout()
        self.main_layout.addLayout(self.body_layout)

        self.sidebar = SidebarWidget()
        self.sidebar.update_dynamic_width(int(1400 * self.drawer_ratio)) 
        self.body_layout.addWidget(self.sidebar)

        self.setup_central_display()
        
        self.sidebar.page_changed.connect(self.stacked_widget.setCurrentIndex)

        # --- YENİ KABLO: Gamepad'in bağlantı durumunu Header'a (Üst Bar) iletiyoruz ---
        self.joystick_manager.get_connection_signal().connect(self.header.update_gamepad_state)

        self.video_manager.get_frame_signal().connect(self.update_video_frame)
        self.joystick_manager.get_live_data_signal().connect(self.update_live_joystick_ui)
        self.telemetry_manager.get_telemetry_signal().connect(self.update_telemetry_ui)
        
        self.connection_manager.connected_signal.connect(self._on_system_connected)
        self.connection_manager.disconnected_signal.connect(self._on_system_disconnected)
        self.connection_manager.connection_lost_signal.connect(self._on_connection_lost)
        self.connection_manager.connection_failed_signal.connect(self._on_connection_failed)

        QApplication.instance().aboutToQuit.connect(self._execute_shutdown_protocol)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        target_width = int(self.width() * self.drawer_ratio)
        self.sidebar.update_dynamic_width(target_width)

    def toggle_drawer(self):
        target_width = int(self.width() * self.drawer_ratio)
        self.sidebar.toggle_menu(target_width)

    # --- KOKPİT MERKEZ GÖRÜNÜMLERİ (VIEWS) ---

    def setup_central_display(self):
        self.stacked_widget = QStackedWidget()
        self.body_layout.addWidget(self.stacked_widget, stretch=1) 

        self.page_video = CameraView()
        self.page_video.camera_toggled.connect(self.on_camera_clicked)
        self.stacked_widget.addWidget(self.page_video) 

        self.page_joystick = GamepadView()
        self.stacked_widget.addWidget(self.page_joystick)

        self.page_motor = MotorTestView()
        self.page_motor.motor_test_command.connect(self.on_motor_test_command)
        self.stacked_widget.addWidget(self.page_motor) 

        self.page_settings = SettingsView()
        self.stacked_widget.addWidget(self.page_settings) 

    # --- BİLEŞEN TABANLI ŞALTER VE SİNYAL YÖNETİMİ ---

    def on_connect_clicked(self):
        if not self.is_vehicle_connected:
            self.header.set_ui_connecting() 
            success = self.connection_manager.connect_to_vehicle(
                host=self.target_host, 
                port=self.target_port
            )
            if not success:
                self.header.set_ui_error()
        else:
            self.header.set_ui_disconnecting()
            if hasattr(self.connection_manager, 'disconnect_vehicle'):
                self.connection_manager.disconnect_vehicle()

    def _on_system_connected(self):
        self.is_vehicle_connected = True
        self.header.set_ui_connected()
        self.page_video.set_camera_button_state(True) 
        self.telemetry_manager.start_telemetry_loop() 

    def _on_system_disconnected(self):
        self.is_vehicle_connected = False
        self.header.set_ui_disconnected() 
        self._stop_subsystems()

    def _on_connection_lost(self):
        self.is_vehicle_connected = False
        self.header.set_ui_connection_lost() 
        self._stop_subsystems()

    def _on_connection_failed(self):
        self.is_vehicle_connected = False
        self.header.set_ui_connection_failed() 
        self._stop_subsystems()

    def _stop_subsystems(self):
        self.header.update_armed_state(False)
        
        # MİMARİ GÜNCELLEME: Derinlik parametresi uçuruldu. Sadece Pil ve Voltaj sıfırlanıyor.
        self.header.update_telemetry_values(0.0, 0.0) 
        
        if self.is_camera_running:
            self.video_manager.stop_video()
            self.is_camera_running = False
            self.should_show_video = False
            
            self.page_video.reset_screens()
            self._update_camera_btn_state("Kamerayı Başlat", "#2A2A2A")

        self.page_video.set_camera_button_state(False)
        self.telemetry_manager.stop_telemetry_loop()

    def on_camera_clicked(self):
        self.page_video.set_camera_button_state(False)
        self.page_video.btn_camera.setText("İşleniyor...") 
        
        if not self.is_camera_running:
            self.video_manager.start_video()
            self.is_camera_running = True
            self.should_show_video = True 
            
            QTimer.singleShot(1500, lambda: self._update_camera_btn_state("Kamerayı Durdur", "#8B0000"))
        else:
            self.video_manager.stop_video()
            self.is_camera_running = False
            self.should_show_video = False 
            
            self.page_video.reset_screens()
                
            QTimer.singleShot(1500, lambda: self._update_camera_btn_state("Kamerayı Başlat", "#2A2A2A"))

    def _update_camera_btn_state(self, text, bg_color):
        hover_color = "#3A3A3A" if bg_color == "#2A2A2A" else "#A00000" 
        pressed_color = "#151515" if bg_color == "#2A2A2A" else "#600000"
        
        smooth_qss = f"""
            QPushButton {{ 
                background-color: {bg_color}; 
                color: white; 
                border-radius: 4px; 
                font-weight: bold; 
                border: none; 
                font-size: 14px; 
            }}
            QPushButton:hover {{ background-color: {hover_color}; }}
            QPushButton:pressed {{ background-color: {pressed_color}; }}
        """
        
        self.page_video.btn_camera.setText(text)
        self.page_video.btn_camera.setStyleSheet(smooth_qss)
        
        if self.is_vehicle_connected:
            self.page_video.set_camera_button_state(True)

    def update_video_frame(self, frame):
        if not self.should_show_video:
            return 
        self.page_video.render_frame(frame)

    def update_live_joystick_ui(self, axes: list, buttons: list, is_armed: bool):
        # Sadece Joystick sayfasındaki grafikleri günceller. Başka hiçbir şeye karışmaz!
        self.page_joystick.update_data(axes, buttons)
        
    def update_telemetry_ui(self, data):
        # MİMARİ GÜNCELLEME: Derinlik parametresi uçuruldu. Sadece Pil ve Voltaj Header'a gidiyor.
        self.header.update_telemetry_values(data.battery_level, data.voltage)
        
        # --- KAPALI DÖNGÜ (CLOSED LOOP) MİMARİSİ ---
        # Header'daki butonun rengi, sadece Jetson'dan gelen gerçek telemetri verisine göre değişir!
        if self.is_vehicle_connected:
            self.header.update_armed_state(data.is_armed)
        
        if hasattr(self.page_motor, 'update_motor_feedbacks'):
            self.page_motor.update_motor_feedbacks(data.motor_speeds)

        # --- YENİ: TAKTİKSEL BİLDİRİM (STATUSTEXT) YÖNLENDİRMESİ ---
        if hasattr(data, 'status_msg') and data.status_msg:
            
            # --- UUV BİLDİRİM ANAYASASI ---
            # INFO: Hiçbir şey yapma, yut. (İleride Log dosyasına yazılacak)
            if data.msg_type == "INFO":
                pass 
                
            # WARNING: Sadece geçmişe (Menüye) düşsün, ekrana fırlamasın.
            elif data.msg_type == "WARNING":
                self.header.add_notification(data.status_msg, data.msg_type, show_popup=False)
                
            # CRITICAL & FATAL: Hem geçmişe düşsün hem de ekrandan süzülerek (Popup) insin.
            elif data.msg_type in ["CRITICAL", "FATAL", "ERROR"]:
                self.header.add_notification(data.status_msg, data.msg_type, show_popup=True)
            
    def on_motor_test_command(self, motor_index: int, value: float):
        if self.is_vehicle_connected:
            if hasattr(self.connection_manager, 'send_motor_command'):
                self.connection_manager.send_motor_command(motor_index, value)

    def on_ui_arm_requested(self, arm_request: bool):
        if self.is_vehicle_connected:
            if hasattr(self.connection_manager, 'send_arm_command'):
                self.connection_manager.send_arm_command(arm_request)

    def closeEvent(self, event):
        self._execute_shutdown_protocol()
        event.accept()

    def _execute_shutdown_protocol(self):
        if self.is_camera_running:
            self.video_manager.stop_video()
            self.is_camera_running = False 
            
        if self.is_vehicle_connected:
            if hasattr(self.connection_manager, 'disconnect_vehicle'):
                self.connection_manager.disconnect_vehicle()
            self.is_vehicle_connected = False
                
        if hasattr(self.telemetry_manager, 'stop_telemetry_loop'):
            self.telemetry_manager.stop_telemetry_loop()

