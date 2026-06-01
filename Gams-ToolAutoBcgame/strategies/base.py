"""
Base Strategy - Lớp cơ sở cho tất cả chiến thuật cược
"""
from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """Lớp cơ sở cho chiến thuật cược"""

    def __init__(self, base_amount: float, config: dict = None):
        self.base_amount = base_amount
        self.config = config or {}
        self.current_level = 0
        self.last_result = None  # 'won' | 'lost' | None

    @abstractmethod
    def get_next_amount(self) -> float:
        """Tính số tiền cược tiếp theo"""
        pass

    @abstractmethod
    def on_win(self):
        """Xử lý khi thắng"""
        pass

    @abstractmethod
    def on_lose(self):
        """Xử lý khi thua"""
        pass

    def reset(self):
        """Reset chiến thuật về trạng thái ban đầu"""
        self.current_level = 0
        self.last_result = None

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def get_info(self) -> str:
        """Mô tả trạng thái hiện tại"""
        return f"{self.name} | Mức: {self.current_level} | Tiếp theo: {self.get_next_amount():.2f}"
