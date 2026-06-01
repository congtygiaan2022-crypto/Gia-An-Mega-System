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
    print("Starting HTML structure extraction...")
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
        
        # JS script to find elements containing "Crystal Palace" and print their outerHTML
        # We recursively scan all elements including shadowRoots.
        js_code = """
        function scanShadow(root, target) {
            let elements = root.querySelectorAll('*');
            for (let i = 0; i < elements.length; i++) {
                let el = elements[i];
                if (el.textContent && el.textContent.includes(target)) {
                    // Let's check if it's a leaf node containing the target text
                    let isLeaf = true;
                    for (let j = 0; j < el.children.length; j++) {
                        if (el.children[j].textContent.includes(target)) {
                            isLeaf = false;
                            break;
                        }
                    }
                    
                    if (isLeaf) {
                        // Let's traverse up 5 levels and print their tag, class, outerHTML
                        let trace = [];
                        let p = el;
                        let depth = 0;
                        while (p && depth < 6) {
                            trace.push({
                                tagName: p.tagName,
                                className: p.className || '',
                                outerHTML: p.outerHTML ? p.outerHTML.substring(0, 300) : ''
                            });
                            if (!p.parentElement && p.parentNode && p.parentNode.host) {
                                p = p.parentNode.host;
                            } else {
                                p = p.parentElement;
                            }
                            depth++;
                        }
                        return trace;
                    }
                }
                
                if (el.shadowRoot) {
                    let res = scanShadow(el.shadowRoot, target);
                    if (res) return res;
                }
            }
            return null;
        }
        return scanShadow(document, 'Crystal Palace');
        """
        data = browser.driver.execute_script(js_code)
        if data:
            print("Successfully found Crystal Palace element ancestry:")
            for idx, item in enumerate(data):
                print(f"Level {idx}: <{item['tagName']}> class='{item['className']}'")
                print(f"  Snippet: {item['outerHTML']}")
        else:
            print("Did not find 'Crystal Palace' text anywhere on the page.")

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
