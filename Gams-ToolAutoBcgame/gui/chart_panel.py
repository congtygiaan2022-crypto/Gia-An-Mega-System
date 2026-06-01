import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
from typing import List

# Cấu hình matplotlib cho giao diện dark mode
matplotlib.use("TkAgg")
plt.style.use("dark_background")

class ChartPanel(ctk.CTkFrame):
    """Panel hiển thị biểu đồ lợi nhuận (P&L)"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self.header = ctk.CTkLabel(self, text="Biểu đồ Lợi nhuận (P&L)", font=ctk.CTkFont(size=14, weight="bold"))
        self.header.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Tạo Figure
        self.fig, self.ax = plt.subplots(figsize=(5, 3), dpi=100)
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#1e1e1e')
        
        self.ax.tick_params(colors='white')
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#444444')
            
        self.line, = self.ax.plot([], [], color='#00aaff', linewidth=2, marker='o', markersize=4)
        self.ax.set_xlabel("Số phiên cược", color='white', fontsize=8)
        self.ax.set_ylabel("Lợi nhuận (USDT)", color='white', fontsize=8)
        
        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.canvas_widget.configure(bg='#2b2b2b', highlightthickness=0)

    def update_chart(self, profit_history: List[float]):
        """Cập nhật dữ liệu biểu đồ"""
        if not profit_history:
            return
            
        x = list(range(len(profit_history)))
        y = profit_history
        
        self.line.set_data(x, y)
        
        # Tự động scale trục
        if len(x) > 0:
            self.ax.set_xlim(0, max(1, len(x) - 1))
            min_y = min(y) - 5
            max_y = max(y) + 5
            self.ax.set_ylim(min_y, max_y)
            
        self.canvas.draw()
