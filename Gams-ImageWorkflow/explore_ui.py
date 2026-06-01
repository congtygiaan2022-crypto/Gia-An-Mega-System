import os
import json
import time
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import profile_manager

def dump_elements(page, site_name):
    print(f"[{site_name}] Đang chờ load trang...")
    time.sleep(10) # Đợi trang load hoàn toàn
    
    # JavaScript trích xuất các thành phần tương tác (inputs, textareas, buttons, contenteditable)
    js_code = """
    () => {
        const elements = document.querySelectorAll('input, textarea, button, [contenteditable="true"], [role="button"], [role="textbox"]');
        const results = [];
        elements.forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                results.push({
                    tag: el.tagName,
                    type: el.getAttribute('type') || '',
                    id: el.id,
                    className: el.className,
                    placeholder: el.getAttribute('placeholder') || '',
                    ariaLabel: el.getAttribute('aria-label') || '',
                    role: el.getAttribute('role') || '',
                    text: el.innerText ? el.innerText.substring(0, 50).trim() : '',
                    contentEditable: el.getAttribute('contenteditable') || ''
                });
            }
        });
        return results;
    }
    """
    elements = page.evaluate(js_code)
    
    with open(f"explore_{site_name}.json", "w", encoding="utf-8") as f:
        json.dump(elements, f, ensure_ascii=False, indent=4)
        
    print(f"[{site_name}] Đã trích xuất {len(elements)} phần tử.")

def main():
    profile_name = "Yui Hatano"
    with sync_playwright() as p:
        pm = profile_manager.ProfileManager("profiles")
        context = pm.launch_browser_for_profile(p, profile_name, headless=False)
        
        # 1. ChatGPT
        print("Mở ChatGPT...")
        page = context.new_page()
        page.goto("https://chatgpt.com/")
        dump_elements(page, "chatgpt")
        page.close()
        
        # 2. Google AI Studio
        print("Mở Google AI Studio...")
        page = context.new_page()
        page.goto("https://aistudio.google.com/prompts/new_chat")
        dump_elements(page, "google")
        page.close()
        
        # 3. Facebook Fanpage (Lấy link từ cấu hình)
        print("Mở FB Business Suite...")
        page = context.new_page()
        page.goto("https://business.facebook.com/latest/composer/?asset_id=439411339247687&business_id=1016985112612772")
        dump_elements(page, "facebook")
        page.close()
        
        context.close()

if __name__ == "__main__":
    main()
