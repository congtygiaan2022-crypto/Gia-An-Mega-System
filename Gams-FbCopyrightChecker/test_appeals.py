import os
import sys
import time
import logging

logging.basicConfig(level=logging.INFO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.fb_login import build_driver, login
from modules.copyright_checker import switch_context_via_menu, navigate_to_support_inbox
from selenium.webdriver.common.by import By

def test_appeals():
    driver = build_driver()
    try:
        ok = login(driver)
        if not ok:
            print("Login failed")
            return
            
        print("Login OK. Switching to 'Tin Này Trending'...")
        # Switch to Fanpage
        switch_context_via_menu(driver, "Tin Này Trending")
        time.sleep(3)
        
        print("Navigating to Support Inbox via UI...")
        nav_ok = navigate_to_support_inbox(driver)
        if not nav_ok:
            print("UI navigation failed, trying direct URL fallback...")
            driver.get("https://www.facebook.com/support/?tab_type=APPEALS")
        time.sleep(5)
        
        # Dump all text to see what is actually there
        print("Dumping page text...")
        with open("appeals_dump.txt", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
            
        # Try to find items using current xpath
        items = driver.find_elements(By.XPATH, "//div[@role='article'] | //div[contains(@class,'x1qjc9v5')]//div[@data-visualcompletion]")
        print(f"Found {len(items)} items with current XPath.")
        
        for i, item in enumerate(items):
            print(f"--- Item {i} ---")
            print(item.text)
            print("-" * 20)
            
    except Exception as e:
        print("Exception:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    test_appeals()
