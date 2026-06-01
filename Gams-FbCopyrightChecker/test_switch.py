import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.fb_login import build_driver, login
from modules.copyright_checker import switch_context_via_menu
from modules.config_loader import CONFIG

def test_switch():
    driver = build_driver()
    try:
        ok = login(driver)
        if not ok:
            print("Login failed")
            return
            
        print("Login OK. Testing context switch...")
        # Lấy thử fanpages từ db hoặc config
        fanpages = CONFIG.get("facebook", {}).get("fanpages", [])
        if not fanpages:
            from modules.account_manager import get_manager
            mgr = get_manager()
            if mgr.accounts:
                fanpages = mgr.accounts[0].get("fanpages", [])
        
        if not fanpages:
            print("No fanpages to switch to.")
            return
            
        # Thử switch tới page đầu tiên
        target_name = fanpages[0].get("name")
        if target_name:
            print(f"Attempting to switch to {target_name}...")
            switch_ok = switch_context_via_menu(driver, target_name)
            print(f"Switch to {target_name}: {switch_ok}")
            
    except Exception as e:
        print("Exception:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    test_switch()
