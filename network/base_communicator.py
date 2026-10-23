from abc import ABC, abstractmethod

class BaseCommunicator(ABC):
    """
    Tüm haberleşme sınıflarının (ZMQ, WiFi, Lazer, Akustik vb.) 
    uymak ZORUNDA olduğu şablon (Interface) sınıfımız.
    """

    @abstractmethod
    def connect(self, host: str, port: int) -> bool:
        """
        Belirtilen IP adresi ve porta bağlanır.
        Başarılıysa True, başarısızsa False döner.
        """
        pass

    @abstractmethod
    def send_data(self, data: dict) -> bool:
        """
        Sözlük (dict) formatındaki veriyi (JSON olarak) karşıya iletir.
        """
        pass

    @abstractmethod
    def receive_data(self) -> dict:
        """
        Karşıdan gelen veriyi dinler ve sözlük (dict) olarak döndürür.
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        Bağlantıyı güvenli bir şekilde kapatır.
        """
        pass