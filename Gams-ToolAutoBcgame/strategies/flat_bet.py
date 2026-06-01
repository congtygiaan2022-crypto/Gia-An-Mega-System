"""
Flat Bet Strategy - Cược cùng một mức mỗi lần
"""
from strategies.base import BaseStrategy


class FlatBetStrategy(BaseStrategy):
    """
    Flat Bet: Cược cùng một số tiền cho mỗi lần.
    Đơn giản và an toàn nhất.
    """
    display_name = "Flat Bet (Cố định)"
    description = "Cược cùng một số tiền mỗi lần. An toàn nhất, phù hợp người mới."

    def get_next_amount(self) -> float:
        return self.base_amount

    def on_win(self):
        self.last_result = "won"

    def on_lose(self):
        self.last_result = "lost"

    def reset(self):
        super().reset()
