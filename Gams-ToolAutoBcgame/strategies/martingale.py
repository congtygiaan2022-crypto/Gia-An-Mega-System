"""
Martingale Strategy - Nhân đôi sau mỗi lần thua
"""
from strategies.base import BaseStrategy


class MartingaleStrategy(BaseStrategy):
    """
    Martingale: Nhân đôi số tiền cược sau mỗi lần thua.
    Sau khi thắng, quay về mức ban đầu.
    ⚠️ Rủi ro cao nếu chuỗi thua dài!
    """
    display_name = "Martingale (Nhân đôi)"
    description = "Nhân đôi sau mỗi lần thua. Lý thuyết: thắng 1 lần bù tất cả. ⚠️ Rủi ro cao!"

    def __init__(self, base_amount: float, config: dict = None):
        super().__init__(base_amount, config)
        self.multiplier = config.get("multiplier", 2.0) if config else 2.0
        self.max_level = config.get("max_level", 6) if config else 6
        self.current_amount = base_amount

    def get_next_amount(self) -> float:
        return min(self.current_amount, self.base_amount * (self.multiplier ** self.max_level))

    def on_win(self):
        self.last_result = "won"
        self.current_level = 0
        self.current_amount = self.base_amount

    def on_lose(self):
        self.last_result = "lost"
        self.current_level += 1
        if self.current_level <= self.max_level:
            self.current_amount = self.base_amount * (self.multiplier ** self.current_level)
        else:
            # Đã đạt max level - giữ nguyên
            pass

    def reset(self):
        super().reset()
        self.current_amount = self.base_amount

    def get_info(self) -> str:
        display_level = min(self.current_level, self.max_level)
        return (f"Martingale | Cấp {self.current_level}/{self.max_level} | "
                f"Tiếp theo: {self.get_next_amount():.2f} "
                f"(x{self.multiplier**display_level:.1f})")
