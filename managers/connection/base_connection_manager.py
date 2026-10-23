from PySide6.QtCore import QObject, Signal

class BaseConnectionManager(QObject):
    """
    Sistemin İDA (veya Simülasyon) ile olan bağlantı durumunu 
    yönetecek olan İş Mantığı (Business) arayüzü.
    
    Not: PySide6 sinyallerini (Event-Driven Mimari) kullanabilmek için 
    ABC yerine QObject'ten miras (inherit) alınmıştır.
    """

    # --- İŞARET FİŞEKLERİMİZ (Event Sinyalleri) ---
    # Bütün alt sistemler (Kamera, Gamepad, UI) bu sinyallere abone olacak.
    connected_signal = Signal()     # YEŞİL FİŞEK: "Sistem ayağa kalktı, işe koyulun!"
    disconnected_signal = Signal()  # KIRMIZI FİŞEK: "Bağlantı koptu, güvenli moda geçin!"

    def connect_to_vehicle(self, host: str, port: int) -> bool:
        """
        Belirtilen IP ve Port üzerinden araca bağlanma emrini verir.
        Başarılıysa True dönmeli ve 'connected_signal' fırlatmalıdır.
        """
        raise NotImplementedError("Bu metod alt sınıfta (ConnectionManager) ezilmelidir (override).")

    def disconnect_from_vehicle(self):
        """
        Araçla olan bağlantıyı güvenli bir şekilde keser.
        İşlem bitince veya hata anında 'disconnected_signal' fırlatmalıdır.
        """
        raise NotImplementedError("Bu metod alt sınıfta (ConnectionManager) ezilmelidir (override).")