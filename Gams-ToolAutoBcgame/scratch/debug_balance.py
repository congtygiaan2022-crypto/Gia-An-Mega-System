import sys
import os
import json

# Thêm đường dẫn gốc vào sys.path để import được core
sys.path.append(os.getcwd())

from core.browser import BrowserController

def debug_balance():
    print("🔍 Đang kết nối tới trình duyệt để kiểm tra balance...")
    # Khởi tạo browser nhưng không gọi start() để tránh kill cái đang chạy
    # Tuy nhiên, BrowserController.start() của mình có lệnh kill.
    # Mình sẽ viết code Selenium thuần để connect nếu có thể, 
    # nhưng tốt nhất là dùng chính BrowserController và sửa tạm thời để không kill.
    
    browser = BrowserController()
    # Mocking _kill_existing_chrome to do nothing
    browser._kill_existing_chrome = lambda x: print("Skipping kill for debug")
    
    if not browser.start():
        print("❌ Không thể khởi động browser debug")
        return

    driver = browser.driver
    print(f"🌐 Đang ở URL: {driver.current_url}")
    
    js_dump_balance = """
    function dumpBalance(root, results) {
        let els = root.querySelectorAll('*');
        for(let el of els) {
            let text = (el.innerText || '').trim();
            if (text.length > 0 && text.length < 50 && (text.includes('VND') || text.includes('VNDK') || text.includes('JB') || text.includes('USDT'))) {
                results.push({
                    tag: el.tagName,
                    class: el.className,
                    text: text,
                    rect: el.getBoundingClientRect()
                });
            }
            if (el.shadowRoot) dumpBalance(el.shadowRoot, results);
        }
        return results;
    }
    return dumpBalance(document, []);
    """
    
    try:
        data = driver.execute_script(js_dump_balance)
        print(f"📊 Tìm thấy {len(data)} phần tử tiềm năng chứa balance:")
        for item in data:
            print(f"  - [{item['tag']}] Cls: {item['class']} | Text: '{item['text']}'")
            
        # Chụp ảnh màn hình vùng header nếu được
        driver.save_screenshot("artifacts/balance_debug.png")
        print("📸 Đã chụp ảnh màn hình balance_debug.png")
        
        with open("artifacts/balance_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"💥 Lỗi JS: {e}")
    finally:
        # Đừng đóng browser của người dùng!
        pass

if __name__ == "__main__":
    debug_balance()
