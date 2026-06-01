import json
import os
import urllib.parse

SOURCE_DB = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')), 'Gams-AutoPostFanpage', 'database.json')
TARGET_LINKS = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')), 'Gams Ai Jarvis Os', 'javis-agent/plugins/data/gams_insight/links.json')
BUSINESS_ID = "1016985112612772"

def sync():
    if not os.path.exists(SOURCE_DB):
        print(f"Error: Source database not found at {SOURCE_DB}")
        return

    # 1. Load source data
    with open(SOURCE_DB, "r", encoding="utf-8") as f:
        source_data = json.load(f)
        source_fanpages = source_data.get("fanpages", [])

    # 2. Load target data (to preserve existing insights)
    existing_links = []
    if os.path.exists(TARGET_LINKS):
        try:
            with open(TARGET_LINKS, "r", encoding="utf-8") as f:
                existing_links = json.load(f)
        except:
            existing_links = []

    # Map existing links by page_id
    existing_map = {item.get("page_id"): item for item in existing_links if item.get("page_id")}

    new_links = []
    for sp in source_fanpages:
        name = sp.get("name")
        link = sp.get("link", "")
        
        # Extract asset_id (page_id)
        page_id = ""
        if "asset_id=" in link:
            parsed = urllib.parse.urlparse(link)
            params = urllib.parse.parse_qs(parsed.query)
            page_id = params.get("asset_id", [""])[0]
        
        if not page_id or not name:
            continue

        # Construct target URL
        target_url = f"https://business.facebook.com/latest/insights/overview/?business_id={BUSINESS_ID}&asset_id={page_id}"

        # Merge with existing data if available
        entry = {
            "stt": sp.get("stt", len(new_links) + 1),
            "page_name": name,
            "page_id": page_id,
            "url": target_url,
            "status": "Chưa chạy"
        }

        if page_id in existing_map:
            old = existing_map[page_id]
            # Keep existing status and dynamic data
            entry["status"] = old.get("status", "Chưa chạy")
            entry["data"] = old.get("data", {})
            entry["total_followers"] = old.get("total_followers", "")
            entry["latest_post_date"] = old.get("latest_post_date", "")
            entry["latest_post_title"] = old.get("latest_post_title", "")
            if "last_scanned" in old:
                entry["last_scanned"] = old["last_scanned"]
        
        new_links.append(entry)

    # 3. Save target data
    os.makedirs(os.path.dirname(TARGET_LINKS), exist_ok=True)
    with open(TARGET_LINKS, "w", encoding="utf-8") as f:
        json.dump(new_links, f, ensure_ascii=False, indent=4)
    
    print(f"Successfully synchronized {len(new_links)} fanpages to {TARGET_LINKS}")

if __name__ == "__main__":
    sync()
