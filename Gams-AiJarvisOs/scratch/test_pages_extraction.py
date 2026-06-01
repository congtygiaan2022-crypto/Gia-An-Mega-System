import sys
import os
import time
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugins", "lib"))
from gams_utils import BrowserManager

def test_extraction():
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
        
        bm.dismiss_popups()
        
        # JS Extraction script
        extraction_script = """
        try {
            const pageBlocks = [];
            const profileLinks = Array.from(document.querySelectorAll('a')).filter(a => {
                const href = a.href || "";
                return href.includes('profile.php?id=') && (a.innerText || "").trim().length > 0;
            });

            for (let a of profileLinks) {
                const name = a.innerText.trim();
                let parent = a.parentElement;
                let pageId = "";
                let attempts = 0;
                while (parent && attempts < 8) {
                    const subLinks = Array.from(parent.querySelectorAll('a'));
                    for (let sub of subLinks) {
                        const href = sub.href || "";
                        let match = href.match(/[?&](page_id|asset_id)=(\d+)/);
                        if (match) {
                            pageId = match[2];
                            break;
                        }
                    }
                    if (pageId) break;
                    parent = parent.parentElement;
                    attempts++;
                }
                
                if (name && pageId) {
                    // Avoid duplicates
                    if (!pageBlocks.some(p => p.page_id === pageId)) {
                        pageBlocks.push({ name, page_id: pageId });
                    }
                }
            }
            return pageBlocks;
        } catch(e) {
            return [{error: e.message}];
        }
        """
        
        results = bm.driver.execute_script(extraction_script)
        print(f"Extraction returned {len(results)} items:")
        print(json.dumps(results, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        bm.close_browser()

if __name__ == "__main__":
    test_extraction()
