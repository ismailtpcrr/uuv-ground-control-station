from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class SettingsView(QWidget):
    """Sistem ayarlarının yapıldığı bağımsız sayfa (View)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        settings_layout = QVBoxLayout(self)
        lbl_settings = QLabel("🛠️ Sistem Ayarları\n(Yakında...)")
        lbl_settings.setAlignment(Qt.AlignCenter)
        lbl_settings.setStyleSheet("font-size: 24px; color: #555555;")
        settings_layout.addWidget(lbl_settings)