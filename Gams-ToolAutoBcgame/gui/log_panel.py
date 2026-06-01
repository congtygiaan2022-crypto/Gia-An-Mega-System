import customtkinter as ctk
import tkinter as tk
from datetime import datetime

class LogPanel(ctk.CTkFrame):
    """Panel hiển thị log real-time với màu sắc"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self.header = ctk.CTkLabel(self, text="Nhật ký thời gian thực", font=ctk.CTkFont(size=14, weight="bold"))
        self.header.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Text area
        self.text_area = tk.Text(
            self, 
            bg="#1a1a1a", 
            fg="#ffffff", 
            font=("Consolas", 10),
            state="disabled",
            wrap="word",
            padx=10,
            pady=10,
            borderwidth=0
        )
        self.text_area.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Scrollbar
        self.scrollbar = ctk.CTkScrollbar(self, command=self.text_area.yview)
        self.scrollbar.grid(row=1, column=1, sticky="ns")
        self.text_area.configure(yscrollcommand=self.scrollbar.set)
        
        # Tags for coloring
        self.text_area.tag_config("INFO", foreground="#00aaff")
        self.text_area.tag_config("SUCCESS", foreground="#00ff00")
        self.text_area.tag_config("ERROR", foreground="#ff4444")
        self.text_area.tag_config("WARNING", foreground="#ffaa00")
        self.text_area.tag_config("BET", foreground="#ff00ff")
        self.text_area.tag_config("WIN", foreground="#00ff00", font=("Consolas", 10, "bold"))
        self.text_area.tag_config("LOSE", foreground="#ff4444", font=("Consolas", 10, "bold"))

    def add_log(self, message: str, level: str = "INFO"):
        """Thêm một dòng log mới"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.text_area.configure(state="normal")
        self.text_area.insert("end", formatted_message, level)
        self.text_area.see("end")
        self.text_area.configure(state="disabled")
        
    def clear(self):
        """Xóa toàn bộ log"""
        self.text_area.configure(state="normal")
        self.text_area.delete("1.0", "end")
        self.text_area.configure(state="disabled")
