from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QLabel, QMenu, QSizePolicy

class HeaderWidget(QFrame):
    menu_clicked = Signal()
    connect_clicked = Signal()
    arm_ui_command = Signal(bool) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setStyleSheet("background-color: #1A1A1A; border-bottom: 1px solid #2A2A2A;")
        
        top_layout = QHBoxLayout(self)
        top_layout.setContentsMargins(10, 0, 10, 0)

        # 1. Menü Butonu 
        self.btn_menu = QPushButton("☰ Menü")
        self.btn_menu.setFixedSize(90, 35) 
        self.btn_menu.setStyleSheet(self._get_btn_style("#2A2A2A", "#3A3A3A", "#151515"))
        self.btn_menu.clicked.connect(self.menu_clicked.emit)
        top_layout.addWidget(self.btn_menu)

        self.status_led = QLabel("⚪") 
        self.status_led.setStyleSheet("font-size: 16px; border: none; background-color: transparent;")
        
        # 3. Bağlantı Kilidi
        self.btn_lock = QPushButton("🔒")
        self.btn_lock.setFixedSize(35, 35) 
        self.btn_lock.setStyleSheet(self._get_btn_style("#2A2A2A", "#3A3A3A", "#151515") + " QPushButton { padding: 0px; }")
        self.btn_lock.hide() 
        self.btn_lock.clicked.connect(self._toggle_lock)
        
        # 4. Bağlan Butonu 
        self.btn_connect = QPushButton("Sisteme Bağlan")
        self.btn_connect.setStyleSheet(self._get_btn_style("#8B0000", "#A00000", "#600000")) 
        self.btn_connect.clicked.connect(self._on_connect_clicked)
        
        top_layout.addSpacing(20)
        top_layout.addWidget(self.status_led)
        top_layout.addWidget(self.btn_lock)
        top_layout.addWidget(self.btn_connect)
        
        self.lock_timer = QTimer(self)
        self.lock_timer.setSingleShot(True)
        self.lock_timer.timeout.connect(self._relock)
        
        # 5. Taktiksel Armed/Safe Göstergesi 
        top_layout.addSpacing(20)
        self.lbl_global_armed = QPushButton("Disarmed")
        self.lbl_global_armed.setEnabled(False) 
        self.lbl_global_armed.setStyleSheet(self._get_btn_style("#8B0000", "#A00000", "#600000"))
        
        self.lbl_global_armed.pressed.connect(self._start_arm_hold)
        self.lbl_global_armed.released.connect(self._cancel_arm_hold)
        
        self.is_currently_armed = False
        self.arm_countdown = 3
        self.arm_timer = QTimer(self)
        self.arm_timer.timeout.connect(self._arm_tick)

        top_layout.addWidget(self.lbl_global_armed)
        
        top_layout.addStretch()

        # --- YENİ: TAKTİKSEL BİLDİRİM (TOAST & HISTORY) SİSTEMİ ---
        self.notification_history = []
        
        # MİMARİ ZIRH: Toast'ı hapishaneden (layout) kurtarıp doğrudan Ana Pencereye bağlıyoruz.
        self.lbl_toast = QLabel(parent if parent else self) 
        self.lbl_toast.hide()
        self.lbl_toast.setAlignment(Qt.AlignCenter)
        
        # UI HACK (Click-to-Dismiss): Eğer ölümcül bir hata ekranda kalırsa, pilot üstüne tıklayarak kapatabilsin.
        self.lbl_toast.mousePressEvent = lambda event: self._hide_toast()
        # top_layout.addWidget(self.lbl_toast) ---> SİLİNDİ! Artık tamamen özgür.
        
        # UI ESTETİĞİ: Havada asılı durma hissi için Gölgelendirme (Drop Shadow)
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtCore import QPropertyAnimation, QByteArray, QPoint
        
        shadow = QGraphicsDropShadowEffect(self.lbl_toast)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(Qt.black)
        self.lbl_toast.setGraphicsEffect(shadow)
        
        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self._hide_toast)
        
        # UI Animasyon nesnemiz: Artık Şeffaflık (Opacity) değil, Pozisyon (pos) animasyonu kullanıyoruz!
        self.toast_anim = QPropertyAnimation(self.lbl_toast, b"pos")
        self.toast_anim.setDuration(400) # 400ms süzülme süresi
        
        # Eğer animasyon yukarı kaçış ise (Y ekseni 0'ın altına indiyse) widget'ı tamamen gizle.
        self.toast_anim.finished.connect(lambda: self.lbl_toast.hide() if self.toast_anim.endValue().y() < 0 else None)
        
        self.btn_notifications = QPushButton("📢")
        self.btn_notifications.setFixedHeight(35)
        self.btn_notifications.setMinimumWidth(60)
        self.btn_notifications.setStyleSheet(self._get_btn_style("#2A2A2A", "#3A3A3A", "#151515"))
        self.btn_notifications.clicked.connect(self._show_notifications_menu)
        top_layout.addWidget(self.btn_notifications)
        top_layout.addSpacing(10)

        # --- EKLENEN DONANIM STANDARTLARI ---
        self.lbl_gamepad = QLabel("🎮 🔴") # Başlangıçta koptu varsayıyoruz
        self.lbl_battery = QLabel("🔋 %0.0")
        self.lbl_voltage = QLabel("⚡ 0.00V") 
        # (MİMARİ TEMİZLİK: Derinlik (Depth) verisi HUD'a taşınacağı için buradan silindi)
        
        for lbl in [self.lbl_gamepad, self.lbl_battery, self.lbl_voltage]:
            lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #AAAAAA; padding: 0 10px; border: none; background-color: transparent;")
            top_layout.addWidget(lbl)


    def _get_btn_style(self, base_color, hover_color, pressed_color):
        return f"""
            QPushButton {{ 
                background-color: {base_color}; 
                color: white; 
                border-radius: 4px; 
                font-weight: bold; 
                border: none; 
                font-size: 14px;
                padding: 6px 20px; 
            }}
            QPushButton:hover {{ background-color: {hover_color}; }}
            QPushButton:pressed {{ background-color: {pressed_color}; }}
            QPushButton:disabled {{ background-color: {base_color}; color: #FFFFFF; }}
        """

    def _toggle_lock(self):
        self.btn_lock.setText("🔓")
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText("Bağlantıyı Kes (Onayla)") 
        self.btn_connect.setStyleSheet(self._get_btn_style("#D35400", "#E67E22", "#A04000")) 
        self.lock_timer.start(3000) 
        
    def _relock(self):
        self.btn_lock.setText("🔒")
        self.btn_connect.setEnabled(False)
        self.btn_connect.setText("Bağlantı Aktif")
        self.btn_connect.setStyleSheet(self._get_btn_style("#1E8449", "#27AE60", "#145A32"))
        
    def _on_connect_clicked(self):
        self.lock_timer.stop()
        self.btn_lock.hide() 
        self.connect_clicked.emit() 

    # --- HOLD-TO-ARM MEKANİZMASI (GERİ BİLDİRİMLİ YAPI) ---
    def _start_arm_hold(self):
        self.arm_countdown = 3
        hedef_durum = "Arm Ediliyor" if not self.is_currently_armed else "Disarm Ediliyor"
        self.lbl_global_armed.setText(f"{hedef_durum}... {self.arm_countdown}")
        self.lbl_global_armed.setStyleSheet(self._get_btn_style("#D68910", "#E69A28", "#A86A08")) 
        self.arm_timer.start(1000) 
        
    def _arm_tick(self):
        self.arm_countdown -= 1
        if self.arm_countdown <= 0:
            self.arm_timer.stop()
            # ARTIK KENDİ KENDİNE YEŞİL OLMAYACAK! "İşleniyor" durumuna geçip Jetson'dan onay bekleyecek.
            self.lbl_global_armed.setText("İşleniyor...") 
            self.lbl_global_armed.setStyleSheet(self._get_btn_style("#5D6D7E", "#85929E", "#34495E")) # Gri/Bekleme Rengi
            
            self.arm_ui_command.emit(not self.is_currently_armed) 
        else:
            hedef_durum = "Arm Ediliyor" if not self.is_currently_armed else "Disarm Ediliyor"
            self.lbl_global_armed.setText(f"{hedef_durum}... {self.arm_countdown}")

    def _cancel_arm_hold(self):
        if self.arm_timer.isActive():
            self.arm_timer.stop()
            self.update_armed_state(self.is_currently_armed)

    # --- DURUM GÜNCELLEMELERİ ---    
    def set_ui_connecting(self):
        self.btn_connect.setEnabled(False)
        self.status_led.setText("🟡") 
        self.btn_connect.setText("Bağlanılıyor...")
        self.btn_connect.setStyleSheet(self._get_btn_style("#D68910", "#E69A28", "#A86A08"))
        
    def set_ui_disconnecting(self):
        self.btn_connect.setEnabled(False)
        self.btn_connect.setText("Kapatılıyor...")
        
    def set_ui_error(self):
        self.btn_connect.setEnabled(True) 
        self.status_led.setText("🔴")
        self.btn_connect.setText("Bağlanılamadı! Tekrar Dene")
        self.btn_connect.setStyleSheet(self._get_btn_style("#A0522D", "#C0392B", "#641E16"))

    def set_ui_connection_failed(self):
        self.btn_connect.setEnabled(True)
        self.status_led.setText("🟠") 
        self.btn_connect.setText("Bağlanılamadı, Tekrar Deneyiniz")
        self.btn_connect.setStyleSheet(self._get_btn_style("#D35400", "#E67E22", "#A04000"))
        
    def set_ui_connection_lost(self):
        self.btn_connect.setEnabled(True)
        self.btn_lock.hide()
        self.status_led.setText("🔴")
        self.btn_connect.setText("Bağlantı Koptu!")
        self.btn_connect.setStyleSheet(self._get_btn_style("#8B0000", "#A00000", "#600000"))
        self.lbl_global_armed.setEnabled(False)

    def set_ui_connected(self):
        self.status_led.setText("🟢")
        self.btn_lock.show() 
        self.btn_lock.setText("🔒")
        self.btn_connect.setText("Bağlantı Aktif")
        self.btn_connect.setStyleSheet(self._get_btn_style("#1E8449", "#27AE60", "#145A32"))
        self.btn_connect.setEnabled(False) 
        self.lbl_global_armed.setEnabled(True)
        
    def set_ui_disconnected(self):
        self.status_led.setText("⚪")
        self.btn_lock.hide()
        self.btn_connect.setText("Sisteme Bağlan")
        self.btn_connect.setStyleSheet(self._get_btn_style("#8B0000", "#A00000", "#600000")) 
        self.btn_connect.setEnabled(True)
        self.lbl_global_armed.setEnabled(False) 
        self.lbl_battery.setText("🔋 %0.0")
        self.lbl_voltage.setText("⚡ 0.00V")
        # Derinlik sıfırlama kodu silindi
        
    def update_armed_state(self, is_armed: bool):
        # Eğer kullanıcı hala butona basılı tutuyorsa (sayım devam ediyorsa) Jetson verisini yoksay
        if self.arm_timer.isActive():
            return
            
        self.is_currently_armed = is_armed
        if is_armed:
            self.lbl_global_armed.setText("Armed")
            self.lbl_global_armed.setStyleSheet(self._get_btn_style("#1E8449", "#27AE60", "#145A32"))
        else:
            self.lbl_global_armed.setText("Disarmed")
            self.lbl_global_armed.setStyleSheet(self._get_btn_style("#8B0000", "#A00000", "#600000"))
            
    # YENİ: Kumanda bağlantı durumunu güncelleyen fonksiyon
    def update_gamepad_state(self, is_connected: bool):
        if is_connected:
            self.lbl_gamepad.setText("🎮 🟢")
        else:
            self.lbl_gamepad.setText("🎮 🔴")
            
    # MİMARİ GÜNCELLEME: Derinlik parametresi uçuruldu
    def update_telemetry_values(self, battery, voltage):
        self.lbl_battery.setText(f"🔋 %{battery}")
        self.lbl_voltage.setText(f"⚡ {voltage:.2f}V")

    # --- MİMARİ ZIRH: APTAL UI SUNUM MANTIĞI (PRESENTATION LOGIC) ---
    def _hide_toast(self):
        """Toast'ı yavaşça ekranın üstüne kaydırır ve gölgeyi temizler (Slide-Up)"""
        from PySide6.QtCore import QPoint
        current_x = self.lbl_toast.x()
        self.toast_anim.setStartValue(self.lbl_toast.pos())
        self.toast_anim.setEndValue(QPoint(current_x, -100))
        
        # MİMARİ ZIRH: Animasyon yukarı doğru bittiğinde, gölgeyi sil ve widget'ı tamamen gizle!
        def _on_finish():
            if self.toast_anim.endValue().y() < 0:
                self.lbl_toast.graphicsEffect().setEnabled(False) # Gölgeyi devre dışı bırak
                self.lbl_toast.hide()
                
        # Önceki bağlantıları temizle ve yenisini bağla
        try: self.toast_anim.finished.disconnect() 
        except: pass
        self.toast_anim.finished.connect(_on_finish)
        
        self.toast_anim.start()

    # MİMARİ ZIRH: UI karar vermez! Kararı 'show_popup' parametresi ile MainWindow verir.
    def add_notification(self, message: str, msg_type: str, show_popup: bool = True):
        """Orkestra şefinden gelen uyarıyı alır, anlamına bakmaz, ne emredilirse onu çizer."""
        if not message:
            return
            
        new_alert = (msg_type, message)
        
        # 1. GEÇMİŞ (HISTORY) KAYDI
        self.notification_history.insert(0, new_alert)
        if len(self.notification_history) > 50:
            self.notification_history.pop()

        # 2. RENK KARARI (Sunum mantığı - Presentation Logic)
        bg_color = "#333333"
        if msg_type in ["CRITICAL", "FATAL", "ERROR"]:
            bg_color = "#8B0000"
        elif msg_type == "WARNING":
            bg_color = "#D68910"
        elif msg_type == "INFO":
            bg_color = "#2980B9"

        # 3. YUMUŞAK TOAST ANİMASYONU (ŞARTLI ÇALIŞTIRMA)
        if show_popup:
            # MAYIN İMHASI: Yeni mesaj geldiğinde eğer eski mesaj hala ekrandaysa, sayacını durdur!
            if self.toast_timer.isActive():
                self.toast_timer.stop()

            from PySide6.QtCore import QPoint
            
            self.lbl_toast.setText(f" {message} ")
            
            self.lbl_toast.setStyleSheet(f"""
                background-color: {bg_color}; 
                color: #FFFFFF; 
                border-radius: 8px; 
                font-weight: bold; 
                padding: 6px 20px; 
                font-size: 14px;
                border: none; 
            """)
            self.lbl_toast.adjustSize() 
            
            parent_width = self.window().width()
            toast_width = self.lbl_toast.width()
            center_x = (parent_width - toast_width) // 2
            
            start_pos = QPoint(center_x, -100)
            end_pos = QPoint(center_x, 40)
            
            self.lbl_toast.move(start_pos) 
            
            if self.lbl_toast.graphicsEffect():
                self.lbl_toast.graphicsEffect().setEnabled(True)
                
            self.lbl_toast.raise_()        
            self.lbl_toast.show()          
            
            from PySide6.QtCore import QEasingCurve
            self.toast_anim.setEasingCurve(QEasingCurve.OutExpo)
            
            self.toast_anim.setStartValue(start_pos)
            self.toast_anim.setEndValue(end_pos)
            self.toast_anim.start()
            
            # ANAYASA ZIRHI: FATAL mesaj gelirse ekranın üstünde çakılı kalsın. (Zamanlayıcı çalışmasın)
            if msg_type != "FATAL":
                self.toast_timer.start(3000)

        # 4. BUTON GÜNCELLEMESİ
        count = len(self.notification_history)
        self.btn_notifications.setText(f"📢 ({count})")
        
        # MİMARİ ZIRH: Eğer INFO geldiyse sağ üstteki butonu maviye boyayıp göz yorma, standart renkte bırak.
        if msg_type == "INFO":
            self.btn_notifications.setStyleSheet(self._get_btn_style("#2A2A2A", "#3A3A3A", "#151515"))
        else:
            self.btn_notifications.setStyleSheet(self._get_btn_style(bg_color, bg_color, bg_color))

    def _show_notifications_menu(self):
        """Butona tıklandığında eski uyarıları Scroll mantığı ile gösterir."""
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QWidgetAction
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1A1A1A; color: white; border: 1px solid #444; border-radius: 4px; } 
        """)
        
        # İçine koyacağımız Widget
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll_layout.setSpacing(2)
        
        if not self.notification_history:
            lbl = QLabel("Uyarı geçmişi temiz.")
            lbl.setStyleSheet("color: #888; padding: 10px; font-size: 13px;")
            scroll_layout.addWidget(lbl)
        else:
            # MİMARİ ZIRH: UI artık dedektiflik (string parsing) yapmıyor, doğrudan veri etiketine bakıyor!
            for alert_type, alert_msg in self.notification_history:
                lbl = QLabel(f"[{alert_type}] {alert_msg}")
                
                if alert_type in ["CRITICAL", "FATAL", "ERROR"]:
                    lbl.setStyleSheet("color: #FF5555; padding: 5px; font-weight: bold; border-bottom: 1px solid #333;")
                elif alert_type == "WARNING":
                    lbl.setStyleSheet("color: #FFAA00; padding: 5px; font-weight: bold; border-bottom: 1px solid #333;")
                else:
                    lbl.setStyleSheet("color: #CCCCCC; padding: 5px; border-bottom: 1px solid #333;")
                scroll_layout.addWidget(lbl)
                
        # Kaydırma (Scroll) Alanı
        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # MİMARİ ZIRH: Tam 4 mesaj gösterecek şekilde yükseklik ayarı (Yaklaşık 125px)
        scroll_area.setMaximumHeight(125) 
        scroll_area.setMinimumWidth(300)
        
        # UI ESTETİĞİ: Taktiksel, ince ve okları gizlenmiş karanlık Scrollbar!
        scroll_area.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background-color: transparent; 
            }
            QScrollBar:vertical {
                border: none;
                background-color: #1A1A1A;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #444444;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px; 
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # ScrollArea'yı menüye bağla
        scroll_action = QWidgetAction(menu)
        scroll_action.setDefaultWidget(scroll_area)
        menu.addAction(scroll_action)
                
        # Dropdown menüyü aç
        menu.exec(self.btn_notifications.mapToGlobal(self.btn_notifications.rect().bottomLeft()))
        
        # Menü okunduktan sonra dikkat çekici rengi sıfırla
        self.btn_notifications.setStyleSheet(self._get_btn_style("#2A2A2A", "#3A3A3A", "#151515"))