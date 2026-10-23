class CommandData:
    """
    İnsansız Deniz Aracına (İDA) gönderilecek olan komutların standart veri modeli (DTO).
    Ağ katmanı sadece bu modeli tanır, arayüzdeki slider'lar ile ilgilenmez.
    """
    def __init__(self, forward_back=0.0, left_right=0.0, up_down=0.0, yaw=0.0, armed=False):
        self.forward_back = forward_back
        self.left_right = left_right
        self.up_down = up_down
        self.yaw = yaw
        self.armed = armed

    def to_dict(self):
        """Ağ üzerinden (ZMQ/JSON) gönderilmek üzere veriyi sözlüğe çevirir."""
        return {
            "forward_back": self.forward_back,
            "left_right": self.left_right,
            "up_down": self.up_down,
            "yaw": self.yaw,
            "armed": self.armed
        }