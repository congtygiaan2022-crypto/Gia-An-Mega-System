"""
Bettor - Module B: Engine đặt cược tự động (Thực thi cược)
"""
import time
from datetime import datetime
from typing import Optional, Callable
from loguru import logger

from core.browser import BrowserController
from core.scraper import BCGameScraper, Match
from core.bug_tracker import report_bug

SELENIUM_AVAILABLE = True

class BetRecord:
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.match = ""
        self.bet_type = ""
        self.odds = 0.0
        self.amount = 0.0
        self.status = "pending"
        self.profit = 0.0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "match": self.match,
            "bet_type": self.bet_type,
            "odds": self.odds,
            "amount": self.amount,
            "status": self.status,
            "profit": self.profit
        }

class BettingEngine:
    """Xử lý việc điền phiếu cược và xác nhận cược trên BCGame"""

    def __init__(self, browser: BrowserController, scraper: BCGameScraper,
                 config: dict, log_callback: Optional[Callable] = None,
                 stats_callback: Optional[Callable] = None):
        self.browser = browser
        self.scraper = scraper
        self.config = config
        self.log_callback = log_callback
        self.stats_callback = stats_callback
        self.is_active = False

    def _log(self, message: str, level: str = "INFO"):
        logger.info(message)
        if self.log_callback:
            self.log_callback(message, level)

    def place_bet(self, match: Match, bet_type_name: str, amount: float, strategy: str = "All-in") -> Optional[dict]:
        """
        Thực hiện các bước điền số tiền và bấm xác nhận cược.
        Giả định rằng phần tử kèo đã được click trước đó.
        """
        self._log(f"🚀 Đang xử lý phiếu cược cho trận: {match.home_team} vs {match.away_team}", "INFO")
        try:
            # 1. Tìm các phần tử trong phiếu cược, thử lại 3 lần nếu chưa thấy ngay
            elements = None
            for _ in range(3):
                elements = self._find_bet_elements()
                if elements and elements.get('input'): break
                self._log("⏳ Đang đợi phiếu cược hiện lên...")
                time.sleep(1.5)

            if not elements or not elements.get('input'):
                self._log("⚠️ Không tìm thấy ô nhập tiền trong phiếu cược", "WARNING")
                return None

            amount_input = elements['input']
            
            # 2. Nhập số tiền
            clean_amount = int(round(amount))
            self._log(f"⌨️ Đang nhập số tiền cược: {clean_amount}...")
            
            js_set_amount = f"""
                let input = arguments[0];
                if (input) {{
                    // Highlight để bác thấy Tool đang chọn đúng ô
                    input.style.border = "3px solid red";
                    input.style.backgroundColor = "yellow";
                    
                    input.focus();
                    input.click();
                    
                    // Cách 'Ctrl + A' và 'Paste' cực mạnh:
                    input.select(); // Bôi đen toàn bộ (giống Ctrl + A)
                    document.execCommand('delete'); // Xóa sạch (giống Backspace)
                    
                    // Dùng insertText để giả lập việc 'Gõ/Dán' thật sự vào ô nhập
                    // Cách này React/Vue không bao giờ chặn được
                    document.execCommand('insertText', false, '{clean_amount}');
                    
                    // Kích hoạt thêm sự kiện cho chắc chắn
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    
                    return true;
                }}
                return false;
            """
            self.browser.driver.execute_script(js_set_amount, amount_input)
            self._log(f"✅ Đã nhập số tiền {clean_amount} bằng phương pháp 'Select & Insert'")
            
            time.sleep(2.0) # Đợi UI cập nhật

            
            # 3. Bấm xác nhận cược (Thử tìm nút lại vì UI có thể render lại)
            confirm_btn = None
            for _ in range(3):
                elements = self._find_bet_elements()
                if elements:
                    confirm_btn = elements.get('btn')
                    if confirm_btn: break
                time.sleep(1.0)

            if confirm_btn:
                self._log(f"💰 Bấm xác nhận cược: {clean_amount}", "BET")
                self.browser.driver.execute_script("arguments[0].click();", confirm_btn)
                self._log("✅ Đã bấm nút xác nhận. Đang chờ phản hồi...")
                time.sleep(4)
                
                # 4. Kiểm tra xem có lỗi gì không (Toast notification)
                toast_msg = self._check_toast_error()
                if toast_msg:
                    self._log(f"❌ Đặt cược thất bại! Lý do từ BCGame: {toast_msg}", "ERROR")
                    return None
                    
                self._log("✅ Đặt cược hoàn tất thành công!", "SUCCESS")
                return {"status": "success", "amount": amount, "time": datetime.now().isoformat()}
            else:
                self._log("⚠️ Không tìm thấy nút 'Đặt cược' (Place Bet) sau khi nhập tiền", "WARNING")
                return None


        except Exception as e:
            self._log(f"❌ Lỗi khi thực hiện cược: {str(e)}", "ERROR")
            report_bug(
                exc=e, module="core.bettor", task="place_bet",
                context={"match": f"{match.home_team} vs {match.away_team}",
                         "bet_type": bet_type_name, "amount": amount},
                severity="CRITICAL",
            )
            return None

    def clear_bet_slip(self):
        """Xoá toàn bộ các cược cũ đang có trong phiếu cược để tránh cược xiên"""
        js_clear = """
            function clearAll() {
                let slipHost = document.querySelector('div#betby');
                if (!slipHost) return "Already Empty (No container)";
                
                function findInShadow(root, selector, textFilter) {
                    let results = [];
                    let els = Array.from(root.querySelectorAll(selector));
                    if (textFilter) {
                        els = els.filter(el => (el.innerText || el.textContent || '').toLowerCase().includes(textFilter.toLowerCase()));
                    }
                    results = results.concat(els);
                    let all = root.querySelectorAll('*');
                    for (let el of all) {
                        if (el.shadowRoot) results = results.concat(findInShadow(el.shadowRoot, selector, textFilter));
                    }
                    return results;
                }

                // Kiểm tra xem có kèo nào trong slip không (BCGame thường có class liên quan đến 'bet-item' hoặc 'outcome')
                let items = findInShadow(slipHost, 'div', '');
                let hasBets = items.some(el => {
                    let rect = el.getBoundingClientRect();
                    return rect.width > 100 && (el.innerText || '').length > 5 && (el.innerText || '').includes(' vs ');
                });

                if (!hasBets) return "Already Empty (No bets found)";

                // Chỉ clear nếu có kèo
                let trashBtns = findInShadow(slipHost, 'div, button, svg', 'Xóa tất cả');
                if (trashBtns.length === 0) trashBtns = findInShadow(slipHost, 'div, button, svg', 'Clear all');
                
                if (trashBtns.length > 0) {
                    trashBtns[0].click();
                    return "Cleared All Bets";
                }

                return "Could not clear but bets exist";
            }
            return clearAll();
        """
        try:
            self._log("🧹 Đang dọn dẹp phiếu cược cũ...", "INFO")
            res = self.browser.driver.execute_script(js_clear)
            self._log(f"✅ Kết quả dọn dẹp: {res}")
            time.sleep(1.0) # Đợi UI cập nhật
            return True
        except Exception as e:
            self._log(f"⚠️ Lỗi dọn dẹp phiếu cược: {str(e)}", "DEBUG")
            report_bug(exc=e, module="core.bettor", task="clear_bet_slip",
                       severity="WARNING")
            return False

    def _find_bet_elements(self):
        """Dùng JS nhắm mục tiêu chính xác vào Shadow Host của phiếu cược (div#betby)"""
        js_find_elements = """
            function findInShadow(root, selector, textFilter) {
                let els = Array.from(root.querySelectorAll(selector));
                if (textFilter) {
                    els = els.filter(el => (el.innerText || el.textContent || '').toLowerCase().includes(textFilter.toLowerCase()));
                }
                if (els.length > 0) return els;
                let all = root.querySelectorAll('*');
                for (let el of all) {
                    if (el.shadowRoot) {
                        let res = findInShadow(el.shadowRoot, selector, textFilter);
                        if (res.length > 0) return res;
                    }
                }
                return [];
            }

            function getBetElements() {
                // 1. Chuyển sang tab "Một" (Single) trước để chắc chắn
                let singleTabs = findInShadow(document, 'div, span', 'Một');
                if (singleTabs.length === 0) singleTabs = findInShadow(document, 'div, span', 'Single');
                if (singleTabs.length > 0) {
                    singleTabs[0].click();
                }

                // 2. Tìm ô nhập tiền (Quét kỹ hơn các thuộc tính)
                let inputs = findInShadow(document, 'input[type="number"], input[type="tel"], input[placeholder="0"], input.bt830, [class*="stake"], [name*="amount"], [name*="stake"]', '');
                
                // Lọc bỏ các ô input ẩn hoặc quá nhỏ
                inputs = inputs.filter(el => {
                    let rect = el.getBoundingClientRect();
                    return rect.width > 30 && rect.height > 20;
                });
                
                let input = inputs.length > 0 ? inputs[0] : null;

                // 3. Tìm nút Đặt cược
                let btns = findInShadow(document, 'button', 'Cược');
                if (btns.length === 0) btns = findInShadow(document, 'button', 'Bet');
                if (btns.length === 0) btns = findInShadow(document, 'button', 'Place');
                
                let btn = btns.length > 0 ? btns[0] : null;
                
                return {input, btn};
            }
            return getBetElements();
        """
        try:
            return self.browser.driver.execute_script(js_find_elements)
        except Exception as e:
            self._log(f"⚠️ Lỗi quét phiếu cược JS: {e}", "WARNING")
            return {"input": None, "btn": None}

    def _check_toast_error(self):
        """Kiểm tra có thông báo lỗi nào xuất hiện trên màn hình không (Ví dụ: Số dư không đủ)"""
        js_get_toast = """
            function findToast(root) {
                // BCGame thường dùng snackbar hoặc toast
                let toasts = root.querySelectorAll('.toast, .snackbar, .notification, [class*="toast"]');
                for(let i=0; i<toasts.length; i++) {
                    let text = (toasts[i].innerText || '').trim();
                    if (text.length > 0) return text;
                }
                
                let allNodes = root.querySelectorAll('*');
                for (let i = 0; i < allNodes.length; i++) {
                    if (allNodes[i].shadowRoot) {
                        let t = findToast(allNodes[i].shadowRoot);
                        if (t) return t;
                    }
                }
                return null;
            }
            return findToast(document);
        """
        try:
            return self.browser.driver.execute_script(js_get_toast)
        except Exception:
            return None

    def update_bet_result(self, record, won):
        """Cập nhật kết quả phiên cược (Dummy placeholder for logic compatibility)"""
        pass
