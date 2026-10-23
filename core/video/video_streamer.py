import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from .base_video_streamer import BaseVideoStreamer # ÖNEMLİ: Importu unutma!

class VideoStreamer(QThread, BaseVideoStreamer):
    """
    Kameradan arka planda (ayrı bir Thread'de) görüntü okuyan sınıf.
    Arayüzün (UI) donmasını engeller.
    """
    
    # Yeni bir kare (fotoğraf) okunduğunda dışarıya fırlatılacak sinyal
    frame_ready = Signal(np.ndarray)

    def __init__(self, camera_source=0):
        # Önce her iki üst sınıfı da başlatıyoruz
        super().__init__()
        self.camera_source = camera_source
        self._is_running = False

    def run(self):
        """Thread (İşçi) başlatıldığında çalışacak ana döngü."""
        cap = cv2.VideoCapture(self.camera_source)
        
        # DONANIM ZIRHI: Kamera açılamazsa boşuna döngüye girme
        if not cap.isOpened():
            self._is_running = False
            return

        # DONANIM AYARI: Gecikmeyi (Latency) önlemek için dahili tamponu 1 kareye indiriyoruz.
        # Bu sayede 'bayat' kareleri değil, her zaman kameradan gelen EN SON kareyi okuruz.
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self._is_running = True

        while self._is_running:
            try:
                ret, frame = cap.read()
                
                if ret:
                    self.frame_ready.emit(frame)
                else:
                    # Görüntü gelmiyorsa kablo kopmuş veya sensör susmuş olabilir
                    self._is_running = False
                    break
            except Exception:
                self._is_running = False
                break
                
            # Saniyede yaklaşık 60-100 FPS üst sınır koyarak CPU'yu gereksiz yormuyoruz
            self.msleep(1) 

        # TEMİZLİK: Donanımı serbest bırak
        if cap.isOpened():
            cap.release()
        self._is_running = False

    def stop(self):
        """Kamera okuma işlemini güvenli bir şekilde durdurur."""
        self._is_running = False
        # MİMARİ DÜZELTME: Kendi 'while' döngümüzü kullandığımız için quit() (Qt Event Loop) gereksizdir.
        # Sadece bayrağı indirip thread'in döngüden çıkmasını (wait) beklemek en güvenli ve doğru yöntemdir.
        self.wait()
    
    def is_running(self) -> bool:
        """BaseVideoStreamer anayasasındaki zorunlu metod."""
        # Qt'nin dahili isRunning() metodu ile bizim flag'imizi harmanlıyoruz
        return self.isRunning() and self._is_running

    def read_frame(self):
        """
        BaseVideoStreamer anayasasındaki zorunlu metod.
        Bu işçi 'Push' (Sinyal) modeliyle çalıştığı için bu metod boş kalabilir,
        ancak sınıfta bulunması ZORUNLUDUR.
        """
        pass