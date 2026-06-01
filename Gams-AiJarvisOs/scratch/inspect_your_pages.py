import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugins", "lib"))
from gams_utils import BrowserManager

def inspect_pages():
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
    
    url = "https://www.facebook.com/pages/?category=your_pages&ref=bookmarks"
    print(f"Navigating to: {url}")
    
    try:
        bm.launch_browser()
        bm.driver.get(url)
        print("Waiting for page load...")
        time.sleep(12)
        
        # Dismiss any popup if present
        bm.dismiss_popups()
        
        # Save screenshot
        os.makedirs(os.path.join(os.getcwd(), "scratch"), exist_ok=True)
        screenshot_path = os.path.abspath(os.path.join(os.getcwd(), "scratch", "fb_pages_screenshot.png"))
        bm.driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Save body text
        body_text = bm.driver.find_element("tag name", "body").text
        text_path = os.path.abspath(os.path.join(os.getcwd(), "scratch", "fb_pages_body.txt"))
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(body_text)
        print(f"Body text saved to: {text_path}")
        
        # Find page names and links
        script_links = """
        try {
            const results = [];
            const links = Array.from(document.querySelectorAll('a'));
            for (let link of links) {
                const href = link.href || "";
                const text = (link.innerText || "").trim();
                if (href && text) {
                    results.push({href, text});
                }
            }
            return results;
        } catch(e) { return []; }
        """
        all_links = bm.driver.execute_script(script_links)
        print(f"Found {len(all_links)} links with text.")
        for l in all_links[:30]:
            print(f"Link: {l['text']} -> {l['href']}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        bm.close_browser()

if __name__ == "__main__":
    inspect_pages()
