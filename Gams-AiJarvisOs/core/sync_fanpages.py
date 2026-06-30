import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        try:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass
    except Exception:
        pass

import json
import os
import time
import datetime

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "plugins", "lib"))

from gams_utils import BrowserManager

TARGET_LINKS = os.path.join(PROJECT_ROOT, 'plugins', 'data', 'gams_insight', 'links.json')
BUSINESS_ID = "1016985112612772"

def sync():
    # 1. Start browser
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

    print(f"Using Chrome: {portable_path}")
    bm = BrowserManager(portable_path)
    
    url = "https://www.facebook.com/pages/?category=your_pages&ref=bookmarks"
    print(f"Navigating to: {url}")
    
    browser_pages = []
    try:
        bm.launch_browser()
        bm.driver.get(url)
        time.sleep(10)
        
        bm.dismiss_popups()
        
        # Scroll and load more pages
        print("Scrolling and loading all pages dynamically...")
        last_count = 0
        no_change_rounds = 0
        max_scrolls = 30
        
        # Helper count script
        count_script = """
        try {
            const actionLinks = Array.from(document.querySelectorAll('a')).filter(a => {
                const href = a.href || "";
                return (href.includes('latest/inbox') && href.includes('asset_id=')) || 
                       (href.includes('ad_center') && href.includes('page_id='));
            });
            const ids = new Set();
            actionLinks.forEach(link => {
                let match = link.href.match(/[?&](page_id|asset_id)=(\d+)/);
                if (match) ids.add(match[2]);
            });
            return ids.size;
        } catch(e) { return 0; }
        """
        
        for i in range(max_scrolls):
            # Scroll to bottom
            bm.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2.5)
            
            # Get current count
            current_count = bm.driver.execute_script(count_script)
            print(f"Scroll {i+1}/{max_scrolls}: Found {current_count} pages visible in DOM.")
            
            if current_count > last_count:
                # Count increased, continue scrolling
                no_change_rounds = 0
                last_count = current_count
                time.sleep(1.0)
            else:
                # Count did not increase, try clicking "Tải thêm"
                click_more_script = """
                try {
                    const buttons = Array.from(document.querySelectorAll('div[role="button"], span, button, a'));
                    let clicked = false;
                    for (let btn of buttons) {
                        const text = (btn.innerText || "").trim().toLowerCase();
                        if (text === "tải thêm" || text === "see more" || text === "xem thêm" || text === "xem thêm trang") {
                            btn.click();
                            clicked = true;
                            break;
                        }
                    }
                    return clicked;
                } catch(e) { return false; }
                """
                clicked = bm.driver.execute_script(click_more_script)
                if clicked:
                    print("Clicked 'Tải thêm' button. Waiting 7 seconds for async load...")
                    time.sleep(7.0)
                    # Get count again after wait
                    current_count = bm.driver.execute_script(count_script)
                    print(f"After click load: Found {current_count} pages visible in DOM.")
                    if current_count > last_count:
                        no_change_rounds = 0
                        last_count = current_count
                        continue
                
                # If no click happened, or count still didn't increase
                no_change_rounds += 1
                if no_change_rounds >= 3:
                    print("Page count stabilized and no 'Tải thêm' button clicked. Stopping scroll.")
                    break
              # Extract page names and IDs
        extraction_script = """
        try {
            const pageBlocks = [];
            const actionLinks = Array.from(document.querySelectorAll('a')).filter(a => {
                const href = a.href || "";
                return (href.includes('latest/inbox') && href.includes('asset_id=')) || 
                       (href.includes('ad_center') && href.includes('page_id='));
            });

            actionLinks.forEach(actionLink => {
                const href = actionLink.href;
                let pageId = "";
                let match = href.match(/[?&](page_id|asset_id)=(\d+)/);
                if (match) {
                    pageId = match[2];
                }
                if (!pageId) return;
                
                if (pageBlocks.some(p => p.page_id === pageId)) return;
                
                let parent = actionLink.parentElement;
                let pageName = "";
                let publicUrl = "";
                let attempts = 0;
                while (parent && attempts < 12) {
                    const subLinks = Array.from(parent.querySelectorAll('a'));
                    for (let sub of subLinks) {
                        const subHref = sub.href || "";
                        const subText = (sub.innerText || "").trim();
                        if (subText.length > 0 && 
                            !subHref.includes('latest/inbox') && 
                            !subHref.includes('ad_center') && 
                            !subHref.includes('business.facebook.com') && 
                            !subHref.includes('pages/?category') &&
                            !["tin nhắn", "quảng cáo", "inbox", "message", "messages", "ads", "ad", "tạo quảng cáo"].includes(subText.toLowerCase())) {
                            
                            pageName = subText;
                            if (subHref) {
                                try {
                                    const u = new URL(subHref);
                                    if (u.pathname === "/profile.php") {
                                        const idVal = u.searchParams.get("id");
                                        publicUrl = u.origin + u.pathname + "?id=" + idVal;
                                    } else {
                                        publicUrl = u.origin + u.pathname;
                                    }
                                } catch(err) {
                                    publicUrl = subHref;
                                }
                            }
                            break;
                        }
                    }
                    if (pageName && pageId) break;
                    parent = parent.parentElement;
                    attempts++;
                }
                
                if (pageName && pageId) {
                    pageBlocks.push({ name: pageName, page_id: pageId, public_url: publicUrl });
                }
            });
            return pageBlocks;
        } catch(e) {
            return [];
        }
        """
        browser_pages = bm.driver.execute_script(extraction_script)
        print(f"Extracted {len(browser_pages)} pages from browser.")
        
    except Exception as e:
        print(f"Error during browser sync: {e}")
    finally:
        bm.close_browser()
        
    if not browser_pages:
        print("No pages extracted from browser. Sync aborted to prevent data loss.")
        return
 
    # 2. Load existing links.json
    existing_links = []
    if os.path.exists(TARGET_LINKS):
        try:
            with open(TARGET_LINKS, "r", encoding="utf-8") as f:
                existing_links = json.load(f)
        except Exception as e:
            print(f"Error loading existing links: {e}")
            existing_links = []
            
    existing_map = {item.get("page_id"): item for item in existing_links if item.get("page_id")}
    
    # 3. Merge and update
    new_links = []
    
    # Process browser extracted pages
    for bp in browser_pages:
        name = bp["name"]
        page_id = bp["page_id"]
        public_url = bp.get("public_url", "")
        target_url = f"https://business.facebook.com/latest/insights/overview/?business_id={BUSINESS_ID}&asset_id={page_id}"
        
        entry = {
            "stt": len(new_links) + 1,
            "page_name": name,
            "page_id": page_id,
            "url": target_url,
            "public_url": public_url,
            "status": "Chưa chạy"
        }
        
        if page_id in existing_map:
            old = existing_map[page_id]
            entry["status"] = old.get("status", "Chưa chạy")
            entry["data"] = old.get("data", {})
            entry["total_followers"] = old.get("total_followers", "")
            entry["latest_post_date"] = old.get("latest_post_date", "")
            entry["latest_post_title"] = old.get("latest_post_title", "")
            if "last_scanned" in old:
                entry["last_scanned"] = old["last_scanned"]
            if "public_url" not in entry or not entry["public_url"]:
                entry["public_url"] = old.get("public_url", "")
                
        new_links.append(entry)
        
    # Append existing pages that weren't found in browser list (to prevent loss of pages)
    browser_page_ids = {bp["page_id"] for bp in browser_pages}
    for old_item in existing_links:
        old_id = old_item.get("page_id")
        if old_id and old_id not in browser_page_ids:
            old_item["stt"] = len(new_links) + 1
            new_links.append(old_item)
            
    # 4. Save results back
    os.makedirs(os.path.dirname(TARGET_LINKS), exist_ok=True)
    with open(TARGET_LINKS, "w", encoding="utf-8") as f:
        json.dump(new_links, f, ensure_ascii=False, indent=4)
        
    print(f"Successfully synchronized {len(new_links)} fanpages to {TARGET_LINKS}")

if __name__ == "__main__":
    sync()
