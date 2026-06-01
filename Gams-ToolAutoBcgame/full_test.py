import time
import random
from core.browser import BrowserController
from core.scraper_wap import WapScraper
from core.scraper import BCGameScraper
from core.session import SessionManager
from core.bettor import BettingEngine
from core.selector import MatchSelector

def run_full_simulation():
    browser = BrowserController()
    if not browser.start():
        print("Failed to start browser")
        return

    try:
        session = SessionManager(browser)
        # Giả định đã đăng nhập thủ công hoặc dùng cookies
        if not session.login_with_cookies():
            print("Vui lòng đăng nhập thủ công trước hoặc đảm bảo cookies còn hạn.")
            # browser.navigate("https://bcvn2.com/vi")
            # time.sleep(30) # Đợi người dùng đăng nhập nếu cần

        scraper_wap = WapScraper(browser)
        scraper_bc = BCGameScraper(browser)
        selector = MatchSelector()
        bettor = BettingEngine(browser, scraper_bc, {"betting": {"strategy": "all-in"}})
        bettor.is_active = True

        print("\n--- BƯỚC 1: QUÉT WAP.VN ---")
        wap_matches = scraper_wap.get_tai_matches()
        if not wap_matches:
            print("Không tìm thấy trận TÀI nào trên Wap.vn")
            return
        
        print(f"Tìm thấy {len(wap_matches)} trận TÀI.")
        
        print("\n--- BƯỚC 2: CHỌN NGẪU NHIÊN 1 TRẬN ---")
        selected = random.choice(wap_matches)
        print(f"Đã chọn: {selected['home']} vs {selected['away']} ({selected['tx_val']})")

        print("\n--- BƯỚC 3: TÌM KIẾM TRÊN BCGAME ---")
        bc_results = scraper_bc.search_match(selected['home'], selected['away'])
        
        best_match = None
        for bcm in bc_results:
            if selector.is_match_similar(selected['home'], selected['away'], bcm.home_team, bcm.away_team):
                best_match = bcm
                break
        
        if not best_match:
            print(f"Không tìm thấy trận '{selected['home']} vs {selected['away']}' trên BCGame")
            return
        
        print(f"Đã khớp trận: {best_match.home_team} vs {best_match.away_team}")

        print("\n--- BƯỚC 4: CHỌN KÈO TÀI 0.5 ---")
        over_odds = scraper_bc.get_over_odds(best_match)
        
        target_odd = None
        for odd in over_odds:
            if "0.5" in odd['market']:
                target_odd = odd
                break
        
        if not target_odd:
            print("Trận đấu không có kèo Tài 0.5")
            return
        
        print(f"Đã chọn kèo: {target_odd['market']} (Odds: {target_odd['odds']})")

        print("\n--- BƯỚC 5: ĐIỀN TIỀN & BẤM ĐẶT CƯỢC ---")
        balance = session.get_balance()
        print(f"Số dư hiện tại: {balance} VND")

        # Click vào kèo (bỏ qua nếu đã click bằng JS)
        if not target_odd.get('_js_click_done'):
            browser.click_element(target_odd['element'])
            time.sleep(2)
        
        # Thực hiện điền tiền và bấm nút (dùng BettingEngine)
        result = bettor.place_bet(best_match, "over", balance, "Full Simulation Test")
        
        if result:
            print(f"KẾT QUẢ: {result}")
        else:
            print("KẾT QUẢ: Thất bại ở bước điền phiếu hoặc bấm nút.")

    finally:
        time.sleep(5)
        browser.stop()

if __name__ == "__main__":
    run_full_simulation()
