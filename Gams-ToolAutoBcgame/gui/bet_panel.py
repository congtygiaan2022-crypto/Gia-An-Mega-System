import customtkinter as ctk

class BetPanel(ctk.CTkFrame):
    """Panel cấu hình tối giản - Chỉ giữ lại các thông số cần thiết"""
    
    def __init__(self, master, config: dict, **kwargs):
        super().__init__(master, **kwargs)
        self.config = config
        
        self.grid_columnconfigure(1, weight=1)
        
        # Header
        self.header = ctk.CTkLabel(self, text="CẤU HÌNH CƯỢC", font=ctk.CTkFont(size=14, weight="bold"), text_color="#00aaff")
        self.header.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 15), sticky="w")
        
        # --- PHẦN 1: SỐ TIỀN CƯỢC ---
        self.lbl_bet_title = ctk.CTkLabel(self, text="💰 CHẾ ĐỘ TIỀN CƯỢC:", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_bet_title.grid(row=1, column=0, columnspan=2, padx=10, pady=(5, 2), sticky="w")
        
        self.bet_mode = ctk.StringVar(value="all-in")
        
        self.rb_allin = ctk.CTkRadioButton(self, text="All-in (Toàn bộ số dư)", variable=self.bet_mode, value="all-in", 
                                           command=self._toggle_bet_entry, font=ctk.CTkFont(size=12))
        self.rb_allin.grid(row=2, column=0, columnspan=2, padx=20, pady=2, sticky="w")
        
        self.rb_fixed = ctk.CTkRadioButton(self, text="Tự nhập số tiền:", variable=self.bet_mode, value="fixed", 
                                            command=self._toggle_bet_entry, font=ctk.CTkFont(size=12))
        self.rb_fixed.grid(row=3, column=0, padx=20, pady=2, sticky="w")
        
        self.ent_fixed_amount = ctk.CTkEntry(self, placeholder_text="Ví dụ: 1000", width=120, height=32)
        self.ent_fixed_amount.grid(row=3, column=1, padx=10, pady=2, sticky="w")
        self.ent_fixed_amount.configure(state="disabled")

        # Stop Loss
        self.lbl_sl = ctk.CTkLabel(self, text="Cắt lỗ (USDT):", font=ctk.CTkFont(size=12))
        self.lbl_sl.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="w")
        self.ent_stop_loss = ctk.CTkEntry(self, placeholder_text="100.0", width=120, height=32)
        self.ent_stop_loss.insert(0, str(config.get("risk", {}).get("stop_loss", 100)))
        self.ent_stop_loss.grid(row=4, column=1, padx=10, pady=(10, 5), sticky="w")

        # --- PHẦN 2: CHỌN TRẬN ĐẤU ---
        self.lbl_match_title = ctk.CTkLabel(self, text="⚽ CHỌN TRẬN ĐẤU:", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_match_title.grid(row=5, column=0, columnspan=2, padx=10, pady=(15, 2), sticky="w")

        sel_config = config.get("selection", {})
        self.selection_mode = ctk.StringVar(value=sel_config.get("mode", "auto"))
        
        self.rb_auto = ctk.CTkRadioButton(self, text="Tự động quét (Wap.vn)", variable=self.selection_mode, value="auto", 
                                          command=self._toggle_match_entry, font=ctk.CTkFont(size=12))
        self.rb_auto.grid(row=6, column=0, columnspan=2, padx=20, pady=2, sticky="w")
        
        self.rb_manual = ctk.CTkRadioButton(self, text="Nhập tay tên trận:", variable=self.selection_mode, value="manual", 
                                            command=self._toggle_match_entry, font=ctk.CTkFont(size=12))
        self.rb_manual.grid(row=7, column=0, padx=20, pady=2, sticky="w")
        
        self.ent_manual_match = ctk.CTkEntry(self, placeholder_text="Arsenal vs Bayern", width=280, height=32)
        self.ent_manual_match.insert(0, sel_config.get("manual_name", ""))
        self.ent_manual_match.grid(row=7, column=1, padx=10, pady=2, sticky="w")
        
        # Note cuối
        self.lbl_note = ctk.CTkLabel(self, text="* Tool sẽ tự động tìm kèo Tài 0.5\nvà đặt cược theo cấu hình trên.", 
                                   font=ctk.CTkFont(size=11), text_color="#888888", justify="left")
        self.lbl_note.grid(row=8, column=0, columnspan=2, padx=10, pady=(20, 10), sticky="w")

        # Thiết lập trạng thái ban đầu
        self._toggle_match_entry()
        self._toggle_bet_entry()

    def _toggle_bet_entry(self):
        if self.bet_mode.get() == "fixed":
            self.ent_fixed_amount.configure(state="normal", fg_color="white", text_color="black")
        else:
            self.ent_fixed_amount.configure(state="disabled", fg_color="#333333", text_color="#888888")

    def _toggle_match_entry(self):
        if self.selection_mode.get() == "manual":
            self.ent_manual_match.configure(state="normal", fg_color="white", text_color="black")
        else:
            self.ent_manual_match.configure(state="disabled", fg_color="#333333", text_color="#888888")

    def get_settings(self) -> dict:
        """Lấy cài đặt từ giao diện"""
        try:
            sl_val = self.ent_stop_loss.get()
            sl = float(sl_val) if sl_val else 100.0
            
            fixed_val = self.ent_fixed_amount.get()
            fixed_amount = float(fixed_val) if fixed_val else 0.0
        except Exception:
            sl = 100.0
            fixed_amount = 0.0
            
        return {
            "betting": {
                "mode": self.bet_mode.get(),
                "fixed_amount": fixed_amount,
                "strategy": "custom",
                "bet_type": "ou",
            },
            "selection": {
                "mode": self.selection_mode.get(),
                "manual_name": self.ent_manual_match.get()
            },
            "risk": {
                "stop_loss": sl,
            }
        }

