class BaseVideoManager:
    """
    Video yöneticisi için şablon (Interface).
    UI katmanı sadece bu arayüzü tanıyacak.
    
    Not: QObject ile metaclass çatışması yaşamamak için ABC kullanılmamıştır.
    """

    def start_video(self):
        """Kamera akışını başlatma emri verir."""
        raise NotImplementedError("Alt sınıf start_video() metodunu yazmak zorundadır!")

    def stop_video(self):
        """Kamera akışını durdurma emri verir."""
        raise NotImplementedError("Alt sınıf stop_video() metodunu yazmak zorundadır!")

    # --- MİMARİ BÜTÜNLÜK: Property silindi, Saf OOP Getter metodu geldi ---
    def get_frame_signal(self):
        """
        UI katmanının kamera görüntülerini almak için bağlanacağı sinyal nesnesini verir.
        Kullanımı: manager.get_frame_signal().connect(fonksiyon)
        """
        raise NotImplementedError("Alt sınıf get_frame_signal() metodunu yazmak zorundadır!")