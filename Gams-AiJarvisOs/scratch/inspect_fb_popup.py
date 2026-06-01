import sys
import os
import time

# Ensure we can load from plugins/lib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugins", "lib"))
from gams_utils import BrowserManager

def inspect():
    portable_path = os.getenv("CHROME_PORTABLE_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    if not os.path.exists(portable_path):
        paths = [
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        for p in paths:
            if os.path.exists(p):
                portable_path = p
                break
                
    print(f"Using Chrome path: {portable_path}")
    bm = BrowserManager(portable_path)
    
    # Target URL for "Đỡ phải hóng 24/7"
    url = "https://business.facebook.com/latest/insights/overview?global_scope_id=1016985112612772&business_id=1016985112612772&page_id=243738568828870&asset_id=243738568828870"
    print(f"Navigating to: {url}")
    
    try:
        bm.launch_browser()
        bm.driver.get(url)
        print("Waiting for page load...")
        time.sleep(10)
        
        # Implement popup dismissal inside the browser manager to test
        # 1. Dismiss popups
        script_dismiss = r"""
        try {
            const popups = Array.from(document.querySelectorAll('[role="dialog"], .role-dialog, [role="alertdialog"], .modal, .dialog'));
            const closeSelectors = [
                '[aria-label="Close"]', '[aria-label="Đóng"]', '[aria-label="Dismiss"]',
                'button[type="button"]', 'div[role="button"]'
            ];
            let closed = false;
            for (let popup of popups) {
                const buttons = Array.from(popup.querySelectorAll('button, div[role="button"], span[role="button"]'));
                for (let btn of buttons) {
                    const text = (btn.innerText || "").trim().toLowerCase();
                    if (["đóng", "close", "hủy", "cancel", "bỏ qua", "skip", "dismiss", "x", "ok", "đã hiểu", "got it"].includes(text)) {
                        btn.click();
                        closed = true;
                        break;
                    }
                }
                if (!closed) {
                    const xBtns = Array.from(popup.querySelectorAll('[aria-label*="Close" i], [aria-label*="Đóng" i], [aria-label*="Dismiss" i], .close-button, .close'));
                    if (xBtns.length > 0) {
                        xBtns[0].click();
                        closed = true;
                    }
                }
            }
            if (!closed) {
                const globalCloseTexts = ["đóng", "close", "bỏ qua", "skip", "đã hiểu", "got it", "not now", "lúc khác"];
                const allButtons = Array.from(document.querySelectorAll('button, [role="button"]'));
                for (let btn of allButtons) {
                    const text = (btn.innerText || "").trim().toLowerCase();
                    if (globalCloseTexts.includes(text) && btn.offsetWidth > 0 && btn.offsetHeight > 0) {
                        btn.click();
                        closed = true;
                        break;
                    }
                }
            }
            return closed;
        } catch(e) { return false; }
        """
        closed = bm.driver.execute_script(script_dismiss)
        print(f"Dismiss popups executed. Closed dialog: {closed}")
        if closed:
            time.sleep(3)
            
        # Capture screenshot and text
        os.makedirs(os.path.join(os.getcwd(), "scratch"), exist_ok=True)
        screenshot_path = os.path.abspath(os.path.join(os.getcwd(), "scratch", "fb_popup_screenshot.png"))
        bm.driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        body_text = bm.driver.find_element("tag name", "body").text
        text_path = os.path.abspath(os.path.join(os.getcwd(), "scratch", "fb_popup_body.txt"))
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(body_text)
        print(f"Body text saved to: {text_path}")
        
        print("Page Title:", bm.driver.title)
        
    except Exception as e:
        print(f"Error during inspection: {e}")
    finally:
        bm.close_browser()

if __name__ == "__main__":
    inspect()
