import sys
import os
import time
import subprocess
import shutil

# Kill any existing chrome/chromedriver first and wait 3 seconds
print("Killing Chrome...")
subprocess.run('taskkill /F /IM chrome.exe /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run('taskkill /F /IM chromedriver.exe /T', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.browser import BrowserController

temp_profile = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chrome_profile_temp")
if os.path.exists(temp_profile):
    try:
        shutil.rmtree(temp_profile)
    except Exception:
        pass

class TempBrowserController(BrowserController):
    def start(self) -> bool:
        old_start = super().start
        return old_start()

def main():
    print("Testing query selector without leading slash in href attribute...")
    browser = TempBrowserController(headless=True)
    
    import core.browser
    orig_join = os.path.join
    def custom_join(*args):
        res = orig_join(*args)
        if "chrome_profile_v2" in res:
            res = res.replace("chrome_profile_v2", "chrome_profile_temp")
        return res
    os.path.join = custom_join

    if not browser.start():
        print("Failed to start browser")
        os.path.join = orig_join
        return

    os.path.join = orig_join

    try:
        url = "https://bcvn2.com/vi/sports/soccer-1"
        print(f"Navigating to {url}...")
        browser.navigate(url)
        print("Waiting 15 seconds for page load...")
        time.sleep(15)
        
        # Test query selector using href*="sports/soccer/" (no leading slash) and unconditional recursion
        js_code = """
        function getRowsFixed(root) {
            let results = [];
            // Use sports/soccer/ (no leading slash)
            let rows = root.querySelectorAll('a.bt230, a[href*="sports/soccer/"], [class*="match-item"]');
            for(let i=0; i<rows.length; i++) {
                results.push({
                    tagName: rows[i].tagName,
                    className: rows[i].className,
                    href: rows[i].getAttribute ? rows[i].getAttribute('href') : null,
                    text: (rows[i].innerText || rows[i].textContent || '').substring(0, 100).trim()
                });
            }
            
            let allNodes = root.querySelectorAll('*');
            for (let i = 0; i < allNodes.length; i++) {
                if (allNodes[i].shadowRoot) {
                    results = results.concat(getRowsFixed(allNodes[i].shadowRoot));
                }
            }
            return results;
        }
        
        let results = getRowsFixed(document);
        return {
            count: results.length,
            sample: results.slice(0, 10)
        };
        """
        data = browser.driver.execute_script(js_code)
        print("\n--- RESULTS ---")
        print(f"Selector found: {data['count']} elements")
        for idx, item in enumerate(data['sample']):
            print(f"Event {idx+1}: Tag: {item['tagName']}, Class: {item['className']}, Href: {item['href']} | Text: {item['text']}")

    finally:
        browser.stop()
        time.sleep(2)
        if os.path.exists(temp_profile):
            try:
                shutil.rmtree(temp_profile)
            except Exception:
                pass

if __name__ == "__main__":
    main()
