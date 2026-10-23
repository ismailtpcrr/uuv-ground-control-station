from dataclasses import dataclass, field
from typing import List

@dataclass
class JoystickData:
    """
    Evrensel Kumanda Veri Paketi.
    Tüm donanım verisini ham olarak tutar ve kolay okunabilir özellikler (property) sunar.
    """
    axes: List[float] = field(default_factory=list)
    buttons: List[int] = field(default_factory=list)

    # (MİMARİ TEMİZLİK: 'is_armed' değişkeni kumandanın yetkisi alındığı için tamamen silindi.)

    # --- SOL ÇUBUK (HAREKET) ---
    @property
    def forward_back(self) -> float:
        """İleri/Geri (Axis 1). Yukarı -1, aşağı 1"""
        if len(self.axes) > 1: return self.axes[1]
        return 0.0

    @property
    def left_right(self) -> float:
        """Sağ/Sol Yengeç Yürüyüşü (Axis 0). Sola -1, sağa 1"""
        if len(self.axes) > 0: return self.axes[0]
        return 0.0

    # --- SAĞ ÇUBUK (DERİNLİK VE DÖNÜŞ) ---
    @property
    def up_down(self) -> float:
        """Yukarı/Aşağı Derinlik (Axis 3). Yukarı -1, aşağı 1"""
        if len(self.axes) > 3: return self.axes[3]
        return 0.0

    @property
    def yaw(self) -> float:
        """Kendi Etrafında Dönüş (Axis 2). Sola -1, sağa 1"""
        if len(self.axes) > 2: return self.axes[2]
        return 0.0