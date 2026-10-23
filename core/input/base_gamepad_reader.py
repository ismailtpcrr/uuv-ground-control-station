class BaseGamepadReader:
    """
    Tüm gamepad/joystick okuyucu donanımlarının uymak zorunda olduğu şablon.
    DIP Gereği: JoystickManager sadece bu arayüze güvenir.
    
    Not: QObject ile metaclass çatışması yaşamamak için ABC kullanılmamıştır.
    """

    def start(self) -> None:
        """Donanım okuma döngüsünü veya Timer'ı başlatır."""
        raise NotImplementedError("Alt sınıf start() metodunu yazmak zorundadır!")

    def stop(self) -> None:
        """Donanım okuma işlemini durdurur ve kaynakları serbest bırakır."""
        raise NotImplementedError("Alt sınıf stop() metodunu yazmak zorundadır!")

    def is_running(self) -> bool:
        """Okuyucunun o an aktif olup olmadığını döner."""
        raise NotImplementedError("Alt sınıf is_running() metodunu yazmak zorundadır!")

    def read_data(self):
        """
        Gamepad'den verileri çeken ana fonksiyondur. 
        Sistemimiz 'Push' (Signal) modeliyle çalıştığı için 
        bu metod veriyi toplar ve ilgili sinyalleri tetikler.
        """
        raise NotImplementedError("Alt sınıf read_data() metodunu yazmak zorundadır!")