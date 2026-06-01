import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

# Thêm thư mục gốc vào PYTHONPATH để import core
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.browser import BrowserController

def test_login():
    print("Starting Browser...")
    browser = BrowserController(headless=True) # Run headless for testing DOM extraction
    if not browser.start():
        print("Lỗi khởi động.")
        return

    try:
        print("Điều hướng tới BCGame...")
        browser.navigate("https://bcvn2.com/vi")
        time.sleep(3)

        print("Tìm nút Đăng nhập...")
        # Tìm nút Đăng Nhập
        login_btn = browser.find_element(
            browser.By.XPATH,
            "//button[contains(text(), 'Đăng Nhập') or contains(text(), 'Login') or contains(@class, 'login')]"
        )
        if not login_btn:
            login_btn = browser.find_element(browser.By.CSS_SELECTOR, "[data-testid='login-btn'], .login-btn, button.login")

        if login_btn:
            print("Click Đăng Nhập...")
            browser.click_element(login_btn)
            time.sleep(3) # Đợi form hiện ra
            
            # Chụp ảnh để xem form có hiện không
            screenshot_path = os.path.join(os.path.dirname(__file__), "login_form.png")
            browser.take_screenshot(screenshot_path)
            print(f"Đã chụp ảnh: {screenshot_path}")

            # Thử tìm các input
            inputs = browser.find_elements(browser.By.TAG_NAME, "input")
            print(f"Tìm thấy {len(inputs)} thẻ input:")
            for inp in inputs:
                try:
                    inp_type = inp.get_attribute("type")
                    inp_name = inp.get_attribute("name")
                    inp_placeholder = inp.get_attribute("placeholder")
                    inp_class = inp.get_attribute("class")
                    print(f" - Input: type={inp_type}, name={inp_name}, placeholder={inp_placeholder}, class={inp_class}")
                except Exception:
                    pass
            
            # In ra HTML của phần tử cha (nếu có modal)
            # Thường modal login nằm cuối body hoặc có class chứa chữ login
            try:
                login_modal = browser.find_element(browser.By.CSS_SELECTOR, "div[class*='login'], div[class*='modal'], div[role='dialog']")
                if login_modal:
                    html = login_modal.get_attribute('outerHTML')
                    with open(os.path.join(os.path.dirname(__file__), "login_html.txt"), "w", encoding="utf-8") as f:
                        f.write(html)
                    print("Đã lưu DOM của form đăng nhập.")
            except Exception as e:
                print(f"Lỗi lấy DOM modal: {e}")

        else:
            print("Không tìm thấy nút Đăng Nhập!")

    finally:
        browser.stop()

if __name__ == "__main__":
    test_login()
