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
    def post_to_fanpage(self, profile_name, text_path, image_path):
        """
        Tự động hóa đăng bài lên Facebook Fanpage.
        """
        if not text_path or not image_path:
            p_log(profile_name, f"[{profile_name}] Thiếu thông tin ảnh/text để đăng bài.")
            return False

        with open(text_path, "r", encoding="utf-8") as f:
            status_text = f.read()

        is_new_page = False
        if self.context.pages:
            page = self.context.pages[0]
        else:
            page = self.context.new_page()
            is_new_page = True
        try:
            p_log(profile_name, f"[{profile_name}] Đang truy cập Fanpage: {self.fanpage_url}")
            page.goto(self.fanpage_url, wait_until="domcontentloaded")
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

            # Tải ảnh lên
            upload_success = False
            
            # --- CÁCH 1: Tìm và set files trực tiếp lên input file hiện có (trang / tất cả các frames) ---
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

            # --- CÁCH 2: Nếu chưa được, click nút Thêm ảnh để kích hoạt và tìm input / file chooser ---
            if not upload_success:
                try:
                    p_log(profile_name, f"[{profile_name}] Tìm nút upload ảnh gốc...")
                    add_photo_locators = [
                        'text="Thêm ảnh"', 'text="Add photo"', 'text="Add Photo"',
                        'div[aria-label*="photo"]', 'div[aria-label*="Photo"]', 'div[aria-label*="ảnh"]', 'div[aria-label*="Ảnh"]', 
                        'span:has-text("Add photo")', 'span:has-text("Thêm ảnh")', 
                        'div:has-text("Photo/video")', 'div:has-text("Ảnh/video")'
                    ]
                    
                    add_photo_btn = None
                    for loc in add_photo_locators:
                        loc_obj = container.locator(loc)
                        if loc_obj.count() > 0:
                            add_photo_btn = loc_obj.last
                            break
                            
                    if not add_photo_btn:
                        add_photo_btn = container.locator("text='Thêm ảnh'").last
                    
                    p_log(profile_name, f"[{profile_name}] Đang click nút Thêm ảnh...")
                    try:
                        add_photo_btn.click(timeout=5000)
                    except Exception as click_err:
                        p_log(profile_name, f"[{profile_name}] Click thường nút Thêm ảnh thất bại, thử click force...")
                        try:
                            add_photo_btn.click(timeout=3000, force=True)
                        except Exception as click_err2:
                            p_log(profile_name, f"[{profile_name}] Click force nút Thêm ảnh thất bại, thử dispatch event...")
                            try:
                                add_photo_btn.dispatch_event('click')
                            except:
                                pass
                    
                    time.sleep(2) # Chờ xíu cho DOM sinh ra input mới
                    
                    # Thử quét tất cả các input file trong page và các frames sau khi click nút Thêm ảnh
                    for frame in [page] + page.frames:
                        try:
                            file_inputs = frame.locator('input[type="file"]').all()
                            for inp in file_inputs:
                                try:
                                    inp.set_input_files(image_path, timeout=3000)
                                    p_log(profile_name, f"[{profile_name}] ✅ Đã set_input_files thành công sau khi click nút Thêm ảnh!")
                                    upload_success = True
                                    break
                                except Exception:
                                    pass
                            if upload_success:
                                break
                        except Exception:
                            pass
                            
                except Exception as btn_err:
                    p_log(profile_name, f"[{profile_name}] Warning: Lỗi khi thao tác với nút Thêm ảnh: {btn_err}")

            # --- CÁCH 3: Chờ menu item hiển thị và mở File Chooser (phù hợp với một số giao diện cũ) ---
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
                        p_log(profile_name, f"[{profile_name}] Tìm thấy menu item của upload. Đang click để mở File Chooser...")
                        with page.expect_file_chooser(timeout=5000) as fc_info:
                            active_menu_item.click(force=True)
                        file_chooser = fc_info.value
                        file_chooser.set_files(image_path)
                        p_log(profile_name, f"[{profile_name}] ✅ Đã tải ảnh lên thành công (qua Menu & File Chooser)!")
                        upload_success = True
                except Exception as menu_err:
                    p_log(profile_name, f"[{profile_name}] Warning: Lỗi khi upload qua Menu: {menu_err}")

            # --- CÁCH 4: Click nút Thêm ảnh một lần nữa bằng expect_file_chooser ---
            if not upload_success:
                try:
                    p_log(profile_name, f"[{profile_name}] Thử expect_file_chooser trực tiếp bằng cách click lại nút Thêm ảnh...")
                    with page.expect_file_chooser(timeout=5000) as fc_info:
                        add_photo_btn.click(force=True)
                    file_chooser = fc_info.value
                    file_chooser.set_files(image_path)
                    p_log(profile_name, f"[{profile_name}] ✅ Đã tải ảnh lên thành công (qua expect_file_chooser trực tiếp)!")
                    upload_success = True
                except Exception as fc_err:
                    p_log(profile_name, f"[{profile_name}] Warning: Lỗi expect_file_chooser trực tiếp: {fc_err}")

            if not upload_success:
                raise Exception("Không tìm thấy thẻ input[type=file] nào trong container lẫn toàn trang page (bao gồm cả các iframes) hoặc tất cả cách tải ảnh đều thất bại.")
                
            time.sleep(3)
            
            # Ghi Text
            try:
                textbox = container.locator('div[role="combobox"][contenteditable="true"], div[aria-label*="viết"], div[aria-label*="write"], div[aria-label*="nghĩ"], div[aria-label*="mind"]').first
                textbox.click(force=True)
                textbox.press_sequentially(status_text, delay=20)
                p_log(profile_name, f"[{profile_name}] Đã nhập trạng thái từng chữ.")
            except Exception as e:
                p_log(profile_name, f"[{profile_name}] Lỗi nhập text FB: {e}")
                raise Exception(f"Không thể gõ text trạng thái lên FB: {e}")
                
            time.sleep(5)
            
            # Bấm nút Đăng
            try:
                post_btn = container.locator('div[role="button"]:has-text("Đăng"), div[role="button"]:has-text("Post"), button:has-text("Đăng"), button:has-text("Post")').first
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
                
            time.sleep(15) # Đợi quá trình đăng hoàn tất
            
            # --- Dọn dẹp file AI đã tạo sau khi đăng thành công ---
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
