class BaseVideoStreamer:
    """
    Tüm video akış (USB Kamera, IP Kamera, GStreamer vb.) donanımlarının 
    uymak zorunda olduğu şablon (Interface) sınıfı.
    DIP Gereği: Manager katmanı sadece bu arayüze güvenir.
    
    Not: QThread ile metaclass çatışması yaşamamak için ABC kullanılmamıştır.
    """

    def start(self):
        """Video akışını donanımsal veya ağsal olarak başlatır."""
        raise NotImplementedError("Alt sınıf start() metodunu yazmak zorundadır!")

    def stop(self):
        """Video akışını durdurur ve kaynakları serbest bırakır."""
        raise NotImplementedError("Alt sınıf stop() metodunu yazmak zorundadır!")

    def is_running(self) -> bool:
        """
        KRİTİK: İşçinin aktif olup olmadığını döner. 
        Bu sayede Manager, alt katmanın Qt kullanıp kullanmadığını bilmek zorunda kalmaz.
        """
        raise NotImplementedError("Alt sınıf is_running() metodunu yazmak zorundadır!")

    def read_frame(self):
        """
        Kameradan anlık bir kare okur.
        Push (Sinyal) modeli kullanılıyorsa somut sınıfta sadece 'pass' yazılabilir,
        ancak mimari sözleşme gereği bu metod tanımlanmak zorundadır.
        """
        raise NotImplementedError("Alt sınıf read_frame() metodunu yazmak zorundadır!")