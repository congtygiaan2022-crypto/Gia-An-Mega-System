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

# Delete temp profile if exists, to ensure fresh startup
temp_profile = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "chrome_profile_temp")
if os.path.exists(temp_profile):
    try:
        shutil.rmtree(temp_profile)
        print("Cleaned temporary profile directory.")
    except Exception as e:
        print(f"Could not clean temp profile: {e}")

# Modify BrowserController to use the temp profile
class TempBrowserController(BrowserController):
    def start(self) -> bool:
        old_start = super().start
        return old_start()

def main():
    print("Starting element extraction with shadow DOM traversal...")
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
        
        # JS to recursively traverse shadow DOM, find team name, and trace ancestors
        js_code = """
        function getAncestors(el) {
            let ancestors = [];
            let parent = el;
            while (parent) {
                let info = {
                    tag: parent.tagName,
                    class: parent.className || '',
                    id: parent.id || '',
                    href: parent.getAttribute ? parent.getAttribute('href') : null
                };
                ancestors.push(info);
                // Move to parent element or host of shadow root
                if (!parent.parentElement && parent.parentNode && parent.parentNode.host) {
                    parent = parent.parentNode.host;
                } else {
                    parent = parent.parentElement;
                }
            }
            return ancestors;
        }

        function searchNode(root, targetText) {
            let all = root.querySelectorAll('*');
            for (let i = 0; i < all.length; i++) {
                let el = all[i];
                
                // Check leaf-like elements for text content match
                let text = el.innerText || el.textContent || '';
                if (text.includes(targetText) && el.children.length === 0) {
                    return {
                        element: el,
                        text: text.trim()
                    };
                }
                
                if (el.shadowRoot) {
                    let found = searchNode(el.shadowRoot, targetText);
                    if (found) return found;
                }
            }
            return null;
        }

        let targets = ['Crystal Palace', 'Nacional', 'São Paulo', 'Sao Paulo', 'Saint Etienne', 'Palestino', 'Greuther Furth'];
        for (let targetText of targets) {
            let found = searchNode(document, targetText);
            if (found) {
                let ancestors = getAncestors(found.element);
                return [{
                    matchedTarget: targetText,
                    text: found.text,
                    ancestors: ancestors
                }];
            }
        }
        return [];
        """
        data = browser.driver.execute_script(js_code)
        print(f"Found {len(data)} trace elements.")
        if data:
            trace = data[0]
            print(f"Matched Target: {trace['matchedTarget']}")
            print(f"Element Text: {trace['text']}")
            print("Ancestors (from leaf to root, including shadow hosts):")
            for idx, anc in enumerate(trace['ancestors']):
                print(f"  {idx}: <{anc['tag']}> class='{anc['class']}' id='{anc['id']}' href='{anc['href']}'")
        else:
            print("No matching target team found on the page.")

    finally:
        browser.stop()
        time.sleep(2)
        if os.path.exists(temp_profile):
            try:
                shutil.rmtree(temp_profile)
                print("Temp profile cleaned up successfully.")
            except Exception:
                pass

if __name__ == "__main__":
    main()
