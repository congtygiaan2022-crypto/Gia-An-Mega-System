"""
Script khôi phục tiến trình Google AI Studio cho Yui Hatano.
Ảnh và Text đã được tạo xong - nhiệm vụ: tải ảnh về + lấy text + đăng FB.
"""
import os
import sys
import time
import base64
import urllib.request
import re

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright
import profile_manager
import db_manager
import social_poster

PROFILE_NAME   = "Yui Hatano"
GOOGLE_AI_URL  = "https://aistudio.google.com/prompts/1dzHUCpOdLFa-NE2JWGRCzOMod108xE-D"
OUTPUT_DIR     = "output_data"

def download_image_from_page(page, profile_name, output_image_path, img_selector='ms-chat-turn .chat-turn-container.model img'):
    """3-tier image download: Download btn → base64 src → screenshot fallback."""
    download_success = False

    # TẦNG 1: Hover để hiện nút actions, rồi click Download
    try:
        page.locator('ms-chat-turn .chat-turn-container.model').last.hover()
        time.sleep(1.5)
    except:
        pass

    for dl_sel in [
        'button[aria-label*="Download"]',
        'button[aria-label*="download"]',
        'button[mattooltip*="Download"]',
        'button[mattooltip*="download"]',
        'button[data-test-id*="download"]',
        'a[download]',
    ]:
        try:
            dl_btn = page.locator(dl_sel).last
            if dl_btn.count() > 0:
                with page.expect_download(timeout=30000) as dl_info:
                    dl_btn.click(force=True)
                dl_info.value.save_as(output_image_path)
                print(f"[{profile_name}] ✅ Tải ảnh HQ thành công (nút Download).")
                return True
        except:
            pass

    # TẦNG 2: Trích xuất từ src attribute
    print(f"[{profile_name}] Không có nút Download. Thử trích xuất từ src ảnh...")
    for img_el in reversed(page.locator(img_selector).all()):
        src = img_el.get_attribute("src")
        if not src or "watermark" in src or "avatar" in src:
            continue
        if src.startswith("data:image"):
            img_data = src.split(",", 1)[1]
            with open(output_image_path, "wb") as f:
                f.write(base64.b64decode(img_data))
            print(f"[{profile_name}] ✅ Lưu ảnh từ base64 src.")
            return True
        elif src.startswith("http") or src.startswith("//"):
            try:
                full_url = src if src.startswith("http") else f"https:{src}"
                urllib.request.urlretrieve(full_url, output_image_path)
                print(f"[{profile_name}] ✅ Tải ảnh từ URL.")
                return True
            except:
                pass

    # TẦNG 3: Fallback - screenshot element
    print(f"[{profile_name}] Fallback: Chụp screenshot element ảnh.")
    for img_el in reversed(page.locator(img_selector).all()):
        src = img_el.get_attribute("src")
        if src and "watermark" not in src and "avatar" not in src:
            img_el.screenshot(path=output_image_path)
            print(f"[{profile_name}] ✅ Screenshot ảnh từ Google AI.")
            return True

    return False


def extract_text_from_page(page, profile_name):
    """Lấy text cuối cùng từ Google AI Studio."""
    chunks = page.locator('ms-chat-turn .chat-turn-container.model ms-text-chunk').all()
    if not chunks:
        return None
    text_raw = chunks[-1].inner_text()
    text_raw = re.sub(r'^Model\s*\d+:\d+\s*[AP]M\s*\n', '', text_raw, flags=re.MULTILINE)
    text_raw = text_raw.strip()
    return text_raw if text_raw else None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    img_path = os.path.join(OUTPUT_DIR, f"{PROFILE_NAME}_google_recover.png")
    txt_path = os.path.join(OUTPUT_DIR, f"{PROFILE_NAME}_google_recover.txt")

    print(f"[{PROFILE_NAME}] Bắt đầu khôi phục tiến trình Google AI Studio...")

    with sync_playwright() as p:
        pm = profile_manager.ProfileManager("profiles")
        context = pm.launch_browser_for_profile(p, PROFILE_NAME, headless=False)
        page = context.new_page()

        try:
            # 1. Mở lại đúng URL chat đã tạo ảnh
            print(f"[{PROFILE_NAME}] Đang truy cập: {GOOGLE_AI_URL}")
            page.goto(GOOGLE_AI_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(8)  # Đợi JS render + AngularJS boot xong

            # Debug: dump DOM để biết cấu trúc thực tế
            dom_content = page.content()
            with open('google_ai_live_dom.html', 'w', encoding='utf-8') as f:
                f.write(dom_content)
            print(f"[{PROFILE_NAME}] Đã dump live DOM vào google_ai_live_dom.html")

            # 2. Tìm ảnh với NHIỀU selector hơn
            print(f"[{PROFILE_NAME}] Tìm và tải ảnh HQ...")
            
            # Danh sách selector theo ưu tiên
            img_selectors = [
                'ms-chat-turn .chat-turn-container.model img:not([class*="avatar"]):not([class*="watermark"]):not([class*="icon"])',
                'ms-chat-turn .chat-turn-container.model img',
                '.chat-turn-container.model img',
                'ms-image-message img',
                'ms-image-message-group img', 
                '.model img[src*="blob"]',
                '.model img[src*="data:image"]',
                '.model img[src*="lh3.googleusercontent"]',
                '.model img:not([class*="avatar"]):not([src*="watermark"]):not([src*="gstatic"])',
                '.output-container img',
                'ms-turn img:not([class*="avatar"])',
                '[data-test-id*="image"] img',
                '[class*="image-container"] img',
                '[class*="generated"] img',
            ]
            
            img_count = 0
            working_selector = None
            for sel in img_selectors:
                try:
                    cnt = page.locator(sel).count()
                    if cnt > 0:
                        img_count = cnt
                        working_selector = sel
                        print(f"[{PROFILE_NAME}] Tìm thấy {cnt} ảnh với selector: {sel}")
                        break
                except:
                    pass
            
            if img_count == 0:
                print(f"[{PROFILE_NAME}] CẢNH BÁO: Không tìm thấy ảnh nào trong chat.")
                print(f"[{PROFILE_NAME}] Có thể session đã hết hạn hoặc chat không có ảnh AI.")
                print(f"[{PROFILE_NAME}] DOM đã được lưu vào google_ai_live_dom.html để kiểm tra.")
                return

            ok = download_image_from_page(page, PROFILE_NAME, img_path, working_selector)
            if not ok:
                print(f"[{PROFILE_NAME}] LỖI: Không thể tải ảnh về.")
                return

            # 3. Lấy text đã được tạo (có thể đã có sẵn hoặc chưa)
            print(f"[{PROFILE_NAME}] Trích xuất text từ Google AI...")
            text_raw = extract_text_from_page(page, PROFILE_NAME)

            if not text_raw:
                print(f"[{PROFILE_NAME}] Chưa có text. Sẽ gửi prompt text ngay...")
                # Gửi prompt text mới
                textarea_sel = None
                for sel in ['textarea[aria-label="Enter a prompt"]', 'textarea[formcontrolname="promptText"]']:
                    try:
                        loc = page.locator(sel).first
                        if loc.count() > 0:
                            textarea_sel = loc
                            break
                    except:
                        pass

                if textarea_sel:
                    prompt_text = "Hãy viết 1 caption thả thính ngắn gọn, gợi cảm nhưng lịch sự để đăng kèm ảnh này lên Facebook Fanpage. Chỉ viết caption, không cần giải thích."
                    textarea_sel.fill(prompt_text)
                    page.keyboard.press("Control+Enter")
                    print(f"[{PROFILE_NAME}] Đã gửi prompt text. Đang chờ tối đa 2 phút...")

                    last_text, stable_count = "", 0
                    wait_start = time.time()
                    while time.time() - wait_start < 120:
                        try:
                            chunks = page.locator('ms-chat-turn .chat-turn-container.model ms-text-chunk').all()
                            if chunks:
                                current_text = chunks[-1].inner_text()
                                if current_text == last_text and len(current_text) > 0:
                                    stable_count += 1
                                    if stable_count >= 3:
                                        break
                                else:
                                    last_text = current_text
                                    stable_count = 0
                        except:
                            pass
                        time.sleep(2)

                    text_raw = extract_text_from_page(page, PROFILE_NAME)

            if not text_raw:
                text_raw = "Mỗi khoảnh khắc đều là một tác phẩm nghệ thuật 💕 #xinh #gợicảm"
                print(f"[{PROFILE_NAME}] Dùng caption mặc định.")

            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text_raw)
            print(f"[{PROFILE_NAME}] ✅ Đã lưu text: {txt_path}")
            print(f"[{PROFILE_NAME}] Caption: {text_raw[:80]}...")

            # 4. Đăng lên Facebook
            print(f"[{PROFILE_NAME}] Tiến hành đăng bài lên Facebook...")
            db_manager.init_db()
            profile_cfg = db_manager.get_profile_config(PROFILE_NAME)
            fanpage_url = profile_cfg.get("fanpage_url", "")
            if not fanpage_url:
                print(f"[{PROFILE_NAME}] LỖI: Không tìm thấy fanpage_url trong DB cho profile này.")
                return

            poster = social_poster.SocialPoster(context, fanpage_url)
            poster.post_to_fanpage(PROFILE_NAME, txt_path, img_path)
            print(f"[{PROFILE_NAME}] 🎉 DONE! Đã đăng thành công lên Facebook!")

        except Exception as e:
            print(f"[{PROFILE_NAME}] LỖI: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                context.close()
            except:
                pass


if __name__ == "__main__":
    main()
