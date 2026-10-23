from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QSlider

class MotorBarWidget(QWidget):
    """Tekli Motor Test Çubuğu."""
    value_changed = Signal(float)
    
    def __init__(self, motor_index=0, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_motor = QLabel(f"Motor {motor_index+1}")
        self.lbl_motor.setStyleSheet("font-size: 14px; color: #888888;")
        self.layout.addWidget(self.lbl_motor)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(-100, 100) 
        self.slider.setValue(0)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal { background: #333333; height: 8px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #888888; width: 16px; height: 16px; margin: -4px 0; border-radius: 8px; }
            QSlider::sub-page:horizontal { background: #4A6572; border-radius: 4px; }
        """)
        self.slider.valueChanged.connect(self._on_slider_changed)
        
        # DONANIM ZIRHI: "Dead-Man's Switch". Kullanıcı fareyi bıraktığında motor anında dursun!
        self.slider.sliderReleased.connect(self._on_slider_released)
        
        self.layout.addWidget(self.slider)
        
        # --- YENİ: İstenen ve Gerçek değerleri yan yana şık göstermek için ---
        from PySide6.QtWidgets import QHBoxLayout # Eğer yukarıda import edilmediyse
        
        self.values_layout = QHBoxLayout()
        
        self.lbl_target = QLabel("Hedef: 0%")
        self.lbl_target.setStyleSheet("font-size: 14px; font-weight: bold; color: #DDDDDD;")
        
        self.lbl_real = QLabel("Gerçek: 0%")
        self.lbl_real.setStyleSheet("font-size: 14px; font-weight: bold; color: #00BCD4;") # Canlı veri için Turkuaz
        
        self.values_layout.addWidget(self.lbl_target)
        self.values_layout.addSpacing(15)
        self.values_layout.addWidget(self.lbl_real)
        self.values_layout.addStretch()
        
        self.layout.addLayout(self.values_layout)
        
    def _on_slider_changed(self, value):
        self.lbl_target.setText(f"Hedef: {value}%")
        self.value_changed.emit(value / 100.0)

    def _on_slider_released(self):
        # MİMARİ NOT: Slider 0'a çekilince valueChanged sinyali otomatik tetiklenir ve motorlara 0.0 emri gider.
        self.slider.setValue(0)
        
    def set_real_value(self, real_value_normalized: float):
        """Jetson'dan gelen gerçek telemetri değerini arayüze basar."""
        real_percentage = int(real_value_normalized * 100)
        self.lbl_real.setText(f"Gerçek: {real_percentage}%")

class MotorTestView(QWidget):
    """Tüm motorların test edildiği bağımsız sayfa (View)."""
    
    # YENİ: Dışarıya fırlatılacak ana sinyal (motor_index, güç_değeri)
    motor_test_command = Signal(int, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        motor_layout = QVBoxLayout(self)
        motor_layout.addWidget(QLabel("🔧 Motor Test Paneli", styleSheet="font-size: 20px; font-weight: bold; color: #DDDDDD;"))
        
        self.motor_bars = [] # MİMARİ EKLEME: Çubukları güncelleyebilmek için hafızaya alıyoruz
        
        motor_grid = QGridLayout()
        motor_grid.setSpacing(20)
        for i in range(6):
            motor_bar = MotorBarWidget(motor_index=i)
            # YENİ: Slider değiştiğinde kendi ana sinyalimizi tetikliyoruz
            motor_bar.value_changed.connect(lambda val, idx=i: self.motor_test_command.emit(idx, val)) 
            
            self.motor_bars.append(motor_bar) # Çubuğu listeye ekle
            motor_grid.addWidget(motor_bar, i // 2, i % 2)
            
        motor_layout.addLayout(motor_grid)
        motor_layout.addStretch()

    def update_motor_feedbacks(self, real_motor_speeds: list):
        """Jetson'dan gelen gerçek telemetri listesini çubuklara dağıtır."""
        for i, real_val in enumerate(real_motor_speeds):
            if i < len(self.motor_bars):
                self.motor_bars[i].set_real_value(real_val)