"""
D'Alembert Strategy - Tăng 1 đơn vị khi thua, giảm 1 khi thắng
"""
from strategies.base import BaseStrategy


class DAlembert(BaseStrategy):
    """
    D'Alembert: Cân bằng hơn Martingale.
    - Thua: tăng thêm 1 đơn vị
    - Thắng: giảm 1 đơn vị
    Lý thuyết: số lần thắng = thua thì hòa vốn.
    """
    display_name = "D'Alembert"
    description = "Tăng 1 đơn vị khi thua, giảm 1 khi thắng. Cân bằng và ít rủi ro hơn Martingale."

    def __init__(self, base_amount: float, config: dict = None):
        super().__init__(base_amount, config)
        self.unit = config.get("unit", base_amount) if config else base_amount
        self.current_amount = base_amount

    def get_next_amount(self) -> float:
        return max(self.unit, self.current_amount)

    def on_win(self):
        self.last_result = "won"
        self.current_amount = max(self.unit, self.current_amount - self.unit)
        if self.current_level > 0:
            self.current_level -= 1

    def on_lose(self):
        self.last_result = "lost"
        self.current_amount += self.unit
        self.current_level += 1

    def reset(self):
        super().reset()
        self.current_amount = self.base_amount

    def get_info(self) -> str:
        return (f"D'Alembert | Cấp {self.current_level} | "
                f"Tiếp theo: {self.get_next_amount():.2f}")
