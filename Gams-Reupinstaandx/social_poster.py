import os
import time
from core.bug_tracker import track_errors
import db_manager

def p_log(profile_name, msg):
    print(msg)
    try:
        db_manager.log_msg(profile_name, msg)
    except Exception:
        pass

class SocialPoster:
    def __init__(self, context, fanpage_url):
        self.context = context
        self.fanpage_url = fanpage_url

    @track_errors("social_poster", "post_to_fanpage")
    def post_to_fanpage(self, profile_name, text_path, image_path, cleanup=True, publish=True):
        """
        Tự động hóa đăng bài lên Facebook Fanpage.
        """
        if not text_path or not image_path:
            p_log(profile_name, f"[{profile_name}] Thiếu thông tin ảnh/text để đăng bài.")
            return False

        with open(text_path, "r", encoding="utf-8") as f:
            status_text = f.read()

        # Luon mo tab moi de tranh xung dot trang thai/modal tu lan dang truoc
        page = self.context.new_page()
        is_new_page = True
        try:
            target_url = self.fanpage_url
            if "redirect_session_id=" in target_url:
                import re
                target_url = re.sub(r'[&?]redirect_session_id=[^&]*', '', target_url)
                if "?&" in target_url:
                    target_url = target_url.replace("?&", "?")
                elif target_url.endswith("?") or target_url.endswith("&"):
                    target_url = target_url[:-1]
                    
            p_log(profile_name, f"[{profile_name}] Đang truy cập Fanpage: {target_url}")
            page.goto(target_url, wait_until="domcontentloaded")
            time.sleep(5)
            
            # Dismiss general popups/notifications first (Escape)
            for _ in range(2):
                page.keyboard.press("Escape")
                time.sleep(0.5)

            # Scope selector to the dialog if it exists, otherwise fall back to page
            is_composer_url = "business.facebook.com" in page.url or "business.facebook.com" in self.fanpage_url
            
            if is_composer_url:
                p_log(profile_name, f"[{profile_name}] Đang trên trang Meta Business Composer. Bỏ qua bước tìm nút mở hộp thoại.")
                container = page
                
                # Chờ composer load hoàn tất - dùng nhiều selector hơn để bắt cả giao diện video
                p_log(profile_name, f"[{profile_name}] Đang chờ trang Meta Business Composer tải xong...")
                composer_loaded = False
                start_load = time.time()
                # Các selector có thể xuất hiện khi composer load (anh hoac video)
                composer_selectors = [
                    'div[role="combobox"][contenteditable="true"]',
                    'input[type="file"]',
                    'div[aria-label*="photo"]',
                    'div[aria-label*="Photo"]',
                    'div[aria-label*="video"]',
                    'div[aria-label*="Video"]',
                    'div[aria-label*="anh"]',
                    'div[aria-label*="Anh"]',
                    'span:has-text("Photo/video")',
                    'span:has-text("Add photo")',
                    'span:has-text("Them anh")',
                    'span:has-text("Thêm ảnh")',
                ]
                while time.time() - start_load < 60:  # Tăng lên 60 giây
                    for frame in [page] + page.frames:
                        for sel in composer_selectors:
                            try:
                                if frame.locator(sel).first.count() > 0:
                                    composer_loaded = True
                                    break
                            except:
                                pass
                        if composer_loaded:
                            break
                    if composer_loaded:
                        break
                    time.sleep(1)
                if composer_loaded:
                    p_log(profile_name, f"[{profile_name}] ✅ Trang Meta Business Composer đã tải xong!")
                    time.sleep(2)  # Thêm delay để page ổn định hoàn toàn
                else:
                    p_log(profile_name, f"[{profile_name}] Warning: Hết thời gian chờ composer tải, tiếp tục chạy...")
                    time.sleep(3)  # Chờ thêm cho dù timeout

            else:
                # Check if create post dialog is already open
                dialog_locator = page.locator('div[role="dialog"]')
                if dialog_locator.count() == 0:
                    p_log(profile_name, f"[{profile_name}] Hộp thoại tạo bài viết chưa mở. Đang tìm nút mở...")
                    create_post_locators = [
                        'span:has-text("Bạn đang nghĩ gì?")',
                        'span:has-text("Write something...")',
                        'span:has-text("Tạo bài viết")',
                        'span:has-text("Create post")',
                        'div[role="button"]:has-text("Bạn đang nghĩ gì?")',
                        'div[role="button"]:has-text("Write something...")',
                        'div[role="button"]:has-text("Tạo bài viết")',
                        'div[role="button"]:has-text("Create post")'
                    ]
                    for loc in create_post_locators:
                        try:
                            if page.locator(loc).first.count() > 0:
                                page.locator(loc).first.click(timeout=3000, force=True)
                                p_log(profile_name, f"[{profile_name}] Đã click mở hộp thoại: {loc}")
                                time.sleep(3)
                                break
                        except Exception:
                            pass
                
                dialog = page.locator('div[role="dialog"]').first
                container = dialog if dialog.count() > 0 else page

            # Tải file lên (ảnh hoặc video)
            upload_success = False
            
            # --- CÁCH 1: Tìm và set files trực tiếp lên input file hiện có ---
            p_log(profile_name, f"[{profile_name}] Thử tìm input[type=file] có sẵn...")
            for frame in [page] + page.frames:
                try:
                    file_inputs = frame.locator('input[type="file"]').all()
                    for inp in file_inputs:
                        try:
                            inp.set_input_files(image_path, timeout=3000)
                            p_log(profile_name, f"[{profile_name}] ✅ Đã set_input_files trực tiếp thành công trên input có sẵn!")
                            upload_success = True
                            break
                        except Exception:
                            pass
                    if upload_success:
                        break
                except Exception:
                    pass

            # --- CÁCH 2: Tìm nút upload (anh/video) và click + bắt File Chooser ---
            add_photo_btn = None
            if not upload_success:
                try:
                    p_log(profile_name, f"[{profile_name}] Tìm nút upload ảnh/video...")
                    add_photo_locators = [
                        'text="Thêm ảnh"', 'text="Add photo"', 'text="Add Photo"',
                        'text="Thêm video"', 'text="Add video"', 'text="Add Video"',
                        'div[aria-label*="Chọn thêm ảnh"]',
                        'div[aria-label*="Chọn ảnh"]',
                        'div[aria-label*="photo"]', 'div[aria-label*="Photo"]', 'div[aria-label*="ảnh"]', 'div[aria-label*="Ảnh"]',
                        'div[aria-label*="video"]', 'div[aria-label*="Video"]',
                        'span:has-text("Add photo")', 'span:has-text("Thêm ảnh")',
                        'span:has-text("Add video")', 'span:has-text("Thêm video")',
                        'div:has-text("Photo/video")', 'div:has-text("Ảnh/video")',
                        'div[role="button"]:has-text("Thêm ảnh")', 'div[role="button"]:has-text("Add photo")',
                        'div[role="button"]:has-text("Thêm video")', 'div[role="button"]:has-text("Add video")',
                        'span:has-text("Photo/video")',
                    ]
                    
                    # Tìm nút với retry 15 giây (doi trang load du)
                    search_start = time.time()
                    while time.time() - search_start < 15 and not add_photo_btn:
                        for loc in add_photo_locators:
                            for search_scope in [container, page]:
                                try:
                                    loc_obj = search_scope.locator(loc)
                                    if loc_obj.count() > 0:
                                        add_photo_btn = loc_obj.last
                                        break
                                except:
                                    pass
                            if add_photo_btn:
                                break
                        if not add_photo_btn:
                            time.sleep(1)
                    
                    if add_photo_btn and add_photo_btn.count() > 0:
                        p_log(profile_name, f"[{profile_name}] Đang click nút upload và bắt File Chooser...")
                        try:
                            with page.expect_file_chooser(timeout=5000) as fc_info:
                                try:
                                    add_photo_btn.click(timeout=3000)
                                except Exception:
                                    try:
                                        add_photo_btn.click(timeout=3000, force=True)
                                    except Exception:
                                        add_photo_btn.dispatch_event('click')
                            file_chooser = fc_info.value
                            file_chooser.set_files(image_path)
                            p_log(profile_name, f"[{profile_name}] ✅ Đã tải file lên thành công (qua File Chooser trực tiếp khi click)!")
                            upload_success = True
                        except Exception as fc_err:
                            p_log(profile_name, f"[{profile_name}] File Chooser không kích hoạt ({fc_err}). Kiểm tra input type=file sau click...")
                            time.sleep(2)
                            for frame in [page] + page.frames:
                                try:
                                    file_inputs = frame.locator('input[type="file"]').all()
                                    for inp in file_inputs:
                                        try:
                                            inp.set_input_files(image_path, timeout=3000)
                                            p_log(profile_name, f"[{profile_name}] ✅ Đã set_input_files thành công sau click!")
                                            upload_success = True
                                            break
                                        except Exception:
                                            pass
                                    if upload_success:
                                        break
                                except Exception:
                                    pass
                    else:
                        p_log(profile_name, f"[{profile_name}] Không tìm thấy nút Thêm ảnh/video sau 15 giây.")
                except Exception as btn_err:
                    p_log(profile_name, f"[{profile_name}] Warning: Lỗi khi thao tác với nút upload: {btn_err}")

            # --- CÁCH 3: Chờ menu item "Tải lên từ máy tính" ---
            if not upload_success:
                try:
                    menu_item_locators = [
                        'text="Tải lên từ máy tính"',
                        'text="Upload from desktop"',
                        'text="Upload from computer"',
                        'div:has-text("Tải lên từ máy tính")',
                        'div:has-text("Upload from desktop")',
                        'span:has-text("Tải lên từ máy tính")',
                        'span:has-text("Upload from desktop")'
                    ]
                    
                    active_menu_item = None
                    start_w = time.time()
                    while time.time() - start_w < 5:
                        for loc in menu_item_locators:
                            loc_obj = page.locator(loc)
                            if loc_obj.count() > 0:
                                active_menu_item = loc_obj.last
                                break
                        if active_menu_item:
                            break
                        time.sleep(0.5)
                    
                    if active_menu_item:
                        p_log(profile_name, f"[{profile_name}] Tìm thấy menu item upload. Đang click...")
                        with page.expect_file_chooser(timeout=5000) as fc_info:
                            active_menu_item.click(force=True)
                        file_chooser = fc_info.value
                        file_chooser.set_files(image_path)
                        p_log(profile_name, f"[{profile_name}] ✅ Đã tải file lên thành công (qua Menu & File Chooser)!")
                        upload_success = True
                except Exception as menu_err:
                    p_log(profile_name, f"[{profile_name}] Warning: Lỗi khi upload qua Menu: {menu_err}")

            # --- CÁCH 4: Click lại nút upload (chỉ khi tìm được) ---
            if not upload_success and add_photo_btn is not None:
                try:
                    p_log(profile_name, f"[{profile_name}] Thử expect_file_chooser lần 2...")
                    with page.expect_file_chooser(timeout=5000) as fc_info:
                        add_photo_btn.click(force=True)
                    file_chooser = fc_info.value
                    file_chooser.set_files(image_path)
                    p_log(profile_name, f"[{profile_name}] ✅ Đã tải file lên thành công (lần 2)!")
                    upload_success = True
                except Exception as fc_err:
                    p_log(profile_name, f"[{profile_name}] Warning: Lỗi file chooser lần 2: {fc_err}")

            if not upload_success:
                raise Exception("Không tìm thấy thẻ input[type=file] nào hoặc tất cả cách tải file đều thất bại.")
            
            time.sleep(3)
            
            # Ghi Text va Bam dang (Phan biet anh & video)
            is_video = False
            if image_path:
                ext = os.path.splitext(image_path)[1].lower()
                if ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv']:
                    is_video = True
                    p_log(profile_name, f"[{profile_name}] Phat hien file dang la VIDEO ({ext}). Ap dung luong dang video rieng.")

            if is_video:
                # === LUỒNG ĐĂNG VIDEO ===
                # Chờ giao diện chỉnh sửa video xuất hiện
                p_log(profile_name, f"[{profile_name}] Dang cho giao dien thiet lap video xuat hien...")
                time.sleep(5)
                
                # 1. Nhập Tiêu đề Video (Bắt buộc)
                try:
                    title_selectors = [
                        'input[placeholder*="tiêu đề"]',
                        'input[placeholder*="Title"]',
                        'input[placeholder*="title"]',
                        'input[aria-label*="tiêu đề"]',
                        'input[aria-label*="title"]',
                        'input[type="text"]'
                    ]
                    title_box = None
                    for frame in [page] + page.frames:
                        for sel in title_selectors:
                            try:
                                loc = frame.locator(sel).first
                                if loc.count() > 0 and loc.is_visible():
                                    title_box = loc
                                    break
                            except: pass
                        if title_box: break
                    
                    if title_box:
                        # Lấy tiêu đề từ 50 ký tự đầu của status_text (bỏ hashtag)
                        video_title = status_text.split('\n')[0]
                        video_title = re.sub(r'#\w+', '', video_title).strip()
                        if not video_title:
                            video_title = "New Video Post"
                        video_title = video_title[:45]
                        
                        title_box.click(force=True)
                        title_box.fill(video_title)
                        p_log(profile_name, f"[{profile_name}] Da nhap tieu de video: '{video_title}'")
                    else:
                        p_log(profile_name, f"[{profile_name}] Warning: Khong tim thay o nhap tieu de video.")
                except Exception as title_err:
                    p_log(profile_name, f"[{profile_name}] Loi khi nhap tieu de video: {title_err}")

                # 2. Nhập Mô tả Video (Nội dung status)
                try:
                    desc_selectors = [
                        'div[role="textbox"]',
                        'div[role="combobox"][contenteditable="true"]',
                        'textarea',
                        'div[aria-label*="mô tả"]',
                        'div[aria-label*="description"]'
                    ]
                    desc_box = None
                    for frame in [page] + page.frames:
                        for sel in desc_selectors:
                            try:
                                # Tránh lấy trùng với title_box ở trên
                                loc = frame.locator(sel).first
                                if loc.count() > 0 and loc.is_visible() and loc.get_attribute("type") != "text":
                                    desc_box = loc
                                    break
                            except: pass
                        if desc_box: break
                    
                    if desc_box:
                        desc_box.click(force=True)
                        time.sleep(0.5)
                        
                        paste_ok = False
                        try:
                            import pyperclip
                            pyperclip.copy(status_text)
                            desc_box.focus()
                            page.keyboard.press("Control+A")
                            page.keyboard.press("Control+V")
                            time.sleep(1)
                            paste_ok = True
                            p_log(profile_name, f"[{profile_name}] Da paste mo ta video bang pyperclip.")
                        except Exception as clip_err:
                            p_log(profile_name, f"[{profile_name}] pyperclip that bai ({clip_err}), thu JS clipboard...")
                            
                        if not paste_ok:
                            try:
                                page.evaluate(f"""
                                    navigator.clipboard.writeText({repr(status_text)}).catch(() => {{
                                        const el = document.createElement('textarea');
                                        el.value = {repr(status_text)};
                                        document.body.appendChild(el);
                                        el.select();
                                        document.execCommand('copy');
                                        document.body.removeChild(el);
                                    }});
                                """)
                                desc_box.focus()
                                page.keyboard.press("Control+A")
                                page.keyboard.press("Control+V")
                                time.sleep(1)
                                paste_ok = True
                                p_log(profile_name, f"[{profile_name}] Da paste mo ta video bang JS clipboard.")
                            except Exception as js_err:
                                p_log(profile_name, f"[{profile_name}] JS clipboard that bai: {js_err}")
                                
                        if not paste_ok:
                            desc_box.fill(status_text)
                            p_log(profile_name, f"[{profile_name}] Da dien mo ta bang fill().")
                    else:
                        p_log(profile_name, f"[{profile_name}] Warning: Khong tim thay o nhap mo ta video.")
                except Exception as desc_err:
                    p_log(profile_name, f"[{profile_name}] Loi nhap mo ta video: {desc_err}")

                # 3. Click qua các bước wizard (Next -> Next -> Share/Publish)
                # Facebook Suite video post thường có 3 bước. Ta click "Tiếp" cho đến khi thấy nút "Chia sẻ" hoặc "Đăng"
                next_btn_selectors = [
                    'div[role="button"]:has-text("Tiếp")',
                    'div[role="button"]:has-text("Next")',
                    'button:has-text("Tiếp tục")',
                    'button:has-text("Next")',
                    'span:has-text("Tiếp tục")',
                    'span:has-text("Next")',
                    'div[role="button"]:has-text("Đăng")',
                    'div[role="button"]:has-text("Chia sẻ")',
                    'div[role="button"]:has-text("Publish")',
                    'div[role="button"]:has-text("Share")',
                    'button:has-text("Đăng")',
                    'button:has-text("Chia sẻ")',
                    'button:has-text("Publish")',
                    'button:has-text("Share")'
                ]
                
                p_log(profile_name, f"[{profile_name}] Bat dau click tiep tuc de Dang video...")
                for step in range(1, 4):
                    time.sleep(3)
                    
                    if not publish and step == 3:
                        p_log(profile_name, f"[{profile_name}] 🧪 [TEST MODE] Đã upload và điền mô tả thành công. Dừng lại ở bước chia sẻ cuối cùng (không bấm Đăng/Publish).")
                        time.sleep(15)
                        break
                        
                    next_btn = None
                    for frame in [page] + page.frames:
                        for sel in next_btn_selectors:
                            try:
                                loc = frame.locator(sel).first
                                if loc.count() > 0 and loc.is_visible() and loc.is_enabled():
                                    next_btn = loc
                                    break
                            except: pass
                        if next_btn: break
                        
                    if next_btn:
                        btn_text = next_btn.inner_text().strip()
                        p_log(profile_name, f"[{profile_name}] Step {step}: Click nut '{btn_text}'")
                        try:
                            next_btn.click(force=True, timeout=5000)
                        except:
                            next_btn.dispatch_event('click')
                    else:
                        p_log(profile_name, f"[{profile_name}] Step {step}: Khong tim thay nut tiep tuc/dang, co the da hoan tat.")
                        break
                        
                p_log(profile_name, f"[{profile_name}] Da click nut Dang bài video thanh cong len Fanpage!")
                
            else:
                # === LUỒNG ĐĂNG ẢNH / TEXT THƯỜNG ===
                # Ghi Text
                try:
                    textbox_selectors = [
                        'div[role="combobox"][contenteditable="true"]',
                        'div[aria-label*="viết"]',
                        'div[aria-label*="write"]',
                        'div[aria-label*="nghĩ"]',
                        'div[aria-label*="mind"]'
                    ]
                    textbox = None
                    start_w = time.time()
                    while time.time() - start_w < 15:
                        for frame in [page] + page.frames:
                            for sel in textbox_selectors:
                                try:
                                    loc = frame.locator(sel).first
                                    if loc.count() > 0 and loc.is_visible():
                                        textbox = loc
                                        break
                                except:
                                    pass
                            if textbox:
                                break
                        if textbox:
                            break
                        time.sleep(1)
                        
                    if not textbox:
                        raise Exception("Không tìm thấy ô nhập trạng thái (textbox) trên cả container lẫn page sau 15 giây.")
                    
                    textbox.click(force=True)
                    time.sleep(0.5)
                    
                    paste_ok = False
                    try:
                        import pyperclip
                        pyperclip.copy(status_text)
                        textbox.focus()
                        page.keyboard.press("Control+A")
                        page.keyboard.press("Control+V")
                        time.sleep(1)
                        paste_ok = True
                        p_log(profile_name, f"[{profile_name}] Da paste text bang pyperclip clipboard.")
                    except Exception as clip_err:
                        p_log(profile_name, f"[{profile_name}] pyperclip khong dung duoc ({clip_err}), thu JS clipboard...")
                    
                    if not paste_ok:
                        try:
                            page.evaluate(f"""
                                navigator.clipboard.writeText({repr(status_text)}).catch(() => {{
                                    const el = document.createElement('textarea');
                                    el.value = {repr(status_text)};
                                    document.body.appendChild(el);
                                    el.select();
                                    document.execCommand('copy');
                                    document.body.removeChild(el);
                                }});
                            """)
                            textbox.focus()
                            page.keyboard.press("Control+A")
                            page.keyboard.press("Control+V")
                            time.sleep(1)
                            paste_ok = True
                            p_log(profile_name, f"[{profile_name}] Da paste text bang JS clipboard.")
                        except Exception as js_err:
                            p_log(profile_name, f"[{profile_name}] JS clipboard khong hoat dong ({js_err}), thu type nho...")
                    
                    if not paste_ok:
                        try:
                            textbox.focus()
                            page.evaluate(f"""
                                const el = document.querySelector('div[role="combobox"][contenteditable="true"]');
                                if (el) {{
                                    el.focus();
                                    el.innerText = {repr(status_text)};
                                    el.dispatchEvent(new InputEvent('input', {{bubbles: true}}));
                                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                                }}
                            """)
                            time.sleep(1)
                            paste_ok = True
                            p_log(profile_name, f"[{profile_name}] Da set text bang JS innerText.")
                        except Exception as js2_err:
                            p_log(profile_name, f"[{profile_name}] JS innerText that bai ({js2_err}). Thu press_sequentially ngan...")
                    
                    if not paste_ok:
                        textbox.press_sequentially(status_text[:500], delay=5)
                        p_log(profile_name, f"[{profile_name}] Da nhap text (500 ki tu) bang press_sequentially.")
                    
                    p_log(profile_name, f"[{profile_name}] Da nhap trang thai len FB thanh cong.")
                except Exception as e:
                    p_log(profile_name, f"[{profile_name}] Lỗi nhập text FB: {e}")
                    raise Exception(f"Không thể gõ text trạng thái lên FB: {e}")
                    
                time.sleep(5)
                
                # Bấm nút Đăng
                if not publish:
                    p_log(profile_name, f"[{profile_name}] 🧪 [TEST MODE] Đã upload và điền status thành công. Dừng lại ở bước cuối cùng (không bấm Đăng/Publish).")
                    time.sleep(15)
                else:
                    try:
                        post_btn_selectors = [
                            'div[role="button"]:has-text("Đăng")',
                            'div[role="button"]:has-text("Post")',
                            'div[role="button"]:has-text("Chia sẻ")',
                            'div[role="button"]:has-text("Share")',
                            'div[role="button"]:has-text("Publish")',
                            'button:has-text("Đăng")',
                            'button:has-text("Post")',
                            'button:has-text("Chia sẻ")',
                            'button:has-text("Share")',
                            'button:has-text("Publish")',
                            '[data-testid*="publish"]',
                            '[data-testid*="share"]'
                        ]
                        post_btn = None
                        start_w = time.time()
                        while time.time() - start_w < 15:
                            for frame in [page] + page.frames:
                                for sel in post_btn_selectors:
                                    try:
                                        loc = frame.locator(sel).first
                                        if loc.count() > 0 and loc.is_visible():
                                            post_btn = loc
                                            break
                                    except:
                                        pass
                                if post_btn:
                                    break
                            if post_btn:
                                break
                            time.sleep(1)
                            
                        if not post_btn:
                            raise Exception("Không tìm thấy nút Đăng/Post trên cả container lẫn page sau 15 giây.")
                        
                        try:
                            post_btn.click(force=True, timeout=5000)
                        except:
                            post_btn.dispatch_event('click')
                        p_log(profile_name, f"[{profile_name}] Đã click nút Đăng bài thành công lên Fanpage!")
                    except Exception as e:
                        if "Target page, context or browser has been closed" in str(e) or "Execution context was destroyed" in str(e):
                            p_log(profile_name, f"[{profile_name}] Báo lỗi chuyển hướng sau khi Đăng. Cứ xem như Đăng thành công!")
                        else:
                            p_log(profile_name, f"[{profile_name}] Lỗi khi bấm nút Đăng: {e}")
                            raise Exception(f"Không thể ấn nút Đăng bài trên FB: {e}")

            # Đợi quá trình đăng hoàn tất (video cần chờ lâu hơn để upload xong)
            wait_time = 45 if is_video else 15
            p_log(profile_name, f"[{profile_name}] Dang cho {wait_time} giay de hoan tat dang bai...")
            time.sleep(wait_time)
            
            # --- Dọn dẹp file AI đã tạo sau khi đăng thành công ---
            if cleanup:
                self._cleanup_output_files(profile_name, text_path, image_path)
            
            return True
            
        except Exception as e:
            p_log(profile_name, f"[{profile_name}] Lỗi khi đăng bài Fanpage: {str(e)}")
            raise e
        finally:
            if is_new_page:
                try:
                    page.close()
                except:
                    pass

    def _cleanup_output_files(self, profile_name, text_path, image_path):
        """
        Xóa file ảnh AI và text đã đăng để giải phóng dung lượng.
        TUYỆT ĐỐI không xóa file nằm trong thư mục input.
        """
        # Tập hợp tất cả tên thư mục bị cấm xóa - không xóa ảnh đầu vào gốc
        PROTECTED_DIRS = ["input_images", "input_image", "profiles", "static", "templates", "venv", "core"]
        
        # Lấy cấu hình profile từ DB để biết chính xác thư mục input/output
        try:
            profile_cfg = db_manager.get_profile_config(profile_name)
        except Exception as e:
            p_log(profile_name, f"[{profile_name}] Warning: Không thể đọc cấu hình để check thư mục bảo vệ: {e}")
            profile_cfg = {}
            
        input_img_dir = os.path.abspath(profile_cfg.get("input_img_dir", "").strip()).lower() if profile_cfg.get("input_img_dir") else ""
        output_txt_dir = os.path.abspath(profile_cfg.get("output_txt_dir", "").strip()).lower() if profile_cfg.get("output_txt_dir") else ""
        output_img_dir = os.path.abspath(profile_cfg.get("output_img_dir", "").strip()).lower() if profile_cfg.get("output_img_dir") else ""
        
        for filepath in [text_path, image_path]:
            if not filepath:
                continue
            try:
                abs_path = os.path.abspath(filepath)
                abs_path_lower = abs_path.lower()
                
                # 1. Kiểm tra các thư mục hệ thống / code bị cấm xóa
                path_parts = abs_path.replace("\\", "/").split("/")
                if any(part.lower() in PROTECTED_DIRS for part in path_parts):
                    p_log(profile_name, f"[{profile_name}] Thư mục hệ thống/chương trình bị bảo vệ, không xóa: {filepath}")
                    continue
                    
                # 2. Tuyệt đối không xóa nếu nằm trong thư mục input đầu vào
                if input_img_dir and abs_path_lower.startswith(input_img_dir):
                    p_log(profile_name, f"[{profile_name}] Ảnh gốc (input) bị bảo vệ, không xóa: {filepath}")
                    continue
                    
                # 3. Chỉ xóa nếu nằm trong thư mục output (txt hoặc img) đã cấu hình
                in_output = False
                if output_txt_dir and abs_path_lower.startswith(output_txt_dir):
                    in_output = True
                if output_img_dir and abs_path_lower.startswith(output_img_dir):
                    in_output = True
                    
                if not in_output:
                    p_log(profile_name, f"[{profile_name}] File không nằm trong thư mục output đã cấu hình, không xóa: {filepath}")
                    continue
                    
                # Thực hiện xóa
                if os.path.exists(abs_path):
                    os.remove(abs_path)
                    p_log(profile_name, f"[{profile_name}] ✅ Đã xóa file tạm: {os.path.basename(abs_path)}")
            except Exception as e:
                p_log(profile_name, f"[{profile_name}] Không thể xóa file {filepath}: {e}")
