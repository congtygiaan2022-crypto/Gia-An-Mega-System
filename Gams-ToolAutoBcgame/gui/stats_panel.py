import customtkinter as ctk
from typing import Dict, Any

class StatCard(ctk.CTkFrame):
    """Thành phần thẻ hiển thị một thông số đơn lẻ"""
    def __init__(self, master, title: str, value: str, color: str = "#00aaff", **kwargs):
        super().__init__(master, fg_color="#333333", corner_radius=10, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        self.lbl_title = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=12, weight="normal"), text_color="#aaaaaa")
        self.lbl_title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        
        self.lbl_value = ctk.CTkLabel(self, text=value, font=ctk.CTkFont(size=20, weight="bold"), text_color=color)
        self.lbl_value.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

    def update_value(self, value: str, color: str = None):
        self.lbl_value.configure(text=value)
        if color:
            self.lbl_value.configure(text_color=color)

class StatsPanel(ctk.CTkFrame):
    """Panel thống kê trực quan với dạng thẻ (Dashboard Cards)"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Tạo các thẻ thống kê
        self.card_balance = StatCard(self, "SỐ DƯ HIỆN TẠI", "0.00 USDT", "#28a745")
        self.card_balance.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.card_profit = StatCard(self, "LỢI NHUẬN PHIÊN", "0.00 USDT", "#00aaff")
        self.card_profit.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.card_winrate = StatCard(self, "TỈ LỆ THẮNG", "0%", "#ffc107")
        self.card_winrate.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        
        self.card_bets = StatCard(self, "TỔNG SỐ CƯỢC", "0", "#ffffff")
        self.card_bets.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

    def update_stats(self, stats: Dict[str, Any]):
        """Cập nhật các giá trị thống kê trên dashboard"""
        if "balance" in stats:
            self.card_balance.update_value(f"{stats['balance']:.2f} USDT")
            
        if "session_profit" in stats:
            profit = stats["session_profit"]
            color = "#28a745" if profit >= 0 else "#dc3545"
            self.card_profit.update_value(f"{profit:+.2f} USDT", color)
            
        if "win_rate" in stats:
            self.card_winrate.update_value(f"{stats['win_rate']:.1f}%")
            
        if "session_bets" in stats:
            self.card_bets.update_value(str(stats["session_bets"]))
            
        if "consecutive_losses" in stats:
            # Có thể thêm các thẻ phụ hoặc tooltip nếu cần
            pass
