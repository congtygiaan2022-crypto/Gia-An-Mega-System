import customtkinter as ctk
import json
import os
import threading
import time
import random
import re
from loguru import logger
from datetime import datetime

from core.browser import BrowserController
from core.session import SessionManager
from core.scraper import BCGameScraper
from core.scraper_wap import WapScraper
from core.selector import MatchSelector
from core.bettor import BettingEngine
from core.reporter import GoogleSheetsReporter
from gui.bet_panel import BetPanel
from gui.stats_panel import StatsPanel
from gui.log_panel import LogPanel

class MainWindow(ctk.CTk):
    """Giao diện Dashboard chuyên nghiệp cho Tool Auto BCGame All-in"""
    
    def __init__(self):
        super().__init__()
        
        self.title("BCGAME PRO AUTO-BETTING V3")
        self.geometry("1150x800")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.config = self._load_config()
        self.is_running = False

        # Initialize Core placeholders
        self.browser = None
        self.session = None
        self.scraper_bc = None
        self.scraper_wap = None
        self.selector = None
        self.bettor = None
        self.reporter = None
        self.auditor = None

        # Pending bet state (used across threads)
        self.pending_match = None
        self.pending_report = None
        self.pending_odd = None
        self.pending_balance = None
        self.pending_won = None
        self.pending_bet_amount = None

        self._setup_ui()

    def _setup_ui(self):
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # --- HEADER (Settings & Controls - HORIZONTAL) ---
        self.header = ctk.CTkFrame(self, corner_radius=0, height=160)
        self.header.grid(row=0, column=0, sticky="ew")
        
        # Sub-frame 1: Login Info
        self.frm_login = ctk.CTkFrame(self.header, fg_color="transparent")
        self.frm_login.grid(row=0, column=0, padx=10, pady=10, sticky="n")
        ctk.CTkLabel(self.frm_login, text="ĐĂNG NHẬP", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.ent_phone = ctk.CTkEntry(self.frm_login, placeholder_text="Số điện thoại", width=140)
        self.ent_phone.insert(0, self.config.get("login", {}).get("phone", ""))
        self.ent_phone.pack(pady=2)
        self.ent_pass = ctk.CTkEntry(self.frm_login, placeholder_text="Mật khẩu", show="*", width=140)
        self.ent_pass.insert(0, self.config.get("login", {}).get("password", ""))
        self.ent_pass.pack(pady=2)
        self.ent_2fa = ctk.CTkEntry(self.frm_login, placeholder_text="2FA Key", width=140)
        self.ent_2fa.insert(0, self.config.get("login", {}).get("2fa_key", ""))
        self.ent_2fa.pack(pady=2)
        
        # Sub-frame 2: System Config
        self.frm_sys = ctk.CTkFrame(self.header, fg_color="transparent")
        self.frm_sys.grid(row=0, column=1, padx=10, pady=10, sticky="n")
        ctk.CTkLabel(self.frm_sys, text="HỆ THỐNG", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.ent_proxy = ctk.CTkEntry(self.frm_sys, placeholder_text="Proxy (ip:port:u:p)", width=180)
        self.ent_proxy.insert(0, self.config.get("ui", {}).get("proxy", ""))
        self.ent_proxy.pack(pady=2)
        self.ent_sheet = ctk.CTkEntry(self.frm_sys, placeholder_text="URL Google Sheet", width=180)
        self.ent_sheet.insert(0, self.config.get("ui", {}).get("sheet_url", ""))
        self.ent_sheet.pack(pady=2)
        self.ent_api_key = ctk.CTkEntry(self.frm_sys, placeholder_text="API-Football Key", show="*", width=180)
        self.ent_api_key.insert(0, self.config.get("api", {}).get("football_api_key", ""))
        self.ent_api_key.pack(pady=2)
        
        # Sub-frame 3: Bet Config
        self.bet_panel = BetPanel(self.header, self.config, fg_color="transparent")
        self.bet_panel.grid(row=0, column=2, padx=10, pady=10, sticky="n")
        
        # Sub-frame 4: Buttons (Controls)
        self.frm_btns = ctk.CTkFrame(self.header, fg_color="transparent")
        self.frm_btns.grid(row=0, column=3, padx=10, pady=10, sticky="n")
        
        self.btn_save = ctk.CTkButton(self.frm_btns, text="LƯU CẤU HÌNH", fg_color="#555", width=120, command=self._save_config)
        self.btn_save.grid(row=0, column=0, padx=5, pady=2)
        
        self.btn_login = ctk.CTkButton(self.frm_btns, text="1. ĐĂNG NHẬP", font=ctk.CTkFont(weight="bold"), fg_color="#17a2b8", width=120, command=self._start_manual_login)
        self.btn_login.grid(row=0, column=1, padx=5, pady=2)

        self.btn_auto_bet = ctk.CTkButton(self.frm_btns, text="2. AUTO CƯỢC", font=ctk.CTkFont(weight="bold"), fg_color="#28a745", width=120, command=self._start_auto_bet)
        self.btn_auto_bet.grid(row=1, column=0, padx=5, pady=2)
        
        self.btn_auto_care = ctk.CTkButton(self.frm_btns, text="3. AUTO CARE", font=ctk.CTkFont(weight="bold"), fg_color="#ffc107", text_color="black", width=120, command=self._start_auto_care)
        self.btn_auto_care.grid(row=1, column=1, padx=5, pady=2)
        
        self.btn_auto_report = ctk.CTkButton(self.frm_btns, text="4. BÁO CÁO", font=ctk.CTkFont(weight="bold"), fg_color="#6f42c1", width=120, command=self._start_auto_report)
        self.btn_auto_report.grid(row=2, column=0, padx=5, pady=2)
        
        self.btn_stop = ctk.CTkButton(self.frm_btns, text="DỪNG AUTO", font=ctk.CTkFont(weight="bold"), fg_color="#dc3545", width=120, command=self._stop_execution, state="disabled")
        self.btn_stop.grid(row=2, column=1, padx=5, pady=2)

        self.btn_check_login = ctk.CTkButton(self.frm_btns, text="KIỂM TRA ĐN", fg_color="#17a2b8", width=250, command=self._check_manual_login, state="disabled")
        self.btn_check_login.grid(row=3, column=0, columnspan=2, padx=5, pady=2)

        # --- MAIN DASHBOARD (Tabview) ---
        self.main_area = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0)
        self.main_area.grid(row=1, column=0, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self.main_area, fg_color="#222")
        self.tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.tab_bet = self.tabview.add("1. ĐẶT CƯỢC")
        self.tab_care = self.tabview.add("2. THEO DÕI KẾT QUẢ")
        self.tab_report = self.tabview.add("3. BÁO CÁO")

        # Setup 1. Đặt Cược Tab
        self.stats_panel = StatsPanel(self.tab_bet)
        self.stats_panel.pack(fill="x", padx=10, pady=10)
        
        self.tracking_card = ctk.CTkFrame(self.tab_bet, fg_color="#2b2b2b", height=100)
        self.tracking_card.pack(fill="x", padx=10, pady=5)
        self.lbl_match_info = ctk.CTkLabel(self.tracking_card, text="Đang đợi phiên làm việc mới...", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_match_info.pack(pady=10)
        
        self.log_panel = LogPanel(self.tab_bet)
        self.log_panel.pack(fill="both", expand=True, padx=10, pady=10)

        # Setup 2. Theo Dõi Tab
        self.lbl_care_info = ctk.CTkLabel(self.tab_care, text="DANH SÁCH TRẬN ĐANG THEO DÕI (GOOGLE SEARCH)", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_care_info.pack(pady=10)
        self.care_list = ctk.CTkTextbox(self.tab_care, height=300)
        self.care_list.pack(fill="both", expand=True, padx=20, pady=10)

        # Setup 3. Báo Cáo Tab
        self.lbl_report_info = ctk.CTkLabel(self.tab_report, text="LỊCH SỬ BÁO CÁO ALL-IN", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_report_info.pack(pady=10)
        self.report_list = ctk.CTkTextbox(self.tab_report, height=300)
        self.report_list.pack(fill="both", expand=True, padx=20, pady=10)

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_config(self):
        try:
            if "login" not in self.config: self.config["login"] = {}
            self.config["login"]["phone"] = self.ent_phone.get()
            self.config["login"]["password"] = self.ent_pass.get()
            self.config["login"]["2fa_key"] = self.ent_2fa.get()
            if "ui" not in self.config: self.config["ui"] = {}
            self.config["ui"]["proxy"] = self.ent_proxy.get()
            self.config["ui"]["sheet_url"] = self.ent_sheet.get()
            if "api" not in self.config: self.config["api"] = {}
            self.config["api"]["football_api_key"] = self.ent_api_key.get()
            
            # Cập nhật từ bet_panel
            self.config.update(self.bet_panel.get_settings())
            
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            self._log("💾 Đã lưu cấu hình thành công!", "SUCCESS")
        except Exception as e:
            self._log(f"❌ Lỗi lưu cấu hình: {e}", "ERROR")

    def _log(self, message, level="INFO"):
        self.after(0, lambda m=message, l=level: self.log_panel.add_log(m, l))

    def _start_login(self):
        """Kích hoạt luồng đăng nhập"""
        self.btn_login.configure(text="ĐANG ĐĂNG NHẬP...", state="disabled", fg_color="#555")
        threading.Thread(target=self._login_thread, daemon=True).start()

    def _login_thread(self):
        """Luồng đăng nhập game (độc lập với Auto)"""
        try:
            proxy = self.ent_proxy.get()
            self.browser = BrowserController(proxy=proxy if proxy else None, log_callback=self._log)
            if not self.browser.start():
                self.after(0, lambda: self.btn_login.configure(text="1. ĐĂNG NHẬP GAME", state="normal", fg_color="#007bff"))
                return
            
            self.session = SessionManager(self.browser, log_callback=self._log)
            
            if self.session.login_with_password(self.ent_phone.get(), self.ent_pass.get(), self.ent_2fa.get()):
                self._log("🎉 Đã hoàn tất đăng nhập. Bạn có thể Bắt Đầu Auto!", "SUCCESS")
                # Đăng nhập thành công -> Cập nhật nút UI
                self.after(0, self._on_login_success)
            else:
                self.browser.stop()
                self.after(0, lambda: self.btn_login.configure(text="1. ĐĂNG NHẬP GAME", state="normal", fg_color="#007bff"))
        except Exception as e:
            self._log(f"💥 Lỗi luồng đăng nhập: {str(e)}", "ERROR")
            if self.browser: self.browser.stop()
            self.after(0, lambda: self.btn_login.configure(text="1. ĐĂNG NHẬP GAME", state="normal", fg_color="#007bff"))

    def _start_manual_login(self):
        """Mở trình duyệt để người dùng tự gõ tay"""
        self.btn_login.configure(state="disabled", fg_color="#555")
        threading.Thread(target=self._manual_login_thread, daemon=True).start()

    def _manual_login_thread(self):
        try:
            proxy = self.ent_proxy.get()
            self.browser = BrowserController(proxy=proxy if proxy else None, log_callback=self._log)
            if not self.browser.start():
                self.after(0, lambda: self.btn_login.configure(state="normal", fg_color="#17a2b8"))
                return
            
            self.session = SessionManager(self.browser, log_callback=self._log)
            self._log("🌐 Đã mở trình duyệt. Vui lòng thao tác đăng nhập thủ công, sau đó bấm 'KIỂM TRA ĐN'.", "INFO")
            self.browser.navigate("https://bcvn2.com/vi")
            
            self.after(0, lambda: getattr(self, 'btn_check_login', None) and self.btn_check_login.configure(state="normal"))
        except Exception as e:
            self._log(f"💥 Lỗi mở trình duyệt thủ công: {str(e)}", "ERROR")
            self.after(0, lambda: self.btn_login.configure(state="normal", fg_color="#17a2b8"))

    def _check_manual_login(self):
        """Kiểm tra xem người dùng đã đăng nhập tay thành công chưa"""
        if not self.session or not self.browser:
            self._log("⚠️ Trình duyệt chưa được mở!", "WARNING")
            return
            
        if self.session._check_logged_in():
            self._log("🎉 Nhận diện đăng nhập thủ công thành công. Bạn có thể Bắt Đầu Auto!", "SUCCESS")
            self.session.is_logged_in = True
            self.session.save_cookies()
            self._on_login_success()
        else:
            self._log("⚠️ Chưa phát hiện trạng thái đăng nhập. Vui lòng đăng nhập xong rồi thử lại!", "WARNING")

    def _on_login_success(self):
        """Cập nhật UI khi đăng nhập thành công"""
        self.btn_login.configure(text="✅ ĐÃ ĐĂNG NHẬP", state="disabled", fg_color="#28a745")
        if hasattr(self, 'btn_check_login'):
            self.btn_check_login.configure(state="disabled")

    def _start_auto_bet(self):
        if self.is_running:
            self._log("⚠️ Đang có tiến trình chạy. Bấm DỪNG trước.", "WARNING")
            return
        self.is_running = True
        self.btn_auto_bet.configure(text="ĐANG CHẠY...", state="disabled", fg_color="#555")
        if hasattr(self, 'btn_stop'): self.btn_stop.configure(state="normal")
        threading.Thread(target=self._run_auto_bet, daemon=True).start()

    def _start_auto_care(self):
        if self.is_running:
            self._log("⚠️ Đang có tiến trình chạy. Bấm DỪNG trước.", "WARNING")
            return
        self.is_running = True
        self.btn_auto_care.configure(text="ĐANG CHẠY...", state="disabled", fg_color="#555")
        if hasattr(self, 'btn_stop'): self.btn_stop.configure(state="normal")
        threading.Thread(target=self._run_auto_care, daemon=True).start()

    def _start_auto_report(self):
        if self.is_running:
            self._log("⚠️ Đang có tiến trình chạy. Bấm DỪNG trước.", "WARNING")
            return
        self.is_running = True
        self.btn_auto_report.configure(text="ĐANG CHẠY...", state="disabled", fg_color="#555")
        if hasattr(self, 'btn_stop'): self.btn_stop.configure(state="normal")
        threading.Thread(target=self._run_auto_report, daemon=True).start()

    def _stop_execution(self):
        """Dừng luồng Auto Betting (Nhưng giữ trình duyệt)"""
        self.is_running = False
        self._log("🛑 Đã gửi lệnh dừng hệ thống Auto...", "WARNING")
        
        # Cập nhật nút
        self.btn_auto_bet.configure(text="2. AUTO ĐẶT CƯỢC", state="normal", fg_color="#28a745")
        self.btn_auto_care.configure(text="3. AUTO CARE KẾT QUẢ", state="normal", fg_color="#ffc107")
        self.btn_auto_report.configure(text="4. AUTO ĐIỀN BÁO CÁO", state="normal", fg_color="#6f42c1")
        if hasattr(self, 'btn_stop'): self.btn_stop.configure(state="disabled")

    def _run_auto_bet(self):
        self._log("🚀 Đã khởi động AUTO ĐẶT CƯỢC", "INFO")
        try:
            if not getattr(self, 'browser', None):
                self._log("⚠️ Trình duyệt chưa mở. Vui lòng bấm 1. ĐĂNG NHẬP trước.", "ERROR")
                return

            self.scraper_bc = BCGameScraper(self.browser, log_callback=self._log)
            self.scraper_wap = WapScraper(browser=self.browser, log_callback=self._log)
            self.selector = MatchSelector()
            self.bettor = BettingEngine(self.browser, self.scraper_bc, self.config, log_callback=self._log, stats_callback=self.stats_panel.update_stats)
            self.reporter = GoogleSheetsReporter(spreadsheet_url=self.ent_sheet.get())
            
            while self.is_running:
                # Lấy cài đặt hiện tại từ UI
                settings = self.bet_panel.get_settings()
                sel_config = settings.get("selection", {})
                
                all_tai_matches = []
                if sel_config.get("mode") == "manual":
                    manual_name = sel_config.get("manual_name", "").strip()
                    if not manual_name:
                        self._log("⚠️ Bạn chọn chế độ thủ công nhưng chưa điền tên trận!", "ERROR")
                        time.sleep(5)
                        continue
                        
                    # Phân tách tên đội
                    if " vs " in manual_name.lower():
                        parts = re.split(r" vs ", manual_name, flags=re.IGNORECASE)
                        home, away = parts[0].strip(), parts[1].strip()
                    else:
                        home, away = manual_name, ""
                        
                    all_tai_matches = [{
                        'home': home,
                        'away': away,
                        'raw_line': manual_name,
                        'time': datetime.now().strftime("%H:%M")
                    }]
                    self._log(f"📝 Chế độ THỦ CÔNG: Đang tìm trận '{manual_name}'...")
                else:
                    # Chế độ Auto Wap.vn
                    all_tai_matches = self.scraper_wap.get_tai_matches()
                    
                if not all_tai_matches:
                    self._log("😴 Không tìm thấy trận nào để xử lý. Nghỉ 5 phút...", "WARNING")
                    time.sleep(300)
                    continue
                
                excluded_matches = []
                bet_placed = False
                
                while self.is_running:
                    available = [m for m in all_tai_matches if m['raw_line'] not in excluded_matches]
                    if not available: break
                    
                    selected_match = random.choice(available)
                    self._log(f"🎲 Chọn trận: {selected_match['home']} vs {selected_match['away']}")
                    # BƯỚC 1: Bấm vào nút 'Xem' để check status thực tế (Ưu tiên hàng đầu)
                    detail_url = selected_match.get('detail_url')
                    if detail_url:
                        self._log(f"🔎 Đang check trang chi tiết Wap: {detail_url}")
                        is_upcoming = self.scraper_wap.check_match_status(
                            detail_url, time_str=selected_match.get('time_str')
                        )
                    else:
                        is_upcoming = True  # manual mode: không có Wap link, cho qua
                    if not is_upcoming:
                        self._log(f"🚫 Trận {selected_match['home']} đã bắt đầu hoặc kết thúc (Check Wap Detail). Bỏ qua.", "WARNING")
                        excluded_matches.append(selected_match['raw_line'])
                        continue
                    
                    self._log(f"🎲 Trận {selected_match['home']} hợp lệ (Chưa đá). Tiến hành tìm trên BCGame...")

                    # BƯỚC 2: Tìm trên BCGame
                    bc_matches = self.scraper_bc.search_match(selected_match['home'], selected_match['away'])
                    
                    # Debug: in ra tên đội BCGame để so sánh
                    if bc_matches:
                        bc_names = " | ".join([f"'{b.home_team} vs {b.away_team}'" for b in bc_matches[:5]])
                        self._log(f"📋 BCGame tên trận (5 đầu): {bc_names}", "DEBUG")
                    
                    best_match = None
                    for b in bc_matches:
                        if self.selector.is_match_similar(selected_match['home'], selected_match['away'], b.home_team, b.away_team):
                            self._log(f"🔎 Kiểm tra trận: {b.home_team} vs {b.away_team} | Status: [{b.status}]")
                            best_match = b
                            break
                    
                    if not best_match:
                        self._log(f"⚠️ Không tìm thấy trận phù hợp. Wap: '{selected_match['home']} vs {selected_match['away']}'", "WARNING")
                        excluded_matches.append(selected_match['raw_line'])
                        continue

                        
                    # 1. Dọn dẹp phiếu cược cũ
                    self.bettor.clear_bet_slip()

                    
                    # 2. Tìm và Click kèo (Lọc khắt khe: Chỉ 0.5 và Odds 1.04 - 1.20)
                    over_odds = self.scraper_bc.get_over_odds(best_match)
                    
                    best_odd = None
                    for o in over_odds:
                        # Kiểm tra xem có phải CHÍNH XÁC là kèo 0.5 không (tránh 1.5, 2.5)
                        if re.search(r'(?<!\d)0\.5(?!\d)', o['market']):
                            try:
                                odds_val = float(o['odds'])
                                if 1.04 <= odds_val <= 1.20:
                                    best_odd = o
                                    break
                                else:
                                    self._log(f"ℹ️ Tìm thấy kèo 0.5 nhưng Odds {odds_val} nằm ngoài khoảng [1.04 - 1.20]. Bỏ qua.", "INFO")
                            except Exception: continue
                    
                    if not best_odd:
                        self._log("⚠️ Không có kèo Tài 0.5 thỏa mãn điều kiện (Odds 1.04-1.20). Bỏ qua.", "WARNING")
                        excluded_matches.append(selected_match['raw_line'])
                        self._save_skipped_match(selected_match)
                        continue

                    
                    if not getattr(self, 'session', None):
                        self._log("⚠️ Bạn chưa đăng nhập session game!", "WARNING")
                        return

                    balance = self.session.get_balance()

                    if balance <= 0:
                        self._log("⚠️ Số dư bằng 0 hoặc không đọc được. Bỏ qua trận này.", "ERROR")
                        excluded_matches.append(selected_match['raw_line'])
                        continue

                    bet_cfg = settings.get("betting", {})
                    if bet_cfg.get("mode") == "fixed":
                        bet_amount = bet_cfg.get("fixed_amount", 0)
                        if bet_amount > balance:
                            self._log(f"⚠️ Số tiền cược {bet_amount} lớn hơn số dư {balance}. Chuyển sang All-in!", "WARNING")
                            bet_amount = balance
                        self._log(f"💰 Chế độ: TỰ NHẬP TIỀN. Số tiền: {bet_amount}")
                    else:
                        bet_amount = balance
                        self._log(f"💰 Chế độ: ALL-IN. Số dư hợp lệ: {balance}")
                    
                    if bet_amount <= 0:
                        self._log(f"⚠️ Số tiền cược không hợp lệ ({bet_amount}). Bỏ qua trận này.", "WARNING")
                        excluded_matches.append(selected_match['raw_line'])
                        continue

                    
                    self._log(f"💰 Tiến hành đặt cược {int(bet_amount)} VND vào {best_odd['market']} @ {best_odd['odds']}")
                    
                    # Kiểm tra xem kèo đã được click chưa (từ scraper)
                    click_ok = best_odd.get('_js_click_done', False)
                    
                    if not click_ok:
                        # Fallback nếu scraper chưa click
                        js_clicker = best_odd.get('_js_clicker')
                        if js_clicker:
                            result = self.browser.driver.execute_script(js_clicker)
                            click_ok = result and result.get('clicked')
                        elif best_odd.get('element'):
                            click_ok = self.browser.click_element(best_odd['element'], use_js=True)
                    
                    if not click_ok:
                        self._log("❌ Không thể click kèo. Bỏ qua.", "ERROR")
                        excluded_matches.append(selected_match['raw_line'])
                        continue
                    
                    # 3. Điền tiền và xác nhận
                    record = self.bettor.place_bet(best_match, "over", bet_amount, "All-in Over 0.5")

                    
                    if record:
                        self._log("🚀 Cược thành công! Hãy bật AUTO CARE KẾT QUẢ.", "SUCCESS")
                        self.after(0, lambda: self.tabview.set("2. THEO DÕI KẾT QUẢ"))
                        
                        report_data = {
                            'match': f"{best_match.home_team} vs {best_match.away_team}",
                            'capital': balance,
                            'stake': bet_amount,
                            'odds': best_odd['odds']
                        }
                        self.reporter.add_bet_report(report_data)
                        _msg = f"[{datetime.now().strftime('%H:%M')}] Đã ghi báo cáo PENDING cho {report_data['match']}\n"
                        self.after(0, lambda m=_msg: self.report_list.insert("end", m))

                        self.pending_match = best_match
                        self.pending_report = report_data
                        self.pending_odd = best_odd
                        self.pending_balance = balance
                        self.pending_bet_amount = bet_amount
                        bet_placed = True
                        break
                    else:
                        excluded_matches.append(selected_match['raw_line'])
                
                if bet_placed:
                    break
                else:
                    self._log("⏳ Chưa tìm được kèo ngon, nghỉ 60s quét lại...", "INFO")
                    time.sleep(60)
                
        except Exception as e:
            self._log(f"💥 Lỗi Auto Đặt Cược: {str(e)}", "ERROR")
        finally:
            self.is_running = False
            self.after(0, self._stop_execution)

    def _run_auto_care(self):
        self._log("🔍 Đã khởi động AUTO CARE KẾT QUẢ", "INFO")
        try:
            if not getattr(self, 'browser', None):
                self._log("⚠️ Trình duyệt chưa mở.", "ERROR")
                return

            if not getattr(self, 'pending_match', None):
                self._log("⚠️ Không có trận nào đang chờ. Bạn cần ĐẶT CƯỢC trước.", "WARNING")
                return
            if not getattr(self, 'pending_report', None):
                self._log("⚠️ Chưa có dữ liệu báo cáo. Bạn cần ĐẶT CƯỢC trước.", "WARNING")
                return

            from core.auditor import CombinedAuditor
            self.auditor = CombinedAuditor(self.browser)

            best_match = self.pending_match
            report_data = self.pending_report
            
            _care_msg = f"[{datetime.now().strftime('%H:%M')}] Đang theo dõi: {report_data['match']}\n"
            self.after(0, lambda m=_care_msg: self.care_list.insert("end", m))

            while self.is_running:
                status, h_score, a_score = self.auditor.check_result(best_match.home_team, best_match.away_team)
                _live_txt = f"LIVE: {best_match.home_team} {h_score}-{a_score} {best_match.away_team}"
                self.after(0, lambda t=_live_txt: self.lbl_care_info.configure(text=t))

                won = None
                if (h_score + a_score) > 0:
                    won = True
                    self._log(f"🎉 CÓ BÀN THẮNG! {h_score}-{a_score}. THẮNG CƯỢC!", "SUCCESS")
                elif status == "FIN":
                    won = False
                    self._log("🏁 Kết thúc 0-0. THUA CƯỢC.", "ERROR")

                if won is not None:
                    self.pending_won = won
                    self._log("✅ Care xong! Hãy bật AUTO BÁO CÁO.", "SUCCESS")
                    self.after(0, lambda: self.tabview.set("3. BÁO CÁO"))
                    break
                
                self._log("⏳ Chưa có kết quả, chờ 5 phút check lại...", "INFO")
                for _ in range(30):
                    if not self.is_running: break
                    time.sleep(10)
                
        except Exception as e:
            self._log(f"💥 Lỗi Auto Care: {str(e)}", "ERROR")
        finally:
            self.is_running = False
            self.after(0, self._stop_execution)

    def _run_auto_report(self):
        self._log("📝 Đã khởi động AUTO BÁO CÁO", "INFO")
        try:
            self.reporter = GoogleSheetsReporter(spreadsheet_url=self.ent_sheet.get())
            
            if (not getattr(self, 'pending_report', None)
                    or getattr(self, 'pending_won', None) is None
                    or getattr(self, 'pending_odd', None) is None
                    or getattr(self, 'pending_balance', None) is None):
                self._log("⚠️ Chưa có kết quả hoàn tất để báo cáo.", "WARNING")
                return
                
            report_data = self.pending_report
            won = self.pending_won
            best_odd = self.pending_odd
            balance = self.pending_balance
            bet_amount = getattr(self, 'pending_bet_amount', None) or balance

            self.reporter.finalize_report(report_data['match'], won, best_odd['odds'], bet_amount)
            res_str = "THẮNG" if won else "THUA"
            _rep_msg = f"[{datetime.now().strftime('%H:%M')}] HOÀN TẤT: {report_data['match']} -> {res_str}\n"
            self.after(0, lambda m=_rep_msg: self.report_list.insert("end", m))

            new_balance = (balance - bet_amount) + bet_amount * best_odd['odds'] if won else balance - bet_amount
            _nb = new_balance
            self.after(0, lambda b=_nb: self.stats_panel.update_stats({"balance": b}))

            self.pending_match = None
            self.pending_report = None
            self.pending_odd = None
            self.pending_balance = None
            self.pending_won = None
            self.pending_bet_amount = None
            
            self._log("✅ Báo cáo xong! Bạn có thể quay lại 1. ĐẶT CƯỢC để bắt đầu vòng mới.", "SUCCESS")
                
        except Exception as e:
            self._log(f"💥 Lỗi Auto Báo Cáo: {str(e)}", "ERROR")
        finally:
            self.is_running = False
            self.after(0, self._stop_execution)

    def _run_loop(self):
        """Thuật toán chính: Wap -> Random Choice -> BCGame All-in -> Auditor"""
        try:
            # Khởi tạo các Modules cần thiết (không cần init Browser/Session nữa)
            sheet_url = self.ent_sheet.get()
            
            self.scraper_bc = BCGameScraper(self.browser, log_callback=self._log)
            self.scraper_wap = WapScraper(browser=self.browser, log_callback=self._log)
            self.selector = MatchSelector()
            self.bettor = BettingEngine(self.browser, self.scraper_bc, self.config, log_callback=self._log, stats_callback=self.stats_panel.update_stats)
            self.reporter = GoogleSheetsReporter(spreadsheet_url=sheet_url)
            from core.auditor import CombinedAuditor
            self.auditor = CombinedAuditor(self.browser)

            
            while self.is_running:
                # BƯỚC 1: Quét Wap.vn lấy danh sách TÀI
                all_tai_matches = self.scraper_wap.get_tai_matches()
                if not all_tai_matches:
                    self._log("😴 Không tìm thấy trận TÀI nào. Nghỉ 10 phút...", "WARNING")
                    time.sleep(600)
                    continue
                
                excluded_matches = []
                
                while self.is_running:
                    available = [m for m in all_tai_matches if m['raw_line'] not in excluded_matches]
                    if not available: break
                    
                    selected_match = random.choice(available)
                    self._log(f"🎲 Chọn trận: {selected_match['home']} vs {selected_match['away']}")
                    _t = f"TRẬN CHỌN: {selected_match['home']} vs {selected_match['away']}"
                    self.after(0, lambda t=_t: self.lbl_match_info.configure(text=t))
                    
                    # Tìm trên BCGame
                    bc_matches = self.scraper_bc.search_match(selected_match['home'], selected_match['away'])
                    best_match = next((b for b in bc_matches if self.selector.is_match_similar(selected_match['home'], selected_match['away'], b.home_team, b.away_team)), None)
                    
                    if not best_match:
                        excluded_matches.append(selected_match['raw_line'])
                        continue
                    
                    # Lấy kèo Tài 0.5
                    over_odds = self.scraper_bc.get_over_odds(best_match)
                    best_odd = next((o for o in over_odds if "0.5" in o['market']), None)
                    
                    if not best_odd:
                        self._log("⚠️ Không có kèo Tài 0.5. Bỏ qua.", "WARNING")
                        excluded_matches.append(selected_match['raw_line'])
                        self._save_skipped_match(selected_match)
                        continue
                    
                    # Đặt cược All-in
                    balance = self.session.get_balance()
                    if balance < 1000: # Ngưỡng tối thiểu VND (giả định)
                        self._log(f"❌ Số dư {balance} quá thấp để All-in. Dừng.", "ERROR")
                        self.is_running = False
                        break
                    
                    self._log(f"💰 ALL-IN {balance} VND vào {best_odd['market']} @ {best_odd['odds']}")
                    if not best_odd.get('_js_click_done') and best_odd.get('element'):
                        self.browser.click_element(best_odd['element'])
                    time.sleep(1)
                    
                    record = self.bettor.place_bet(best_match, "over", balance, "All-in Over 0.5")
                    
                    if record:
                        self._log("🚀 Cược thành công! Chuyển sang Tab THEO DÕI.", "SUCCESS")
                        self.after(0, lambda: self.tabview.set("2. THEO DÕI KẾT QUẢ"))

                        # Báo cáo bước đầu
                        report_data = {
                            'match': f"{best_match.home_team} vs {best_match.away_team}",
                            'capital': balance,
                            'stake': balance,
                            'odds': best_odd['odds']
                        }
                        self.reporter.add_bet_report(report_data)
                        _m1 = f"[{datetime.now().strftime('%H:%M')}] Đã ghi báo cáo PENDING cho {report_data['match']}\n"
                        self.after(0, lambda m=_m1: self.report_list.insert("end", m))

                        # BƯỚC 6: Care kết quả (Google Search)
                        won = False
                        _m2 = f"[{datetime.now().strftime('%H:%M')}] Đang theo dõi: {report_data['match']}\n"
                        self.after(0, lambda m=_m2: self.care_list.insert("end", m))
                        
                        while self.is_running:
                            time.sleep(300) # Check mỗi 5 phút
                            status, h_score, a_score = self.auditor.check_result(best_match.home_team, best_match.away_team)
                            _lt = f"LIVE: {best_match.home_team} {h_score}-{a_score} {best_match.away_team}"
                            self.after(0, lambda t=_lt: self.lbl_care_info.configure(text=t))

                            if (h_score + a_score) > 0:
                                won = True
                                self._log(f"🎉 CÓ BÀN THẮNG! {h_score}-{a_score}. THẮNG CƯỢC!", "SUCCESS")
                                break

                            if status == "FIN":
                                won = False
                                self._log("🏁 Kết thúc 0-0. THUA CƯỢC.", "ERROR")
                                break

                        # BƯỚC 7: Làm báo cáo hoàn tất
                        self.after(0, lambda: self.tabview.set("3. BÁO CÁO"))
                        self.reporter.finalize_report(report_data['match'], won, best_odd['odds'], balance)
                        res_str = "THẮNG" if won else "THUA"
                        _rm = f"[{datetime.now().strftime('%H:%M')}] HOÀN TẤT: {report_data['match']} -> {res_str}\n"
                        self.after(0, lambda m=_rm: self.report_list.insert("end", m))

                        # Cập nhật số dư mới sau thắng/thua
                        new_balance = balance * best_odd['odds'] if won else 0
                        self.after(0, lambda b=new_balance: self.stats_panel.update_stats({"balance": b}))
                        
                        if not won:
                            self._log("💀 Cháy tài khoản All-in. Dừng tool.", "ERROR")
                            self.is_running = False
                            break
                        
                        break # Tìm trận mới cho vòng cược tiếp theo
                    else:
                        excluded_matches.append(selected_match['raw_line'])
                
                time.sleep(60) # Nghỉ trước khi quét Wap.vn vòng mới
                
        except Exception as e:
            self._log(f"💥 Lỗi hệ thống: {str(e)}", "ERROR")
            logger.exception(e)
        finally:
            self.is_running = False
            self.after(0, self._stop_execution)

    def _save_skipped_match(self, match_data: dict):
        """Lưu các trận đấu bị loại bỏ vì không có kèo 0.5 vào JSON database"""
        try:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "skipped_matches.json")
            skipped = []
            if os.path.exists(db_path):
                with open(db_path, "r", encoding="utf-8") as f:
                    skipped = json.load(f)
            
            # Tránh trùng lặp
            if not any(s.get('raw_line') == match_data['raw_line'] for s in skipped):
                match_data['skipped_at'] = datetime.now().isoformat()
                match_data['reason'] = "No Over 0.5 market found"
                skipped.append(match_data)
                
                with open(db_path, "w", encoding="utf-8") as f:
                    json.dump(skipped, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self._log(f"⚠️ Lỗi lưu database trận bị loại: {e}")

    def run(self):
        self.mainloop()
