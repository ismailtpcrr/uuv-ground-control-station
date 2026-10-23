from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout

class JoystickAnalogWidget(QWidget):
    """Analog Çubuk Göstergesi (Gamepad ekranı için)."""
    def __init__(self, parent=None, title="Sola"):
        super().__init__(parent)
        self.setFixedSize(160, 160)
        self.setStyleSheet("border: none; background-color: transparent;")
        self._title = title
        self._x = 0.0 
        self._y = 0.0 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.translate(rect.center())
        
        painter.setPen(QPen(QColor(136, 136, 136), 2))
        painter.drawEllipse(-60, -60, 120, 120)
        
        painter.setPen(QPen(QColor(85, 85, 85), 1))
        painter.drawLine(-60, 0, 60, 0)
        painter.drawLine(0, -60, 0, 60)

        painter.setPen(QPen(Qt.white, 4))
        painter.setBrush(Qt.white)
        qx = int(self._x * 60)
        qy = int(self._y * 60)
        painter.drawEllipse(qx - 5, qy - 5, 10, 10)

    def update_position(self, x_val: float, y_val: float):
        self._x = x_val
        self._y = y_val 
        self.update() 


class GamepadView(QWidget):
    """Kumanda canlı verilerinin gösterildiği bağımsız sayfa (View)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        
        # 1. Başlık
        top_header_layout = QHBoxLayout()
        top_header_layout.addWidget(QLabel("🎮 Kumanda Canlı Verileri", styleSheet="font-size: 20px; font-weight: bold; color: #DDDDDD;"))
        top_header_layout.addStretch() 
        layout.addLayout(top_header_layout)
        
        # 2. Analog Çubuklar
        analog_layout = QHBoxLayout()
        analog_layout.addStretch()
        self.analog_left = JoystickAnalogWidget(title="Sol Analog")
        self.analog_right = JoystickAnalogWidget(title="Sağ Analog")
        analog_layout.addWidget(self.analog_left)
        analog_layout.addWidget(self.analog_right)
        analog_layout.addStretch()
        layout.addLayout(analog_layout)
        
        # 3. Canlı Eksen Metinleri (SF Mono Font Korumalı)
        self.lbl_axis_values = QLabel("İleri-Geri: +0.00 | Sağ-Sol: +0.00 | Derinlik: +0.00 | Dönüş: +0.00 | L2: +0.00 | R2: +0.00")
        self.lbl_axis_values.setAlignment(Qt.AlignCenter)
        self.lbl_axis_values.setStyleSheet("font-size: 12px; font-family: 'Menlo', monospace; color: #CCCCCC; background-color: #1A1A1A; padding: 10px; border-radius: 5px; border: 1px solid #333333;")
        layout.addWidget(self.lbl_axis_values)

        # 4. Butonlar Matrisi
        self.buttons_grid = QGridLayout()
        self.btn_labels = []
        for i in range(16): 
            lbl = QLabel(f"BTN {i}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("background-color: #2A2A2A; color: #555; padding: 5px; border-radius: 4px;")
            self.buttons_grid.addWidget(lbl, i // 7, i % 7) 
            self.btn_labels.append(lbl)
            
        layout.addLayout(self.buttons_grid)
        layout.addStretch()

    # --- DIŞARIDAN VERİ GÜNCELLEME METODU ---
    def update_data(self, axes: list, buttons: list):
        """Manager'dan gelen canlı veriyi arayüze basar."""
        if len(axes) >= 4:
            self.analog_left.update_position(axes[0], axes[1])
            self.analog_right.update_position(axes[2], axes[3])
            
        fw_bk = axes[1] if len(axes) > 1 else 0.0
        lf_rt = axes[0] if len(axes) > 0 else 0.0
        yaw   = axes[2] if len(axes) > 2 else 0.0
        up_dw = axes[3] if len(axes) > 3 else 0.0
        l2_val = axes[4] if len(axes) > 4 else 0.0
        r2_val = axes[5] if len(axes) > 5 else 0.0
        
        text_out = f"İleri-Geri: {fw_bk:+5.2f} | Sağ-Sol: {lf_rt:+5.2f} | Derinlik: {up_dw:+5.2f} | Dönüş: {yaw:+5.2f} | L2: {l2_val:+5.2f} | R2: {r2_val:+5.2f}"
        self.lbl_axis_values.setText(text_out)

        for i, val in enumerate(buttons):
            if i < len(self.btn_labels):
                if val == 1:
                    self.btn_labels[i].setStyleSheet("background-color: #4A90E2; color: white; font-weight: bold; padding: 5px; border-radius: 4px;")
                else:
                    self.btn_labels[i].setStyleSheet("background-color: #2A2A2A; color: #555; padding: 5px; border-radius: 4px;")