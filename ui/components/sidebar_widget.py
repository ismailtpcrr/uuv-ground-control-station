from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton

class SidebarWidget(QFrame):
    # Ana pencereye "Şu sayfaya geç" komutunu verecek sinyal (0=Video, 1=Joystick, 2=Motor, 3=Ayarlar)
    page_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #161616; border-right: 1px solid #2A2A2A;")
        
        self.drawer_layout = QVBoxLayout(self)
        self.drawer_layout.setAlignment(Qt.AlignTop)
        self.drawer_layout.setContentsMargins(0, 20, 0, 0)

        # Menü Aç/Kapa Durumu ve Animasyonu
        self.is_open = True
        self.drawer_animation = QPropertyAnimation(self, b"maximumWidth")
        self.drawer_animation.setDuration(250) 
        self.drawer_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Butonları Yaratıyoruz
        self.btn_nav_joystick = self._create_nav_btn("🎮 Kumanda")
        self.btn_nav_motor = self._create_nav_btn("⚙️ Motor Testi")
        self.btn_nav_settings = self._create_nav_btn("🛠️ Ayarlar")

        self.menu_buttons = [self.btn_nav_joystick, self.btn_nav_motor, self.btn_nav_settings]

        for btn in self.menu_buttons:
            self.drawer_layout.addWidget(btn)

        # Buton Tıklama Olayları
        self.btn_nav_joystick.clicked.connect(lambda: self._on_btn_clicked(1, self.btn_nav_joystick))
        self.btn_nav_motor.clicked.connect(lambda: self._on_btn_clicked(2, self.btn_nav_motor))
        self.btn_nav_settings.clicked.connect(lambda: self._on_btn_clicked(3, self.btn_nav_settings))

    def _create_nav_btn(self, text):
        btn = QPushButton(text)
        btn.setFixedHeight(55) 
        btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #888888; text-align: left; padding-left: 20px; font-size: 16px; font-weight: bold; border: none; }
            QPushButton:hover { background-color: #222222; color: #DDDDDD; }
            QPushButton:checked { background-color: #2A3A4A; color: white; border-right: 4px solid #888888; }
        """)
        btn.setCheckable(True)
        return btn

    def _on_btn_clicked(self, page_index, clicked_btn):
        """Sadece tıklanan butonu aktif yapar, diğerlerini söndürür."""
        for btn in self.menu_buttons:
            if btn != clicked_btn:
                btn.setChecked(False)
        
        # Eğer açık olan sekmeye tekrar tıklarsa, 0. sayfaya (Ana Kamera) geri döner
        if not clicked_btn.isChecked():
            self.page_changed.emit(0) 
        else:
            self.page_changed.emit(page_index)

    # --- ANA PENCERENİN MENÜYÜ YÖNETMESİ İÇİN KOMUTLAR ---

    def toggle_menu(self, target_width):
        """Menüyü animasyonlu şekilde açıp kapatır."""
        if self.is_open:
            self.drawer_animation.setStartValue(self.width())
            self.drawer_animation.setEndValue(0)
            self.is_open = False
        else:
            self.drawer_animation.setStartValue(self.width())
            self.drawer_animation.setEndValue(target_width)
            self.is_open = True
            
        self.drawer_animation.start()

    def update_dynamic_width(self, target_width):
        """Pencere boyutu değiştiğinde menü genişliğini orantılı olarak ayarlar."""
        for btn in self.menu_buttons:
            btn.setMinimumWidth(target_width)
            
        if self.is_open and self.drawer_animation.state() != QPropertyAnimation.Running:
            self.setMaximumWidth(target_width)