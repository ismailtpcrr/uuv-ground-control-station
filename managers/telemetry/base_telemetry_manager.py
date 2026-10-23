from abc import ABC, abstractmethod

class BaseTelemetryManager:
    """
    Telemetri yöneticisinin uymak zorunda olduğu anayasa (Arayüz).
    UI katmanı sadece bu metodları bilebilir.
    Metaclass çökmesini engellemek için ABC kullanılmamış, Saf (Pure) sınıf yapılmıştır.
    """

    @abstractmethod
    def start_telemetry_loop(self):
        """Araçtan veri dinleme döngüsünü başlatır."""
        pass

    @abstractmethod
    def stop_telemetry_loop(self):
        """Araçtan veri dinleme döngüsünü güvenle durdurur."""
        pass

    @abstractmethod
    def get_telemetry_signal(self):
        """
        UI'ın (Arayüzün) güncel verileri anlık alabilmesi için
        bağlanacağı (connect) sinyali döndürür.
        """
        pass