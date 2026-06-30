import os
import sys
import time
from datetime import datetime

# Add root folder to PYTHONPATH
sys.path.append(os.getcwd())

from core.browser import BrowserController
from core.bettor import BettingEngine
from core.scraper import BCGameScraper, Match

def run_simulation():
    print("=== STARTING BETTING ENGINE SIMULATION ===")
    
    # 1. Initialize Browser
    browser = BrowserController(headless=True)
    if not browser.start():
        print("Failed to start browser controller")
        return
        
    try:
        # 2. Open local mock html file
        mock_file_path = os.path.abspath("scratch/mock_bcgame.html")
        mock_url = f"file:///{mock_file_path.replace(os.sep, '/')}"
        print(f"Navigating to: {mock_url}")
        browser.navigate(mock_url)
        time.sleep(2)
        
        # 3. Instantiate BettingEngine
        scraper = BCGameScraper(browser)
        engine = BettingEngine(browser, scraper, {})
        
        # 4. Step 1: Clear Bet Slip
        print("\n--- Test Step 1: Clear Bet Slip ---")
        # Check if the bet item exists in HTML before clearing
        html_before = browser.get_page_source()
        has_item_before = "Ma Rốc vs Na Uy" in html_before
        print(f"Has bet item before clearing: {has_item_before}")
        
        # Call clear_bet_slip
        success = engine.clear_bet_slip()
        print(f"clear_bet_slip() returned: {success}")
        
        # Check if the bet item exists in HTML after clearing
        time.sleep(1)
        html_after = browser.get_page_source()
        has_item_after = "Ma Rốc vs Na Uy" in html_after
        print(f"Has bet item after clearing: {has_item_after}")
        
        if not has_item_after and has_item_before:
            print("SUCCESS: clear_bet_slip() successfully cleared the slip!")
        else:
            print("FAILED: clear_bet_slip() failed to clear the slip!")
            
        # 5. Step 2: Place Bet and Set Amount
        print("\n--- Test Step 2: Set Amount and Place Bet ---")
        # Define a mock match
        mock_match = Match(home_team="Greuther Furth", away_team="Essen")
        
        # Get input value before setting
        val_before = browser.driver.execute_script("return document.getElementById('stake-input').value;")
        print(f"Input value before place_bet: '{val_before}'")
        
        # Run place_bet (will set value to 2120)
        # Note: it will click place-bet-btn which is mock
        res = engine.place_bet(mock_match, "over", 2120.0)
        print(f"place_bet() returned: {res}")
        
        # Get input value after setting
        val_after = browser.driver.execute_script("return document.getElementById('stake-input').value;")
        print(f"Input value after place_bet: '{val_after}'")
        
        if val_after == "2120":
            print("SUCCESS: Input value was successfully updated to 2120!")
        else:
            print("FAILED: Input value was NOT updated correctly!")
            
    finally:
        print("\nClosing browser...")
        browser.stop()
        print("=== SIMULATION COMPLETED ===")

if __name__ == "__main__":
    run_simulation()
