"""
Fibonacci Strategy - Tăng theo dãy Fibonacci khi thua
"""
from strategies.base import BaseStrategy


class FibonacciStrategy(BaseStrategy):
    """
    Fibonacci: Tăng theo dãy Fibonacci khi thua.
    Khi thắng, quay lại 2 bước trước.
    Ít rủi ro hơn Martingale nhưng phục hồi chậm hơn.
    """
    display_name = "Fibonacci"
    description = "Tăng theo Fibonacci khi thua, lùi 2 bước khi thắng. Ít rủi ro hơn Martingale."

    SEQUENCE = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]

    def __init__(self, base_amount: float, config: dict = None):
        super().__init__(base_amount, config)
        custom_seq = config.get("sequence", self.SEQUENCE) if config else self.SEQUENCE
        self.sequence = custom_seq
        self.position = 0

    def get_next_amount(self) -> float:
        idx = min(self.position, len(self.sequence) - 1)
        return self.base_amount * self.sequence[idx]

    def on_win(self):
        self.last_result = "won"
        self.position = max(0, self.position - 2)

    def on_lose(self):
        self.last_result = "lost"
        self.position = min(self.position + 1, len(self.sequence) - 1)
        self.current_level = self.position

    def reset(self):
        super().reset()
        self.position = 0

    def get_info(self) -> str:
        fib_val = self.sequence[min(self.position, len(self.sequence)-1)]
        return (f"Fibonacci | Vị trí {self.position} (×{fib_val}) | "
                f"Tiếp theo: {self.get_next_amount():.2f}")
