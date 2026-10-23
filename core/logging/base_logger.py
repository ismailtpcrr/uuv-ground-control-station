from abc import ABC, abstractmethod

class BaseLogger(ABC):
    """
    Loglama (Kayıt tutma) işlemleri için şablon (Interface) sınıfımız.
    C#'taki ILogger arayüzünün karşılığıdır.
    Sisteme eklenecek her yeni loglayıcı (Dosya, Veritabanı, Ekran vb.) 
    bu sınıftan türemek ve aşağıdaki 3 metodu yazmak ZORUNDADIR.
    """

    @abstractmethod
    def log_info(self, message: str):
        """
        Sistemin normal işleyişiyle ilgili bilgileri kaydeder.
        Örn: "Jetson'a bağlanıldı", "Motorlara %50 güç verildi."
        """
        pass

    @abstractmethod
    def log_warning(self, message: str):
        """
        Sistemi durdurmayan ama dikkat edilmesi gereken uyarıları kaydeder.
        Örn: "Pil %20'nin altına düştü", "Görüntüde anlık gecikme var."
        """
        pass

    @abstractmethod
    def log_error(self, message: str):
        """
        Sistemde oluşan kritik hataları kaydeder.
        Örn: "Jetson ile bağlantı koptu!", "Kamera bulunamadı."
        """
        pass