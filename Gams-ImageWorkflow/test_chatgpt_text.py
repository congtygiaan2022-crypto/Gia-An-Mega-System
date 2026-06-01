import time
import sys
import profile_manager
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_text():
    pm = profile_manager.ProfileManager("profiles")
    with sync_playwright() as p:
        context = pm.launch_browser_for_profile(p, "Yui Hatano", headless=False)
        page = context.new_page()

        url = "https://chatgpt.com/c/6a12d2cd-bf7c-83ec-b4b8-8ce17202eacb"
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(10)
        
        try:
            elements = page.locator('[data-message-author-role="assistant"]').all()
            if elements:
                raw_text = elements[-1].inner_text()
                print("RAW TEXT:")
                print(repr(raw_text))
                
                # Check for p tags specifically
                p_texts = elements[-1].locator('p').all_inner_texts()
                print("P TAGS TEXT:")
                print(p_texts)
        except Exception as e:
            print("Lỗi:", e)
        
        context.close()

if __name__ == "__main__":
    test_text()
