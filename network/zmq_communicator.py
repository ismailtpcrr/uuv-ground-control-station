import zmq
import json
from network.base_communicator import BaseCommunicator

class ZmqCommunicator(BaseCommunicator):
    """
    ZeroMQ (pyzmq) kütüphanesini kullanarak İDA ile TCP üzerinden 
    çift yönlü ve hızlı haberleşmeyi sağlayan sınıfımız.
    """

    def __init__(self):
        # Fabrika (Context) uygulama ilk açıldığında 1 kez kurulur ve hep yaşar.
        self.context = zmq.Context()
        self.socket = None
        self.is_connected = False

    def connect(self, host: str, port: int) -> bool:
        try:
            # 1. ZIRH: Eğer hafızada eski, ölü bir soket (boru) kalmışsa önce onu kesin olarak yok et!
            if self.socket:
                self.socket.close()
                self.socket = None

            # PAIR soket tipi, 1'e 1 (Yer İstasyonu <-> İDA) kesintisiz iletişim için idealdir.
            self.socket = self.context.socket(zmq.PAIR)
            
            # --- YENİ EKLENEN ZIRHLAR (Kopmaları ve Şişmeleri Engeller) ---
            self.socket.setsockopt(zmq.SNDHWM, 2)
            self.socket.setsockopt(zmq.RCVHWM, 2)
            self.socket.setsockopt(zmq.LINGER, 0)
            
            # DONANIM ZIRHI (Fast Fail): İşletim sisteminin ve ZMQ'nun inatçı beklemelerini kır!
            self.socket.setsockopt(zmq.TCP_KEEPALIVE, 1)
            
            # (ÇAKIŞMA ÖNLEME: NOBLOCK bayrağını bozmamak için RCVTIMEO/SNDTIMEO kaldırıldı)
            
            # 2. Karşı taraf (Terminal/Araç) kapandığında bağlantıyı umutla askıda tutma, anında düşür!
            self.socket.setsockopt(zmq.IMMEDIATE, 1)

            connection_string = f"tcp://{host}:{port}"
            self.socket.connect(connection_string)
            self.is_connected = True
            return True
            
        except Exception as e:
            print(f"ZMQ Bağlantı hatası: {e}")
            return False

    def send_data(self, data: dict) -> bool:
        if not self.is_connected:
            return False
            
        try:
            # Gelen dict verisini JSON string'e çevirip gönderiyoruz.
            json_data = json.dumps(data)
            # zmq.NOBLOCK: Veri gitmese bile programı dondurma, yola devam et!
            self.socket.send_string(json_data, flags=zmq.NOBLOCK)
            return True
        except zmq.Again:
            # Karşı taraf o an meşgulse bekleme yapmaz, geçer.
            return False 
        except Exception as e:
            print(f"ZMQ Gönderme hatası: {e}")
            return False

    def receive_data(self) -> dict:
        if not self.is_connected:
            return {}
            
        last_message = None
        
        try:
            # MİMARİ ZIRH: "Queue Draining" (Kuyruk Boşaltma)
            # RAM'de birikmiş ne kadar 'geçmiş' paket varsa hepsini şimşek hızında oku.
            # Sadece en sondaki (en güncel) paketi elimizde tutuyoruz.
            while True:
                last_message = self.socket.recv_string(flags=zmq.NOBLOCK)
                
        except zmq.Again:
            # Kuyruk tamamen boşaldığında buraya düşer (Geçmiş temizlendi).
            pass 
        except Exception as e:
            print(f"ZMQ Alma hatası: {e}")
            return {}

        # Döngü bitti. Elimizde taze mesaj yoksa (bağlantı koptuysa) boş dön.
        if not last_message:
            return {}
            
        try:
            # Sadece en taze paketi JSON'a çevirip sisteme ver.
            return json.loads(last_message)
        except json.JSONDecodeError:
            return {}

    def disconnect(self):
        if self.is_connected and self.socket:
            # Sadece boruyu (soketi) kırıp çöpe atıyoruz. Fabrikayı (context) ellemiyoruz!
            self.socket.close()
            self.socket = None
            self.is_connected = False