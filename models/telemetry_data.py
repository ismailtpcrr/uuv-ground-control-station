from dataclasses import dataclass, field
from typing import List

@dataclass
class TelemetryData:
    """
    İDA'dan (Jetson) gelen anlık sensör verilerini tutan SAF (Pure) DTO Sınıfı.
    SRP Gereği: Sadece veri taşır, parse (ayrıştırma) veya iş mantığı içermez.
    """
    depth: float = 0.0               # Derinlik (Metre)
    temperature: float = 0.0         # Su sıcaklığı (Derece)
    battery_level: float = 100.0     # Pil yüzdesi (%0.0 - %100.0)
    voltage: float = 0.0             # Anlık Voltaj (Arayüzde ⚡ 0.00V için)
    current_a: float = 0.0           # YENİ: Anlık Akım Tüketimi (Amper)
    heading: float = 0.0             # YENİ: Pusula Yönü (0-360 Derece)
    pitch: float = 0.0               # YENİ: Yunuslama (Burun aşağı/yukarı)
    roll: float = 0.0                # YENİ: Yuvarlanma (Sağa/Sola yatma)
    is_connected: bool = False       # Bağlantı durumu
    is_armed: bool = False           # YENİ: Sistemin Silahlı/Güvenli olma durumu
    status_msg: str = ""             # YENİ (STATUSTEXT): Jetson'dan gelen kritik uyarı mesajı
    msg_type: str = ""               # YENİ (STATUSTEXT): Uyarı tipi (INFO, WARNING, CRITICAL vb.)
    motor_speeds: List[float] = field(default_factory=lambda: [0.0] * 6)