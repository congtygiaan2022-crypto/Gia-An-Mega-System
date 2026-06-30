import os
import time
import random
from PIL import Image
from core.bug_tracker import track_errors
import db_manager

def print(*args, **kwargs):
    import builtins
    builtins.print(*args, **kwargs)
    msg = " ".join(str(arg) for arg in args)
    if msg.startswith("[") and "]" in msg:
        profile_name = msg[1:msg.find("]")]
        try:
            db_manager.log_msg(profile_name, msg)
        except Exception:
            pass

class AIGenerator:
    def __init__(self, context, ai_studio_url, output_data_dir="output_data"):
        self.context = context
        self.ai_studio_url = ai_studio_url
        self.output_data_dir = output_data_dir

    @track_errors("ai_generator", "generate_content")
    def generate_content(self, profile_name, prompt, status_base, input_image_path, prompt_img=None, output_txt_dir=None, output_img_dir=None, ai_source="google"):
        """
        Tự động hóa quá trình tạo nội dung trên AI Studio hoặc ChatGPT.
        """
        if output_txt_dir is None:
            output_txt_dir = self.output_data_dir
        if output_img_dir is None:
            output_img_dir = self.output_data_dir

        # Đảm bảo thư mục lưu trữ tồn tại
        os.makedirs(output_txt_dir, exist_ok=True)
        os.makedirs(output_img_dir, exist_ok=True)
        is_new_page = False
        if self.context.pages:
            page = self.context.pages[0]
        else:
            page = self.context.new_page()
            is_new_page = True
        
        try:
            sources_to_try = [ai_source]

            output_image_path = os.path.join(output_img_dir, f"{profile_name}_{int(time.time())}.png")
            generated_text = None
            img_downloaded = False
            errors = []

            for current_source in sources_to_try:
                try:
                    # Đảm bảo page hoạt động bình thường trước khi chạy nguồn mới
                    try:
                        if page.is_closed():
                            print(f"[{profile_name}] Page cũ đã đóng, đang tạo page mới cho {current_source.upper()}...")
                            page = self.context.new_page()
                    except Exception:
                        print(f"[{profile_name}] Không thể kiểm tra page, đang tạo page mới cho {current_source.upper()}...")
                        page = self.context.new_page()

                    # --- Truy cập AI và Upload Ảnh ---
                    if current_source == "chatgpt":
                        if "chatgpt.com/c/" in self.ai_studio_url or "chatgpt.com/g/" in self.ai_studio_url:
                            url = self.ai_studio_url
                        else:
                            url = "https://chatgpt.com/images" if "chatgpt.com/images" in self.ai_studio_url else "https://chatgpt.com/"
                        print(f"[{profile_name}] Đang truy cập ChatGPT ({url})...")
                        try:
                            page.goto(url, wait_until="commit", timeout=60000)
                        except Exception as e:
                            print(f"[{profile_name}] Warning: page.goto commit for ChatGPT timed out/failed: {e}")
                        
                        try:
                            page.wait_for_selector('#prompt-textarea', timeout=30000)
                        except Exception as e:
                            print(f"[{profile_name}] Warning: ChatGPT prompt textarea not found: {e}")
                        time.sleep(5)
                        
                        # --- Kiểm tra trạng thái đăng nhập ChatGPT ---
                        is_logged_in = True
                        login_selectors = [
                            'button[data-testid="login-button"]',
                            'a[href*="auth/login"]',
                            'button:has-text("Log in")',
                            'button:has-text("Sign up")',
                            'button:has-text("Đăng nhập")',
                            'button:has-text("Đăng ký")',
                            'a:has-text("Log in")',
                            'a:has-text("Sign up")',
                            'a:has-text("Đăng nhập")',
                            'a:has-text("Đăng ký")'
                        ]
                        for sel in login_selectors:
                            try:
                                loc = page.locator(sel).first
                                if loc.count() > 0 and loc.is_visible():
                                    is_logged_in = False
                                    break
                            except:
                                pass
                                
                        if not is_logged_in:
                            print(f"[{profile_name}] ⚠️ Phát hiện ChatGPT chưa đăng nhập!")
                            raise Exception("CHATGPT_NOT_LOGGED_IN: ChatGPT chưa được đăng nhập. Yêu cầu tạo tài khoản mới.")
                        
                        if os.path.exists(input_image_path):
                            try:
                                # Playwright hỗ trợ bắn trực tiếp file vào input type=file, bất chấp ẩn hiện
                                page.locator('input[type="file"][multiple]').first.set_input_files(input_image_path)
                                print(f"[{profile_name}] Đã upload ảnh gốc lên ChatGPT.")
                                time.sleep(2)
                            except Exception as e:
                                print(f"[{profile_name}] Lỗi upload ảnh ChatGPT: {e}")
                                raise Exception(f"Không thể upload ảnh lên ChatGPT: {e}")
                        
                        if prompt_img and prompt_img.strip():
                            try:
                                # Đếm số lượng ảnh cũ (nếu dùng link chat cũ)
                                prev_img_count = 0
                                for _ in range(3):
                                    try:
                                        prev_img_count = page.locator('img[alt*="Generated"], img[alt*="generated"]').count()
                                        break
                                    except Exception as context_err:
                                        if "context was destroyed" in str(context_err).lower():
                                            time.sleep(2)
                                            continue
                                        raise
                                
                                page.locator('#prompt-textarea').fill(prompt_img)
                                time.sleep(1)
                                page.locator('button[data-testid="send-button"]').click()
                                print(f"[{profile_name}] Đã gửi prompt VẼ ẢNH cho ChatGPT, đang chờ tối đa 5 phút...")
                                
                                # Chờ ảnh xuất hiện (Timeout 5 phút = 300s)
                                wait_start = time.time()
                                last_text = ""
                                stable_count = 0
                                while time.time() - wait_start < 300:
                                    # Fast fail nếu gặp lỗi chính sách
                                    if page.locator('text=violate our guardrails').count() > 0 or page.locator('text=nudity, sexuality').count() > 0 or page.locator(':has-text("may violate our guardrails")').count() > 0:
                                        raise Exception("POLICY_VIOLATION: ChatGPT từ chối tạo ảnh do vi phạm chính sách nội dung nhạy cảm.")
                                        
                                    current_img_count = 0
                                    for _ in range(3):
                                        try:
                                            current_img_count = page.locator('img[alt*="Generated"], img[alt*="generated"]').count()
                                            break
                                        except Exception as context_err:
                                            if "context was destroyed" in str(context_err).lower():
                                                time.sleep(2)
                                                continue
                                            raise
                                    if current_img_count > prev_img_count:
                                        time.sleep(5) # Đợi thêm xíu cho ảnh load hẳn
                                        break
                                        
                                    # Kiểm tra text ổn định để dừng sớm nếu ChatGPT chỉ phản hồi văn bản (ví dụ từ chối tạo ảnh)
                                    try:
                                        assistant_turns = page.locator('[data-message-author-role="assistant"]').all()
                                        if assistant_turns:
                                            text_element = assistant_turns[-1].locator('.markdown')
                                            raw_text = text_element.first.inner_text().strip() if text_element.count() > 0 else assistant_turns[-1].inner_text().strip()
                                            if raw_text:
                                                # Check if response indicates login requirement
                                                low_text = raw_text.lower()
                                                if "please log in" in low_text or "please sign in" in low_text or "need to be logged in" in low_text or "log in to use" in low_text or "logged in to use" in low_text:
                                                    raise Exception(f"CHATGPT_NOT_LOGGED_IN: ChatGPT yêu cầu đăng nhập: {raw_text}")
                                                
                                                if raw_text == last_text:
                                                    stable_count += 1
                                                    if stable_count >= 10: # Khoảng 5 giây không đổi
                                                        is_generating = page.locator('button[data-testid="stop-button"]').count() > 0
                                                        if not is_generating:
                                                            print(f"[{profile_name}] ChatGPT chỉ trả về text hoặc từ chối vẽ ảnh: {raw_text[:200]}")
                                                            raise Exception(f"ChatGPT chỉ trả về text mà không tạo ảnh: {raw_text}")
                                                else:
                                                    last_text = raw_text
                                                    stable_count = 0
                                    except Exception as text_check_err:
                                        if "ChatGPT chỉ trả về text" in str(text_check_err) or "CHATGPT_NOT_LOGGED_IN" in str(text_check_err):
                                            raise text_check_err
                                            
                                    time.sleep(0.5)
                                    
                                # Kiểm tra lại nếu quá 5 phút vẫn không có ảnh
                                if page.locator('img[alt*="Generated"], img[alt*="generated"]').count() <= prev_img_count:
                                    raise Exception("Hết thời gian chờ 5 phút nhưng không thấy ChatGPT tạo ảnh mới hoặc ChatGPT từ chối vẽ ảnh.")
                                    
                                # Trích xuất ảnh
                                img_elements = page.locator('img[alt*="Generated"]').all()
                                if img_elements:
                                    print(f"[{profile_name}] Đã thấy ảnh do ChatGPT vẽ. Tiến hành tải ảnh chất lượng cao...")
                                    img_elements[-1].click()
                                    time.sleep(3)
                                    
                                    try:
                                        download_btn = page.locator('button[aria-label*="Download"], button[title*="Download"], button[aria-label*="Save"], button[title*="Save"], button[aria-label*="Lưu"], div[role="button"]:has-text("Download"), a[download]').first
                                        if download_btn.count() > 0:
                                            try:
                                                is_menu = download_btn.get_attribute("aria-haspopup") == "menu"
                                                
                                                if is_menu:
                                                    download_btn.click()
                                                    time.sleep(1)
                                                    real_dl_btn = page.locator('div[role="menuitem"]:has-text("Download"), div[role="menuitem"]:has-text("Save"), div[role="menuitem"]:has-text("Lưu"), a[download]').first
                                                    with page.expect_download(timeout=30000) as download_info:
                                                        real_dl_btn.click()
                                                else:
                                                    with page.expect_download(timeout=30000) as download_info:
                                                        download_btn.click()
                                                        
                                                download = download_info.value
                                                download.save_as(output_image_path)
                                                print(f"[{profile_name}] Đã tải ảnh HQ từ ChatGPT về thành công.")
                                                img_downloaded = True
                                                
                                                # Tắt modal
                                                try:
                                                    page.locator('button[aria-label="Close"], button[aria-label="Đóng"], button[aria-label="Close fullscreen view"]').first.click()
                                                except:
                                                    page.keyboard.press("Escape")
                                                    
                                            except Exception as dl_err:
                                                print(f"[{profile_name}] Lỗi khi click nút tải xuống HQ: {dl_err}. Thử tải ảnh thumb dự phòng...")
                                                # Fallback về thumb
                                                img_url = img_elements[-1].get_attribute("src")
                                                response = page.request.get(img_url)
                                                with open(output_image_path, "wb") as f:
                                                    f.write(response.body())
                                                img_downloaded = True
                                    except Exception as dl_wrapper_err:
                                        pass
                            except Exception as e:
                                print(f"[{profile_name}] Lỗi khi xử lý prompt ảnh ChatGPT: {e}")
                                raise Exception(f"Không thể gửi prompt ảnh lên ChatGPT: {e}")

                        # --- PHẦN 2: XỬ LÝ TEXT ---
                        try:
                            full_prompt = f"{status_base}\n{prompt}" if status_base else prompt
                            page.locator('#prompt-textarea').fill(full_prompt)
                            time.sleep(1)
                            page.locator('button[data-testid="send-button"]').click()
                            print(f"[{profile_name}] Đã gửi prompt VIẾT STATUS cho ChatGPT, đang chờ...")
                            
                            wait_start = time.time()
                            while time.time() - wait_start < 60:
                                is_generating = page.locator('button[data-testid="stop-button"]').count() > 0
                                if not is_generating and (time.time() - wait_start > 5):
                                    break
                                time.sleep(2)
                                
                            elements = page.locator('[data-message-author-role="assistant"]').all()
                            if elements:
                                # Ưu tiên lấy trong thẻ markdown để không dính nút Edit/Copy
                                markdown_locator = elements[-1].locator('.markdown')
                                if markdown_locator.count() > 0:
                                    raw_text = markdown_locator.first.inner_text()
                                else:
                                    raw_text = elements[-1].inner_text()
                                
                                if raw_text:
                                    low_text = raw_text.lower()
                                    if "please log in" in low_text or "please sign in" in low_text or "need to be logged in" in low_text or "log in to use" in low_text or "logged in to use" in low_text:
                                        raise Exception(f"CHATGPT_NOT_LOGGED_IN: ChatGPT yêu cầu đăng nhập: {raw_text}")
                                
                                # Dọn dẹp các chữ rác nếu có (như Edit, Copy) bị dính vào đầu
                                import re
                                clean_text = re.sub(r'^(Edit|Copy|Like|Dislike)[\r\n]+', '', raw_text.strip(), flags=re.IGNORECASE)
                                generated_text = clean_text.strip()
                                
                                print(f"[{profile_name}] Đã lấy được text sạch từ ChatGPT.")
                        except Exception as e:
                            print(f"[{profile_name}] Lỗi khi xử lý prompt text ChatGPT: {e}")
                            raise Exception(f"Không thể xử lý prompt text ChatGPT: {e}")

                    else:
                        # GOOGLE AI STUDIO
                        url = "https://aistudio.google.com/prompts/new_chat?model=gemini-3-pro-image-preview"
                        print(f"[{profile_name}] Đang truy cập Google AI Studio ({url})...")
                        try:
                            page.goto(url, wait_until="commit", timeout=60000)
                        except Exception as e:
                            print(f"[{profile_name}] Warning: page.goto commit for Google AI Studio timed out/failed: {e}")
                        
                        # Wait for the prompt textarea to be visible with a longer timeout
                        textarea_element = None
                        textarea_selectors = [
                            'textarea[aria-label="Enter a prompt"]',
                            'textarea[formcontrolname="promptText"]',
                            'textarea.textarea',
                            'textarea[placeholder*="prompt"]'
                        ]
                        
                        start_time = time.time()
                        while time.time() - start_time < 40:
                            for sel in textarea_selectors:
                                try:
                                    loc = page.locator(sel).first
                                    if loc.count() > 0 and loc.is_visible():
                                        textarea_element = loc
                                        break
                                except:
                                    pass
                            if textarea_element:
                                break
                            time.sleep(1)
                            
                        if not textarea_element:
                            raise Exception("Không tìm thấy textarea nhập prompt của Google AI Studio sau 40 giây. Có thể trang web chưa load xong hoặc có lỗi.")
                        time.sleep(2)

                        def get_textarea():
                            try:
                                if textarea_element and textarea_element.count() > 0:
                                    return textarea_element
                            except:
                                pass
                            for sel in textarea_selectors:
                                try:
                                    loc = page.locator(sel).first
                                    if loc.count() > 0:
                                        return loc
                                except:
                                    pass
                            return page.locator('textarea[aria-label="Enter a prompt"]').first

                        def send_prompt_with_retry(prompt_text, description="prompt"):
                            print(f"[{profile_name}] Sending {description} to Google AI Studio...")
                            for attempt in range(3):
                                try:
                                    txt_el = get_textarea()
                                    txt_el.focus()
                                    txt_el.fill(prompt_text)
                                    time.sleep(1)
                                    txt_el.press("Control+Enter")
                                    return True
                                except Exception as fill_err:
                                    print(f"[{profile_name}] Attempt {attempt+1} to send {description} failed: {fill_err}")
                                    time.sleep(2)
                            try:
                                page.keyboard.press("Control+A")
                                page.keyboard.press("Backspace")
                                page.keyboard.type(prompt_text)
                                time.sleep(1)
                                page.keyboard.press("Control+Enter")
                                return True
                            except Exception as final_kb_err:
                                raise Exception(f"Không thể điền và gửi {description} sau các lượt thử: {final_kb_err}")

                        # --- PHẦN 1: XỬ LÝ ẢNH ---
                        if os.path.exists(input_image_path):
                            try:
                                uploaded = False
                                
                                # Try setting files directly first, in case the input is already there in the DOM
                                for inp_sel in ['input[type="file"][data-test-upload-file-input]', 'input[type="file"].file-input', 'input[type="file"]']:
                                    try:
                                        inp_loc = page.locator(inp_sel).first
                                        if inp_loc.count() > 0:
                                            inp_loc.set_input_files(input_image_path, timeout=3000)
                                            time.sleep(2)
                                            print(f"[{profile_name}] Uploaded image directly (pre-existing input): {inp_sel}")
                                            uploaded = True
                                            break
                                    except:
                                        pass

                                if not uploaded:
                                    # 1. Find the Add Media button
                                    add_btn = None
                                    add_btn_selectors = [
                                        '[data-test-id="add-media-button"]', 
                                        'button[data-test-id="add-media-button"]',
                                        'button[data-test="selectMediaMenu"]',
                                        'ms-add-media-button button',
                                        'button[aria-label="Insert images, videos, audio, or files"]', 
                                        'button[aria-label="Insert images or files"]', 
                                        'button:has-text("add_circle")'
                                    ]
                                    for sel in add_btn_selectors:
                                        try:
                                            loc = page.locator(sel).first
                                            if loc.count() > 0:
                                                add_btn = loc
                                                break
                                        except:
                                            pass
                                    
                                    if add_btn:
                                        # Try to click the Add Media button to open the menu
                                        for click_attempt in range(3):
                                            try:
                                                expanded = add_btn.get_attribute("aria-expanded")
                                                if expanded == "true":
                                                    print(f"[{profile_name}] Add Media menu is already expanded.")
                                                    break
                                                print(f"[{profile_name}] Clicking Add Media button (attempt {click_attempt+1})...")
                                                add_btn.click(timeout=5000, force=True)
                                                # Wait up to 3s to see if the input[type=file] appears
                                                page.wait_for_selector('input[type="file"]', timeout=3000)
                                                print(f"[{profile_name}] Opened Add Media menu.")
                                                break
                                            except Exception as click_err:
                                                print(f"[{profile_name}] Click Add Media attempt {click_attempt+1} failed: {click_err}")
                                                time.sleep(1.5)
                                    else:
                                        print(f"[{profile_name}] Warning: Add Media button not found, searching for inputs directly.")
                                
                                # 2. Try upload now that we attempted to expand the menu
                                if not uploaded:
                                    for inp_sel in ['input[type="file"][data-test-upload-file-input]', 'input[type="file"].file-input', 'input[type="file"]']:
                                        try:
                                            inp_loc = page.locator(inp_sel).first
                                            if inp_loc.count() > 0:
                                                inp_loc.set_input_files(input_image_path, timeout=5000)
                                                print(f"[{profile_name}] Uploaded image via input: {inp_sel}")
                                                uploaded = True
                                                break
                                        except:
                                            pass
                                    
                                # 3. Fallback: try File Chooser if direct input setting did not succeed
                                if not uploaded:
                                    print(f"[{profile_name}] Fallback to File Chooser...")
                                    upload_menu = None
                                    for menu_selector in [
                                        '.upload-file-menu-item',
                                        'mat-menu-item:has-text("Upload files")',
                                        'button:has-text("Upload files")',
                                        'mat-menu-item:has-text("Upload")',
                                        'button:has-text("Upload")'
                                    ]:
                                        try:
                                            loc = page.locator(menu_selector).first
                                            if loc.count() > 0:
                                                upload_menu = loc
                                                break
                                        except:
                                            pass
                                            
                                    if upload_menu:
                                        try:
                                            with page.expect_file_chooser(timeout=5000) as fc_info:
                                                upload_menu.click(force=True, timeout=5000)
                                            fc_info.value.set_files(input_image_path)
                                            uploaded = True
                                            print(f"[{profile_name}] Uploaded image via File Chooser.")
                                        except Exception as fc_err:
                                            print(f"[{profile_name}] File Chooser attempt failed: {fc_err}")
                                
                                # 4. One final fallback: direct input type file setting anywhere on the page
                                if not uploaded:
                                    print(f"[{profile_name}] Last resort input fallback...")
                                    try:
                                        page.locator('input[type="file"]').first.set_input_files(input_image_path, timeout=5000)
                                        uploaded = True
                                        print(f"[{profile_name}] Uploaded image via raw page input fallback.")
                                    except Exception as final_err:
                                        raise Exception(f"Tất cả các phương pháp upload đều thất bại: {final_err}")
                                    
                                time.sleep(3)
                            except Exception as e:
                                print(f"[{profile_name}] Lỗi upload ảnh Google AI Studio: {e}")
                                raise Exception(f"Không thể upload ảnh lên Google AI Studio: {e}")

                        if prompt_img and prompt_img.strip():
                            try:
                                # Đếm số lượng ảnh cũ
                                prev_img_count = page.locator('ms-chat-turn .chat-turn-container.model img').count()
                                
                                send_prompt_with_retry(prompt_img, "image prompt")
                                
                                # Fallback click nút Run
                                try:
                                    run_btn = page.locator('ms-run-button button, button:has-text("Run")').first
                                    if run_btn.count() > 0:
                                        run_btn.click(timeout=3000, force=True)
                                except:
                                    pass
                                    
                                print(f"[{profile_name}] Đã gửi prompt VẼ ẢNH cho Google AI Studio, đang chờ tối đa 5 phút...")
                                
                                # Chờ ảnh (Timeout 5 phút = 300s)
                                wait_start = time.time()
                                last_text = ""
                                stable_count = 0
                                while time.time() - wait_start < 300:
                                    current_img_count = page.locator('ms-chat-turn .chat-turn-container.model img').count()
                                    if current_img_count > prev_img_count:
                                        time.sleep(3) # Đợi ảnh load hẳn
                                        break
                                        
                                    # Kiểm tra text ổn định để dừng sớm nếu Google AI chỉ trả về text mà không tạo ảnh
                                    try:
                                        chunks = page.locator('ms-chat-turn .chat-turn-container.model ms-text-chunk').all()
                                        if chunks:
                                            current_text = chunks[-1].inner_text().strip()
                                            if current_text:
                                                if current_text == last_text:
                                                    stable_count += 1
                                                    if stable_count >= 10: # Khoảng 5 giây
                                                        # Kiểm tra xem có đang tạo hay không
                                                        is_running = page.locator('ms-run-button button:has-text("Stop"), button:has-text("Stop")').count() > 0
                                                        if not is_running:
                                                            print(f"[{profile_name}] Google AI chỉ trả về text hoặc báo lỗi: {current_text[:200]}")
                                                            raise Exception(f"Google AI chỉ trả về text mà không tạo ảnh: {current_text}")
                                                else:
                                                    last_text = current_text
                                                    stable_count = 0
                                    except Exception as text_check_err:
                                        if "Google AI chỉ trả về text" in str(text_check_err):
                                            raise text_check_err
                                            
                                    time.sleep(0.5)
                                    
                                if page.locator('ms-chat-turn .chat-turn-container.model img:not([class*="avatar"]):not([class*="watermark"]):not([class*="icon"])').count() <= prev_img_count:
                                    raise Exception("Hết thời gian chờ 5 phút nhưng không thấy Google AI tạo ảnh mới.")
                                
                                # Cập nhật biến prev_img_count với selector đúng
                                AI_IMG_SEL = 'ms-chat-turn .chat-turn-container.model img:not([class*="avatar"]):not([class*="watermark"]):not([class*="icon"])'
                                print(f"[{profile_name}] Đã thấy ảnh AI. Đang tải ảnh HQ...")
                                download_success = False
                                
                                # TẦNG 1: Hover + tìm nút Download
                                try:
                                    page.locator('ms-chat-turn .chat-turn-container.model').last.hover()
                                    time.sleep(1)
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
                                            print(f"[{profile_name}] ✅ Đã tải ảnh HQ từ Google AI (nút Download).")
                                            img_downloaded = True
                                            download_success = True
                                            break
                                    except:
                                        pass
                                
                                # TẦNG 2: Lấy src (base64 hoặc URL)
                                if not download_success:
                                    print(f"[{profile_name}] Không tìm thấy nút Download. Thử trích xuất từ src...")
                                    for img_el in reversed(page.locator(AI_IMG_SEL).all()):
                                        src = img_el.get_attribute("src")
                                        if not src or "watermark" in src or "avatar" in src:
                                            continue
                                        if src.startswith("data:image"):
                                            import base64
                                            img_data = src.split(",", 1)[1]
                                            with open(output_image_path, "wb") as f:
                                                f.write(base64.b64decode(img_data))
                                            print(f"[{profile_name}] ✅ Đã lưu ảnh từ base64 src.")
                                            img_downloaded = True
                                            download_success = True
                                            break
                                        elif src.startswith("http") or src.startswith("//"):
                                            try:
                                                import urllib.request
                                                full_url = src if src.startswith("http") else f"https:{src}"
                                                urllib.request.urlretrieve(full_url, output_image_path)
                                                print(f"[{profile_name}] ✅ Đã tải ảnh từ URL.")
                                                img_downloaded = True
                                                download_success = True
                                                break
                                            except:
                                                pass
                                
                                if not download_success:
                                    print(f"[{profile_name}] Fallback: Chụp screenshot element ảnh.")
                                    for img_el in reversed(page.locator(AI_IMG_SEL).all()):
                                        src = img_el.get_attribute("src")
                                        if src and "watermark" not in src and "avatar" not in src:
                                            img_el.screenshot(path=output_image_path)
                                            print(f"[{profile_name}] ✅ Screenshot ảnh từ Google AI.")
                                            img_downloaded = True
                                            break
                            except Exception as e:
                                print(f"[{profile_name}] Lỗi khi xử lý prompt ảnh Google AI: {e}")
                                raise Exception(f"Không thể xử lý prompt ảnh Google AI Studio: {e}")

                        # --- PHẦN 2: XỬ LÝ TEXT ---
                        try:
                            full_prompt = f"{status_base}\n{prompt}" if status_base else prompt
                            send_prompt_with_retry(full_prompt, "text status prompt")
                            print(f"[{profile_name}] Đã gửi prompt VIẾT STATUS cho Google AI Studio, đang chờ...")
                            
                            wait_start = time.time()
                            last_text = ""
                            stable_count = 0
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
                                
                            # Trích xuất text Google AI
                            chunks = page.locator('ms-chat-turn .chat-turn-container.model ms-text-chunk').all()
                            if chunks:
                                text_raw = chunks[-1].inner_text()
                                import re
                                text_raw = re.sub(r'^Model\s*\d+:\d+\s*[AP]M\s*\n', '', text_raw, flags=re.MULTILINE)
                                generated_text = text_raw
                                print(f"[{profile_name}] Đã lấy được text từ Google AI Studio.")
                        except Exception as e:
                            print(f"[{profile_name}] Lỗi khi xử lý prompt text Google AI: {e}")
                            raise Exception(f"Không thể xử lý prompt text Google AI Studio: {e}")

                    if not img_downloaded:
                        raise Exception(f"Tiến trình {current_source.upper()} không tạo được ảnh mới.")

                    # Nếu chạy thành công toàn bộ, thoát khỏi vòng lặp fallback
                    break

                except Exception as e:
                    errors.append(f"{current_source.upper()}: {e}")
                    print(f"[{profile_name}] Nguồn {current_source.upper()} thất bại: {e}")
                    continue
                
            if not img_downloaded or not generated_text:
                error_msg = "Tất cả các nguồn AI đều thất bại hoặc không tạo được ảnh/text! (Nghiêm cấm dùng lại ảnh gốc)\nChi tiết lỗi:\n" + "\n".join(errors)
                raise Exception(error_msg)
                
            # --- Lưu dữ liệu Text ---
            output_text_path = os.path.join(output_txt_dir, f"{profile_name}_{int(time.time())}.txt")
            with open(output_text_path, "w", encoding="utf-8") as f:
                f.write(generated_text)

            # --- Xử lý ẢNH: Xóa EXIF và Đổi tên giả lập iPhone ---
            if os.path.exists(output_image_path):
                iphone_filename = f"IMG_{random.randint(1000, 9999)}.JPG"
                iphone_image_path = os.path.join(output_img_dir, iphone_filename)
                
                try:
                    with Image.open(output_image_path) as img:
                        # Convert sang RGB để lưu dạng JPEG chuẩn
                        rgb_img = img.convert('RGB')
                        # Lưu ảnh với chất lượng cao, Pillow tự động vứt bỏ toàn bộ EXIF/Metadata cũ
                        rgb_img.save(iphone_image_path, 'JPEG', quality=95)
                    
                    # Xóa file ảnh raw tải về từ AI
                    os.remove(output_image_path)
                    final_image_path = iphone_image_path
                    print(f"[{profile_name}] Đã render lại ảnh sang chuẩn iPhone ({iphone_filename}) và xóa siêu dữ liệu AI.")
                except Exception as img_err:
                    print(f"[{profile_name}] Lỗi khi render ảnh iPhone: {img_err}")
                    final_image_path = output_image_path
            else:
                final_image_path = output_image_path

            print(f"[{profile_name}] Đã tạo xong nội dung.")
            return output_text_path, final_image_path
        except Exception as e:
            print(f"[{profile_name}] Lỗi khi generate content: {str(e)}")
            raise e
        finally:
            if is_new_page:
                try:
                    page.close()
                except:
                    pass
