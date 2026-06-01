import sys
import os
import time

# Ensure we can load from plugins/lib
plugin_dir = os.path.join(os.path.dirname(__file__), "..", "plugins")
sys.path.insert(0, os.path.join(plugin_dir, "lib"))

from gams_utils import DataManager, BrowserManager

def test_single():
    data_file = os.path.join(plugin_dir, "data", "gams_insight", "links.json")
    dm = DataManager(data_file)
    links = dm.links
    
    # We want to scrape STT 13 "Đỡ phải hóng 24/7" (index 12 in 0-indexed list)
    target_index = 12
    if len(links) <= target_index:
        print("Error: Target index not found in links.json")
        return
        
    link = links[target_index]
    print(f"Testing scrape for: {link.get('page_name')}")
    print(f"URL: {link.get('url')}")
    
    portable_path = os.getenv("CHROME_PORTABLE_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    bm = BrowserManager(portable_path)
    
    try:
        bm.navigate_to(link.get("url"))
        print("Waiting for page elements to load...")
        time.sleep(8)
        
        # Scroll to load insights
        bm.scroll_page()
        
        # Extract data
        data = bm.extract_insight_data()
        print("Extracted Data:", data)
        
        # Save results back to link
        try:
            post_info = bm.extract_latest_post_date()
            print("Latest post info:", post_info)
        except Exception as pe:
            print("Error checking latest post:", pe)
            post_info = None
            
        dm.update_insight_and_post(target_index, "Xong", data, post_info)
            
        print("Done!")
        
    except Exception as e:
        print("Scrape failed:", e)
    finally:
        bm.close_browser()

if __name__ == "__main__":
    test_single()
