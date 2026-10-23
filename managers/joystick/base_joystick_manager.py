from models import JoystickData

class BaseJoystickManager:
    """
    İş mantığı (Business) katmanındaki Joystick yöneticisi için şablon (Interface).
    UI katmanı sadece bu arayüzü tanıyacak.
    """

    def process_and_send(self, joy_data: JoystickData):
        """Gelen joystick verisini işler ve haberleşme katmanına iletir."""
        raise NotImplementedError("Alt sınıf process_and_send() metodunu yazmak zorundadır!")

    # --- MİMARİ BÜTÜNLÜK: Klasik OOP 'Getter' Metodu ---
    def get_connection_signal(self):
        """
        Gamepad bağlantı durumunu (True/False) dönen sinyal NESNESİNİ verir.
        UI bu metodu çağırarak dönen sinyale connect() ile bağlanır.
        """
        raise NotImplementedError("Alt sınıf get_connection_signal() metodunu yazmak zorundadır!")