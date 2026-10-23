import cv2
from PySide6.QtCore import Qt, Signal, QPropertyAnimation
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QWidget, QLabel, QGridLayout, QPushButton, QSizePolicy, QGraphicsOpacityEffect

class ClickableLabel(QLabel):
    """Tıklanabilir etiket (PiP Takası İçin)."""
    clicked = Signal()
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class CameraView(QWidget):
    """
    Ana video akışının, PIP kameranın ve OpenCV-Qt çevirilerinin yapıldığı bağımsız sayfa.
    """
    camera_toggled = Signal() # Butona basıldığında ana pencereye haber verir

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.is_main_camera_active = True 
        
        # --- ARAYÜZ İNŞASI ---
        self.video_grid = QGridLayout(self)
        self.video_grid.setContentsMargins(10, 10, 10, 10)

        # 1. Ana Kamera (Büyük Ekran)
        self.main_camera_label = QLabel("Ana Kamera\n(Sinyal Bekleniyor)")
        self.main_camera_label.setAlignment(Qt.AlignCenter)
        self.main_camera_label.setStyleSheet("background-color: #0A0A0A; color: #555555; font-size: 20px; border: 1px solid #2A2A2A; border-radius: 8px;")
        self.main_camera_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.main_camera_label.setMinimumSize(400, 300)
        
        # 2. PiP Kamera (Küçük Ekran)
        self.pip_camera_label = ClickableLabel("Kamera 2")
        self.pip_camera_label.setFixedSize(280, 210) 
        self.pip_camera_label.setAlignment(Qt.AlignCenter)
        self.pip_camera_label.setStyleSheet("background-color: #1A1A1A; border: 2px solid #555555; color: #888888; border-radius: 8px;")
        self.pip_camera_label.clicked.connect(self._on_pip_camera_clicked) 

        self.video_grid.addWidget(self.main_camera_label, 0, 0)
        self.video_grid.addWidget(self.pip_camera_label, 0, 0, Qt.AlignBottom | Qt.AlignRight)

        # 3. Kamerayı Başlat Butonu
        self.btn_camera = QPushButton("Kamerayı Başlat")
        self.btn_camera.setFixedSize(150, 40)
        self.btn_camera.setStyleSheet("background-color: #2A2A2A; color: #DDDDDD; border-radius: 4px; font-weight: bold; border: 1px solid #444444;")
        self.btn_camera.setEnabled(False) 
        self.btn_camera.clicked.connect(self.camera_toggled.emit) # Direkt dışarıya sinyal at
        self.video_grid.addWidget(self.btn_camera, 0, 0, Qt.AlignBottom | Qt.AlignCenter)

    # --- YEREL OLAYLAR (PiP Animasyonu) ---
    def _on_pip_camera_clicked(self):
        """Kullanıcı küçük ekrana tıkladığında büyük ekranla yer değiştirir."""
        opacity = QGraphicsOpacityEffect(self.pip_camera_label)
        self.pip_camera_label.setGraphicsEffect(opacity)
        anim = QPropertyAnimation(opacity, b"opacity")
        anim.setDuration(150)
        anim.setStartValue(0.5)
        anim.setEndValue(1.0)
        anim.start()

        self.is_main_camera_active = not self.is_main_camera_active
        if self.is_main_camera_active:
            self.main_camera_label.setText("Ana Kamera\n(Sinyal Bekleniyor)")
            self.pip_camera_label.setText("Kamera 2")
        else:
            self.main_camera_label.setText("Kamera 2\n(Sinyal Bekleniyor)")
            self.pip_camera_label.setText("Ana Kamera")

    # --- DIŞARIDAN YÖNETİM METODLARI ---
    
    def set_camera_button_state(self, is_enabled: bool):
        self.btn_camera.setEnabled(is_enabled)
        
    def set_camera_button_ui(self, text: str, bg_color: str):
        self.btn_camera.setText(text)
        self.btn_camera.setStyleSheet(f"background-color: {bg_color}; color: #DDDDDD; border-radius: 4px; font-weight: bold; border: 1px solid #444444;")

    def reset_screens(self):
        """Sistem kapandığında ekranları siyaha boyar."""
        self.main_camera_label.setPixmap(QPixmap()) 
        self.pip_camera_label.setPixmap(QPixmap())
        
        if self.is_main_camera_active:
            self.main_camera_label.setText("Ana Kamera\n(Sinyal Bekleniyor)")
            self.pip_camera_label.setText("Kamera 2")
        else:
            self.main_camera_label.setText("Kamera 2\n(Sinyal Bekleniyor)")
            self.pip_camera_label.setText("Ana Kamera")

    def render_frame(self, frame):
        """Manager'dan gelen RAW OpenCV görüntüsünü Qt'ye çevirip ekrana basar."""
        # Bellek Referans Kalkanı: Görüntü işlenene kadar belleğin silinmesini engeller.
        self._current_rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = self._current_rgb_image.shape
        bytes_per_line = ch * w
        
        # MİMARİ NOT: QImage belleği self._current_rgb_image üzerinden okur. 
        # Referans sınıf içinde tutulduğu için "Segmentation Fault" engellenir.
        qt_image = QImage(self._current_rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # GPU Dostu Çizim: SmoothTransformation daha yumuşaktır ancak FastTransformation düşük CPU tüketir.
        # Gömülü sistem GCS'lerinde CPU'yu korumak için FastTransformation kalmalı.
        if self.is_main_camera_active:
            pixmap = QPixmap.fromImage(qt_image).scaled(self.main_camera_label.size(), Qt.KeepAspectRatio, Qt.FastTransformation)
            self.main_camera_label.setPixmap(pixmap)
        else:
            pixmap = QPixmap.fromImage(qt_image).scaled(self.pip_camera_label.size(), Qt.KeepAspectRatio, Qt.FastTransformation)
            self.pip_camera_label.setPixmap(pixmap)