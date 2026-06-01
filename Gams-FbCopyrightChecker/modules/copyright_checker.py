"""
Kiểm tra và xử lý khiếu nại bản quyền qua trang Support/Appeals của Facebook.
Hỗ trợ cả profile cá nhân và switch sang từng fanpage.
Tích hợp AI agent pipeline: perceive → decide → act → memory.
"""
import time
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, InvalidSessionIdException, TimeoutException

from modules.database import Database
from modules import bug_tracker
from modules.logger import get_logger

from modules.config_loader import CONFIG

log = get_logger(__name__)

APPEALS_URL = "https://www.facebook.com/support/?tab_type=APPEALS"
SUPPORT_URL  = "https://www.facebook.com/support/"


# ─────────────────────────────────────────────
# Chrome crash detection & recovery
# ─────────────────────────────────────────────

def _is_chrome_dead(driver: webdriver.Chrome) -> bool:
    """Kiểm tra xem Chrome session có còn sống không."""
    try:
        _ = driver.current_url
        return False
    except Exception:
        return True


def _is_chrome_error(exc: Exception) -> bool:
    """Trả về True nếu exception là do Chrome bị tắt/crash/disconnect/connection reset."""
    err_str = str(exc).lower()
    return (
        isinstance(exc, (InvalidSessionIdException, WebDriverException))
        or "invalid session id" in err_str
        or "chrome not reachable" in err_str
        or "max retries exceeded" in err_str
        or "connection refused" in err_str
        or "httpsconnectionpool" in err_str
        or "httpconnectionpool" in err_str
        or "failed to establish a new connection" in err_str
        or "no connection could be made" in err_str
        or "target window already closed" in err_str
        or "disconnected" in err_str
        or "connectionreseterror" in err_str
        or "connection aborted" in err_str
        or "connection reset" in err_str
        or "10054" in err_str
        or "forcibly closed" in err_str
        or "protocolerror" in err_str
    )


def rebuild_driver(old_driver: webdriver.Chrome, profile_dir: str = None) -> webdriver.Chrome:
    """
    Đóng Chrome cũ (nếu còn) và khởi tạo lại Chrome mới đúng profile của tool.
    Trả về driver mới đã sẵn sàng.
    """
    from agent.chrome_manager import ensure_profile_closed
    from modules.fb_login import build_driver, login

    log.warning("Chrome bị tắt/crash — đang khởi động lại...")

    # Đóng driver cũ (best-effort)
    try:
        old_driver.quit()
    except Exception:
        pass

    # Đóng Chrome process đang dùng profile này (nếu còn zombie)
    if profile_dir:
        try:
            ensure_profile_closed(profile_dir)
        except Exception as e:
            log.debug(f"ensure_profile_closed (rebuild): {e}")

    # Khởi động Chrome mới
    new_driver = build_driver(profile_dir=profile_dir)
    log.info("Chrome mới đã khởi động — đang đăng nhập lại...")

    if not login(new_driver):
        log.error("Đăng nhập lại thất bại sau khi rebuild Chrome")
        return new_driver  # trả về dù thất bại — caller quyết định tiếp

    log.info("Đăng nhập lại thành công — tiếp tục quét.")
    return new_driver


# ─────────────────────────────────────────────
# Switch context (profile → fanpage → profile)
# ─────────────────────────────────────────────

def switch_context_via_menu(driver: webdriver.Chrome, target_name: str) -> bool:
    """
    Chuyển đổi context (profile cá nhân hoặc fanpage) bằng menu góc trên bên phải.
    """
    if not target_name:
        return False
    try:
        log.info(f"Bắt đầu chuyển context sang '{target_name}' qua menu...")
        
        # Đảm bảo đang ở trang chủ Facebook (vì trang Support không có menu chuyển Fanpage)
        current_url = driver.current_url
        if "facebook.com" not in current_url or "facebook.com/support" in current_url:
            driver.get("https://www.facebook.com/")
            time.sleep(2)
            
        # 1. Click Avatar góc trên cùng bên phải
        avatar_xpath = (
            "//div[@role='banner']//div[@role='button'][img]"
            "|//div[contains(@aria-label, 'Your profile') or contains(@aria-label, 'Trang cá nhân') or contains(@aria-label, 'Account')]"
        )
        avatar = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, avatar_xpath))
        )
        driver.execute_script("arguments[0].click();", avatar)
        
        # 2. Click "Xem tất cả trang cá nhân" / "See all profiles"
        see_all_xpath = (
            "//*[contains(text(), 'Xem tất cả trang cá nhân') or contains(text(), 'See all profiles') or contains(text(), 'See all Profiles')]"
        )
        see_all_btn = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, see_all_xpath))
        )
        driver.execute_script("arguments[0].click();", see_all_btn)
        
        # 3. Chờ danh sách các button xuất hiện
        buttons_xpath = "//div[@role='dialog' or @role='menu']//div[@role='button'][.//span]"
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.XPATH, buttons_xpath))
        )
        
        # 3.1 Gõ vào ô tìm kiếm (nếu có) để lọc fanpage (trường hợp user quản lý quá nhiều fanpage)
        try:
            search_input = driver.find_element(By.XPATH, "//div[@role='dialog' or @role='menu']//input[contains(@placeholder, 'Tìm kiếm') or contains(@placeholder, 'Search')]")
            driver.execute_script("arguments[0].focus();", search_input)
            search_input.clear()
            search_input.send_keys(target_name)
            # Kích hoạt sự kiện React để FB nhận diện chữ vừa gõ
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", search_input)
            time.sleep(1.5) # Chờ kết quả search render
        except Exception:
            pass
        
        # 4. Tìm và click dòng có tên target_name (Chờ kết quả search render trong tối đa 8 giây)
        target_btn = None
        for _ in range(8):
            if _is_chrome_dead(driver):
                raise WebDriverException("Chrome is dead or disconnected")
            
            script = """
            var targetName = arguments[0].toLowerCase();
            var xpath = "//div[@role='dialog' or @role='menu']//div[@role='button' or @role='link'][.//span]";
            var query = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
            for (var i = 0; i < query.snapshotLength; i++) {
                var el = query.snapshotItem(i);
                var name = el.textContent.trim().toLowerCase();
                if (name && name.indexOf(targetName) !== -1) {
                    return el;
                }
            }
            return null;
            """
            try:
                target_btn = driver.execute_script(script, target_name)
            except Exception as e:
                if _is_chrome_error(e):
                    raise e
                target_btn = None
                
            if target_btn:
                break
            time.sleep(1)
            
        if target_btn:
            driver.execute_script("arguments[0].click();", target_btn)
            log.info(f"Đã click chuyển sang: {target_name}")
            
            # Chờ quá trình chuyển đổi (thường hiển thị màn hình chờ hoặc reload)
            time.sleep(1.5)
            
            # Chờ trang chủ Facebook hoặc trang mới load xong
            WebDriverWait(driver, 15).until(
                lambda d: d.find_elements(By.CSS_SELECTOR, "[aria-label='Facebook'][role='navigation'], [data-pagelet='LeftRail'], [aria-label='Your profile']")
            )
            log.info(f"Chuyển context sang '{target_name}' thành công.")
            bug_tracker.clear_bug("copyright_checker", "switch_context_via_menu")
            return True
        else:
            log.warning(f"Không tìm thấy nút cho '{target_name}' trong menu.")
            bug_tracker.clear_bug("copyright_checker", "switch_context_via_menu")
            return False
    except Exception as e:
        if _is_chrome_error(e):
            raise e
        log.error(f"Lỗi chuyển context sang '{target_name}' qua menu: {e}")
        bug_tracker.log_bug("copyright_checker", "switch_context_via_menu", e)
        return False


def switch_to_page(driver: webdriver.Chrome, page_url: str, page_name: str = "") -> bool:
    """
    Switch sang fanpage bằng cách dùng menu hoặc truy cập URL trực tiếp.
    """
    name_from_url = ""
    if page_url.startswith("#name="):
        name_from_url = page_url.split("=", 1)[1]
    
    target_name = page_name or name_from_url
    
    if target_name:
        # Ưu tiên switch qua menu
        ok = switch_context_via_menu(driver, target_name)
        if ok:
            bug_tracker.clear_bug("copyright_checker", "switch_to_page")
            return True
            
    # Fallback hoặc nếu dùng URL truyền thống
    if page_url and not page_url.startswith("#"):
        try:
            # Thử get page_url tối đa 3 lần nếu gặp TimeoutException
            for attempt in range(1, 4):
                try:
                    driver.get(page_url)
                    break
                except TimeoutException as e:
                    if attempt == 3:
                        raise
                    log.warning(f"Timeout khi tải trang page {page_url} (lần {attempt}/3), đang thử lại...")
                    time.sleep(2)
            # Chờ trang load
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH, "//*"))
            )
            # Thử click nút "Switch Now" / "Chuyển ngay" trên trang (tăng thời gian chờ và sửa XPATH)
            try:
                switch_xpath = (
                    "//div[@role='button'][contains(.,'Switch to Page') or contains(.,'Chuyển sang trang') or contains(.,'Switch Now') or contains(.,'Chuyển ngay')]"
                    " | //*[contains(text(),'Switch to Page') or contains(text(),'Chuyển sang trang') or contains(text(),'Switch Now') or contains(text(),'Chuyển ngay')]"
                )
                btn = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.XPATH, switch_xpath))
                )
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
                log.info(f"Đã click nút Switch Now trên trang cho {page_url}")
                bug_tracker.clear_bug("copyright_checker", "switch_to_page")
                return True
            except Exception:
                pass
            
            # Nếu không tìm thấy nút Switch Now trên trang, thử switch bằng tên page lấy từ Title trang
            title = driver.title
            if title and "facebook" not in title.lower():
                ok = switch_context_via_menu(driver, title.strip())
                if ok:
                    bug_tracker.clear_bug("copyright_checker", "switch_to_page")
                    return True
            bug_tracker.clear_bug("copyright_checker", "switch_to_page")
        except Exception as e:
            if _is_chrome_error(e):
                raise e
            log.error(f"Lỗi fallback switch page {page_url}: {e}")
            bug_tracker.log_bug("copyright_checker", "switch_to_page", e)
            
    return False


def switch_to_profile(driver: webdriver.Chrome) -> bool:
    """Quay về profile cá nhân."""
    try:
        driver.get("https://www.facebook.com/")
        
        # Thử tìm nút Quick Switch (Biểu tượng vòng tròn 2 mũi tên bên cạnh Avatar)
        try:
            quick_switch = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='banner']//div[@aria-label='Switch profile' or @aria-label='Chuyển trang cá nhân'] | //div[@role='banner']//div[contains(@aria-label, 'Switch to') or contains(@aria-label, 'Chuyển sang')]"))
            )
            driver.execute_script("arguments[0].click();", quick_switch)
            time.sleep(1)
            return True
        except Exception:
            pass

        profile_name = CONFIG["facebook"].get("profile_name", "")
        if profile_name:
            # Ưu tiên switch qua menu về profile chính
            ok = switch_context_via_menu(driver, profile_name)
            if ok:
                return True
        
        # Fallback click thủ công vào menu
        try:
            avatar_xpath = (
                "//div[@role='banner']//div[@role='button'][img]"
                "|//div[contains(@aria-label, 'Your profile') or contains(@aria-label, 'Trang cá nhân') or contains(@aria-label, 'Account')]"
            )
            avatar = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.XPATH, avatar_xpath))
            )
            driver.execute_script("arguments[0].click();", avatar)
            
            # Click vào "Xem tất cả trang cá nhân"
            see_all_xpath = "//*[contains(text(), 'Xem tất cả trang cá nhân') or contains(text(), 'See all profiles') or contains(text(), 'See all Profiles')]"
            see_all_btn = WebDriverWait(driver, 3).until(
                EC.visibility_of_element_located((By.XPATH, see_all_xpath))
            )
            driver.execute_script("arguments[0].click();", see_all_btn)
            
            # Chọn cái đầu tiên trong danh sách (thường là cá nhân)
            time.sleep(0.5)
            rows = driver.find_elements(By.XPATH, "//div[@role='dialog' or @role='menu']//div[@role='button' or @role='link'][.//span]")
            if rows:
                driver.execute_script("arguments[0].click();", rows[0])
                time.sleep(1.5)
                return True
        except Exception:
            pass

        return False
    except Exception as e:
        if _is_chrome_error(e):
            raise e
        log.error(f"Lỗi switch về profile: {e}")
        return False


# ─────────────────────────────────────────────
# Lấy danh sách vi phạm bản quyền từ Appeals
# ─────────────────────────────────────────────

def get_copyright_appeals(driver: webdriver.Chrome, context_name: str = "profile") -> list[dict]:
    """
    Vào trang Appeals, lấy danh sách bài viết bị vi phạm bản quyền.
    Dùng AI classifier (Tầng 2) nếu API key có sẵn, fallback về keyword.
    Trả về list[{"title", "post_url", "status", "action", "confidence", "decision_id"}]
    """
    from agent.perceive import observe_page, emit_event
    from agent.decide import classify_violation, score_risk
    from agent.memory import get_memory

    mem = get_memory()
    appeals = []
    try:
        # Thử get APPEALS_URL tối đa 3 lần nếu gặp TimeoutException
        for attempt in range(1, 4):
            try:
                driver.get(APPEALS_URL)
                break
            except TimeoutException as e:
                if attempt == 3:
                    raise
                log.warning(f"Timeout khi tải trang Appeals (lần {attempt}/3), đang thử lại...")
                time.sleep(2)
        try:
            # Chờ cho trang Appeals tải xong
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='article'] | //div[contains(@class,'x1qjc9v5')]"))
            )
        except Exception:
            pass

        # Bấm vào "Thông báo của bạn" (Your alerts)
        try:
            if _is_chrome_dead(driver):
                raise WebDriverException("Chrome is dead or disconnected")
            
            click_script = """
            var xpath = "//span | //div[@role='button'] | //div[@role='tab']";
            var query = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
            for (var i = 0; i < query.snapshotLength; i++) {
                var el = query.snapshotItem(i);
                var text = el.textContent.trim().toLowerCase();
                if (text === "thông báo của bạn" || text === "your alerts") {
                    el.click();
                    return true;
                }
            }
            return false;
            """
            clicked = driver.execute_script(click_script)
            if clicked:
                time.sleep(1.5)
        except Exception as e:
            if _is_chrome_error(e):
                raise e
            log.warning("Không thể click tab 'Thông báo của bạn'")

        # Cuộn thông minh: tối đa 10 lần, dừng khi số item ổn định
        _item_xpath = "//div[@role='article'] | //div[contains(@class,'x1qjc9v5')]//div[@data-visualcompletion]"
        prev_count = 0
        for _ in range(10):
            cur_items = driver.find_elements(By.XPATH, _item_xpath)
            if len(cur_items) == prev_count and prev_count > 0:
                break
            prev_count = len(cur_items)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)

        # Quan sát toàn bộ trang Appeals qua AI
        take_ss = CONFIG.get("agent", {}).get("screenshot_on_classify", False)
        obs = observe_page(driver, take_screenshot=take_ss)
        obs.page_type = "appeals"

        # Phân loại trang tổng thể bằng Claude
        page_decision = classify_violation(obs)
        emit_event("appeals_page_classified", {
            "context": context_name,
            "method": page_decision.method,
            "is_violation": page_decision.is_violation,
            "confidence": page_decision.confidence,
        })

        # Tìm các item vi phạm
        items = driver.find_elements(
            By.XPATH,
            "//div[@role='article'] | //div[contains(@class,'x1qjc9v5')]//div[@data-visualcompletion] | //a[contains(@href, '/support/?item_id=')]"
        )

        copyright_keywords = [
            "copyright", "bản quyền", "intellectual property", "quyền sở hữu trí tuệ",
            "dmca", "rights manager", "content removed", "nội dung bị xóa", 
            "vi phạm", "violation", "tiêu chuẩn cộng đồng", "community standards",
            "cảnh báo", "warning", "bị gỡ", "thay đổi đối với video", "cập nhật mới"
        ]

        for item in items:
            try:
                # Dùng JS để lấy textContent cho an toàn vì có thể text bị ẩn với Selenium
                raw_text = driver.execute_script("return arguments[0].textContent;", item) or ""
                text = raw_text.lower()
                
                # Nếu trống thì skip
                if not text.strip():
                    continue
                    
                is_retracted = False
                if "hủy khiếu nại" in text or "retracted" in text or "gỡ mọi thay đổi" in text:
                    is_retracted = True
                    
                if not is_retracted and not any(kw in text for kw in copyright_keywords):
                    continue

                title = raw_text.strip().split("\n")[0][:120]
                if len(title) < 5:
                    title = raw_text[:120]
                    
                if is_retracted:
                    log.info(f"Video đã được hủy khiếu nại bản quyền (An toàn): {title}")

                post_url = ""
                if item.tag_name.lower() == "a":
                    post_url = item.get_attribute("href") or ""
                else:
                    try:
                        a = item.find_element(By.XPATH, ".//a[contains(@href,'facebook.com') or contains(@href, '/support')]")
                        post_url = a.get_attribute("href") or ""
                    except Exception:
                        pass

                status = ""
                if is_retracted:
                    status = "đã hủy khiếu nại"
                else:
                    for kw in ["removed", "disabled", "violated", "under review", "đã xóa", "bị vô hiệu", "vi phạm", "gỡ", "cập nhật mới"]:
                        if kw in text:
                            status = kw
                            break

                # Tính risk score — dùng age=0 (chưa biết tuổi bài → coi là mới → cần duyệt tay)
                risk = score_risk(post_url, post_age_hours=0)

                # Quyết định hành động: keyword match → queue_review; xóa hay không do caller (auto_delete) quyết định
                item_action = "skip" if is_retracted else "queue_review"
                
                # Ghi quyết định vào memory
                post_id_match = re.search(r"/(\d{10,})", post_url) if post_url else None
                pid = post_id_match.group(1) if post_id_match else (post_url or title[:32])

                decision_id = mem.record_decision(
                    post_id=pid,
                    method="keyword",
                    confidence=0.95,
                    category="copyright",
                    action=item_action,
                    reason="Matched violation keywords",
                    risk_score=risk,
                )

                # Học patterns nếu bật auto_learn
                if CONFIG.get("agent", {}).get("auto_learn_patterns", True) and raw_text:
                    mem.update_patterns(raw_text[:500], category="copyright")

                appeals.append({
                    "context": context_name,
                    "title": title,
                    "post_url": post_url,
                    "status": status,
                    "action": item_action,
                    "confidence": 0.95,
                    "decision_id": decision_id,
                })
            except Exception:
                continue

        if len(appeals) == 0:
            log.info(f"[{context_name}] Không tìm thấy vi phạm bản quyền nào.")
        else:
            safe_count = sum(1 for ap in appeals if ap.get("action") == "skip")
            violation_count = len(appeals) - safe_count
            if safe_count > 0:
                log.info(f"[{context_name}] Trong hộp thư có {len(appeals)} bài viết ({violation_count} vi phạm cần xử lý, {safe_count} bài đã an toàn/hủy khiếu nại).")
            else:
                log.info(f"[{context_name}] Tìm thấy {len(appeals)} vi phạm bản quyền.")
        bug_tracker.clear_bug("copyright_checker", "get_copyright_appeals")
    except Exception as e:
        if _is_chrome_error(e):
            raise e
        log.error(f"Lỗi lấy appeals [{context_name}]: {e}")
        bug_tracker.log_bug("copyright_checker", "get_copyright_appeals", e)
    return appeals


# ─────────────────────────────────────────────
# Xóa / yêu cầu gỡ bài vi phạm
# ─────────────────────────────────────────────

def delete_appeal_post(driver: webdriver.Chrome, appeal: dict, db: Database) -> bool:
    """
    Xóa bài viết. Hỗ trợ cả link Support Inbox và link bài viết thông thường.
    """
    post_url = appeal.get("post_url", "")
    title    = appeal.get("title", "")

    try:
        if not post_url:
            log.warning(f"Không có post_url để xóa bài vi phạm: {title[:60]}")
            return False

        if not post_url.startswith("http"):
            post_url = "https://www.facebook.com" + post_url

        driver.get(post_url)
        time.sleep(3)

        original_window = driver.current_window_handle
        
        if "/support/?item_id=" in post_url:
            # Xử lý xóa trong hộp thư hỗ trợ (Support Inbox)
            
            state = "START"
            max_attempts = 35 # Poll faster, more attempts
            for _ in range(max_attempts):
                if _is_chrome_dead(driver):
                    raise WebDriverException("Chrome is dead or disconnected during deletion flow")
                time.sleep(0.8) # Wait slightly instead of 2.5s
                
                # Check current window handles to close popup tabs like Community Standards
                for window_handle in driver.window_handles:
                    if window_handle != original_window:
                        try:
                            driver.switch_to.window(window_handle)
                            driver.close()
                        except Exception:
                            pass
                driver.switch_to.window(original_window)

                script = """
                var results = [];
                var xpath = "//div[@role='button'] | //div[@role='radio'] | //button | //a[@role='link'] | //a";
                var query = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                for (var i = 0; i < query.snapshotLength; i++) {
                    var el = query.snapshotItem(i);
                    // Check if displayed
                    if (el.offsetWidth > 0 && el.offsetHeight > 0 && window.getComputedStyle(el).visibility !== 'hidden') {
                        var text = el.textContent.trim().toLowerCase();
                        if (text && text.length < 100) {
                            results.push({"text": text, "el": el});
                        }
                    }
                }
                return results;
                """
                try:
                    element_data = driver.execute_script(script) or []
                except Exception as e:
                    if _is_chrome_error(e):
                        raise e
                    element_data = []

                element_texts = [(item["text"], item["el"]) for item in element_data if "text" in item and "el" in item]
                
                def safe_click(element):
                    try:
                        element.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", element)

                # Priority 1: If we are at the end (Đóng / Close)
                found_close = next((el for t, el in element_texts if t in ["đóng", "close", "ok", "xong", "done"]), None)
                if found_close and state == "DELETED":
                    safe_click(found_close)
                    break
                    
                # Priority 2: Confirmation button "Xóa video" or "Delete"
                found_confirm = next((el for t, el in element_texts if t in ["xóa video", "delete video", "xóa", "delete"]), None)
                if found_confirm and state == "READY_TO_DELETE":
                    safe_click(found_confirm)
                    state = "DELETED"
                    continue
                    
                # Priority 3: Radio button "Gỡ video"
                found_radio = next((el for t, el in element_texts if any(kw in t for kw in ["gỡ video", "remove video", "xóa video", "delete video", "remove message"])), None)
                if found_radio and state in ["START", "MODAL_OPEN"]:
                    safe_click(found_radio)
                    state = "OPTION_SELECTED"
                    time.sleep(0.5) # Wait a bit before clicking tiếp tục
                    # Now try to find "Tiếp tục" in the same view
                    try:
                        continue_script = """
                        var xpath = "//div[@role='button'] | //button | //a";
                        var query = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                        for (var i = 0; i < query.snapshotLength; i++) {
                            var el = query.snapshotItem(i);
                            var t = el.textContent.trim().toLowerCase();
                            if ((t === "tiếp tục" || t === "continue") && el.offsetWidth > 0 && el.offsetHeight > 0) {
                                return el;
                            }
                        }
                        return null;
                        """
                        continue_btn = driver.execute_script(continue_script)
                        if continue_btn:
                            safe_click(continue_btn)
                            state = "READY_TO_DELETE"
                    except Exception as e:
                        if _is_chrome_error(e):
                            raise e
                    continue
                    
                # Priority 4: "Tiếp tục" (Navigating modal)
                found_continue = next((el for t, el in element_texts if t in ["tiếp tục", "continue"]), None)
                if found_continue and state in ["START", "MODAL_OPEN", "OPTION_SELECTED"]:
                    prev_state = state
                    safe_click(found_continue)
                    state = "READY_TO_DELETE" if prev_state == "OPTION_SELECTED" else "MODAL_OPEN"
                    continue
                    
                # Priority 5: "Xem chi tiết" or "Xem các tùy chọn"
                found_open = next((el for t, el in element_texts if t in ["xem các tùy chọn", "see options", "xem chi tiết", "see details", "xem lựa chọn"]), None)
                if found_open and state == "START":
                    safe_click(found_open)
                    state = "MODAL_OPEN"
                    continue
                    
            # Update DB anyway if we reached DELETED or READY_TO_DELETE
            if state == "DELETED":
                try:
                    log.info(f"Đã xử lý xóa qua hộp thư hỗ trợ: {(appeal.get('title') or '')[:60]}")
                    if db:
                        db.mark_violation_deleted(appeal.get("post_url"))
                    bug_tracker.clear_bug("copyright_checker", "delete_appeal_post")
                    return True
                except Exception as e:
                    log.error(f"Lỗi xóa bài vi phạm '{(appeal.get('title') or '')[:60]}': {e}")
                    return False
            else:
                log.warning(f"Không thể hoàn thành flow xóa cho: {title[:60]} (State: {state})")
                return False

            
        else:
            # Chờ bài viết load xong
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH, "//*"))
            )

            # Tìm menu 3 chấm của bài viết
            menu = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH,
                 "//div[@aria-label='Actions for this post' or @aria-label='More' "
                 "or @aria-label='Tùy chọn bài viết' or @data-testid='post_chevron_button']")
            ))
            driver.execute_script("arguments[0].click();", menu)

            # Bấm Delete / Xóa
            del_btn = WebDriverWait(driver, 8).until(EC.element_to_be_clickable(
                (By.XPATH,
                 "//*[contains(text(),'Move to trash') or contains(text(),'Delete post') "
                 "or contains(text(),'Xóa bài viết') or contains(text(),'Xóa')]")
            ))
            driver.execute_script("arguments[0].click();", del_btn)

            # Xác nhận dialog
            try:
                confirm = WebDriverWait(driver, 6).until(EC.element_to_be_clickable(
                    (By.XPATH,
                     "//div[@aria-label='Delete' or @aria-label='Xóa']//div[@role='button'] "
                     "| //button[contains(text(),'Delete') or contains(text(),'Xóa') or contains(text(),'OK')]")
                ))
                driver.execute_script("arguments[0].click();", confirm)
                time.sleep(1)
            except Exception:
                pass

            post_id_match = re.search(r"/(\d{10,})", post_url) if post_url else None
            pid = post_id_match.group(1) if post_id_match else post_url
            db.record_deletion(pid, post_url, "copyright_appeal")
            log.info(f"Đã xóa bài vi phạm: {title[:60]}")
            bug_tracker.clear_bug("copyright_checker", "delete_appeal_post")
            return True

    except Exception as e:
        if _is_chrome_error(e):
            raise e
        log.error(f"Lỗi xóa bài vi phạm '{title[:60]}': {e}")
        bug_tracker.log_bug("copyright_checker", "delete_appeal_post", e)
    return False


# ─────────────────────────────────────────────
# Quét toàn bộ: profile + tất cả fanpage
# ─────────────────────────────────────────────

def run_full_copyright_check(
    driver: webdriver.Chrome,
    db: Database,
    fanpages: list[dict],
    auto_delete: bool = False,
    log_callback=None,
    account_name: str = "",
    account_uid: str = "",
    stop_event=None,
    profile_dir: str = None,
) -> dict:
    """
    Quét trang cá nhân + tất cả fanpage để tìm vi phạm bản quyền.
    auto_delete=True → tự xóa ngay các bài có action='auto_delete'.
    stop_event → Event để dừng quét đa luồng từ GUI.
    profile_dir → thư mục Chrome profile của tool (để rebuild đúng khi Chrome crash).
    Trả về {"total_appeals": int, "deleted": int, "details": list, "driver": driver}
    """
    from agent.perceive import notify_violation_found, notify_deletion_done

    def _log(msg):
        log.info(msg)
        if log_callback:
            log_callback(msg)

    # ── Helper: rebuild Chrome nếu bị tắt ──────────────────────────────────
    def _try_recover(current_driver, context_hint=""):
        """
        Phát hiện Chrome chết → rebuild đúng profile → trả về (driver_mới, True)
        Nếu không cần recover → trả về (current_driver, False)
        """
        if not _is_chrome_dead(current_driver):
            return current_driver, False
        _log(f"⚡ Chrome mất kết nối{' (tại: ' + context_hint + ')' if context_hint else ''} — đang khởi động lại...")
        new_drv = rebuild_driver(current_driver, profile_dir)
        return new_drv, True
    # ───────────────────────────────────────────────────────────────────────

    all_appeals = []
    deleted = 0

    # 0. Kiểm tra dừng quét trước khi bắt đầu
    if stop_event and stop_event.is_set():
        _log("Quét bản quyền đã bị dừng bởi người dùng.")
        return {"total_appeals": 0, "deleted": 0, "details": [], "driver": driver}

    # 1. Đảm bảo đang ở trang cá nhân chính
    _log("Đảm bảo đang ở trang cá nhân chính...")
    try:
        switch_to_profile(driver)
    except Exception as e:
        if _is_chrome_error(e):
            driver, _ = _try_recover(driver, "switch_to_profile")
            try:
                switch_to_profile(driver)
            except Exception:
                pass

    # 2. Quét profile cá nhân
    _log("Đang quét trang cá nhân...")
    try:
        personal_appeals = get_copyright_appeals(driver, context_name="Cá nhân")
    except Exception as e:
        if _is_chrome_error(e):
            driver, _ = _try_recover(driver, "get_copyright_appeals cá nhân")
            try:
                personal_appeals = get_copyright_appeals(driver, context_name="Cá nhân")
            except Exception:
                personal_appeals = []
        else:
            personal_appeals = []

    if len(personal_appeals) == 0:
        _log("  ✓ (Cá nhân) Không có bài viết nào vi phạm bản quyền.")
    else:
        safe_count = sum(1 for ap in personal_appeals if ap.get("action") == "skip")
        violation_count = len(personal_appeals) - safe_count
        if safe_count > 0:
            _log(f"  ⚠ (Cá nhân) Hộp thư có {len(personal_appeals)} bài ({violation_count} vi phạm, {safe_count} an toàn/hủy khiếu nại).")
        else:
            _log(f"  ⚠ (Cá nhân) Tìm thấy {len(personal_appeals)} vi phạm bản quyền.")
    all_appeals.extend(personal_appeals)

    if account_uid:
        db.clear_violations(account_uid, "Cá nhân")
        if personal_appeals:
            db.save_violations(account_uid, "Cá nhân", personal_appeals)

    if personal_appeals:
        notify_violation_found("Cá nhân", len(personal_appeals), account=account_name)

    if auto_delete:
        for ap in personal_appeals:
            if stop_event and stop_event.is_set():
                _log("Quét bản quyền đã bị dừng bởi người dùng.")
                break
            if ap.get("action") == "skip":
                _log(f"  ✓ Bỏ qua (Đã an toàn): {ap['title'][:60]}")
                continue
            try:
                ok = delete_appeal_post(driver, ap, db)
            except Exception as e:
                if _is_chrome_error(e):
                    driver, _ = _try_recover(driver, "delete personal")
                    ok = False
                else:
                    ok = False
            if ok:
                deleted += 1
                _log(f"  ✓ Đã xóa: {ap['title'][:60]}")
                if account_uid: db.remove_violation(ap.get("post_url", ""))
            else:
                _log(f"  ✗ Không thể xóa: {ap['title'][:60]}")
    else:
        for ap in personal_appeals:
            _log(f"  ⏳ Chờ duyệt (confidence={ap.get('confidence', 0):.0%}): {ap['title'][:60]}")

    # 3. Quét từng fanpage
    for page in fanpages:
        # Kiểm tra dừng quét trước mỗi fanpage
        if stop_event and stop_event.is_set():
            _log("Quét bản quyền đã bị dừng bởi người dùng.")
            break

        page_name = page.get("name", page.get("url", ""))
        page_url  = page.get("url", "")
        if not page_url:
            continue

        # Kiểm tra Chrome còn sống trước mỗi fanpage
        driver, recovered = _try_recover(driver, f"trước fanpage {page_name}")
        if recovered:
            # Sau recover, bắt đầu lại switch_to_profile
            try:
                switch_to_profile(driver)
            except Exception:
                pass

        _log(f"Đang switch sang fanpage: {page_name}")
        try:
            switched = switch_to_page(driver, page_url, page_name=page_name)
        except Exception as e:
            if _is_chrome_error(e):
                driver, _ = _try_recover(driver, f"switch_to_page {page_name}")
                try:
                    switch_to_profile(driver)
                    switched = switch_to_page(driver, page_url, page_name=page_name)
                except Exception:
                    switched = False
            else:
                switched = False

        if not switched:
            _log(f"  ✗ Không thể switch: {page_name}")
            continue

        # Kiểm tra dừng quét sau khi switch
        if stop_event and stop_event.is_set():
            _log("Quét bản quyền đã bị dừng bởi người dùng.")
            try:
                switch_to_profile(driver)
            except Exception:
                pass
            break

        try:
            page_appeals = get_copyright_appeals(driver, context_name=page_name)
        except Exception as e:
            if _is_chrome_error(e):
                driver, _ = _try_recover(driver, f"get_copyright_appeals {page_name}")
                try:
                    switch_to_profile(driver)
                    switched2 = switch_to_page(driver, page_url, page_name=page_name)
                    page_appeals = get_copyright_appeals(driver, context_name=page_name) if switched2 else []
                except Exception:
                    page_appeals = []
            else:
                page_appeals = []

        if len(page_appeals) == 0:
            _log(f"  ✓ ({page_name}) Không có bài viết nào vi phạm bản quyền.")
        else:
            safe_count = sum(1 for ap in page_appeals if ap.get("action") == "skip")
            violation_count = len(page_appeals) - safe_count
            if safe_count > 0:
                _log(f"  ⚠ ({page_name}) Hộp thư có {len(page_appeals)} bài ({violation_count} vi phạm, {safe_count} an toàn/hủy khiếu nại).")
            else:
                _log(f"  ⚠ ({page_name}) Tìm thấy {len(page_appeals)} vi phạm bản quyền.")
        all_appeals.extend(page_appeals)

        if account_uid:
            db.clear_violations(account_uid, page_name)
            if page_appeals:
                db.save_violations(account_uid, page_name, page_appeals)

        if page_appeals:
            notify_violation_found(page_name, len(page_appeals), account=account_name)

        if auto_delete:
            for ap in page_appeals:
                if stop_event and stop_event.is_set():
                    break
                if ap.get("action") == "skip":
                    _log(f"  ✓ Bỏ qua ({page_name} - Đã an toàn): {ap['title'][:60]}")
                    continue
                try:
                    ok = delete_appeal_post(driver, ap, db)
                except Exception as e:
                    if _is_chrome_error(e):
                        _log(f"  ⚡ Chrome mất kết nối khi xóa bài — đang rebuild...")
                        driver, _ = _try_recover(driver, f"delete {page_name}")
                        ok = False  # bỏ qua bài này, tiếp fanpage tiếp theo
                    else:
                        ok = False
                if ok:
                    deleted += 1
                    _log(f"  ✓ Đã xóa ({page_name}): {ap['title'][:60]}")
                    if account_uid: db.remove_violation(ap.get("post_url", ""))
                else:
                    _log(f"  ✗ Không thể xóa ({page_name}): {ap['title'][:60]}")
        else:
            for ap in page_appeals:
                _log(f"  ⏳ Chờ duyệt: {ap['title'][:60]}")

        # Quay về profile cá nhân chuẩn bị cho vòng quét tiếp theo
        try:
            switch_to_profile(driver)
        except Exception as e:
            if _is_chrome_error(e):
                driver, _ = _try_recover(driver, "switch_to_profile sau fanpage")

    summary = f"Hoàn tất: {len(all_appeals)} vi phạm | Đã xóa: {deleted}"
    _log(summary)
    if deleted > 0:
        notify_deletion_done(deleted, len(all_appeals), account=account_name)

    db.log_scan(total=len(all_appeals), flagged=len(all_appeals), deleted=deleted)

    return {
        "total_appeals": len(all_appeals),
        "deleted": deleted,
        "driver": driver,  # Trả về driver (có thể là driver mới sau rebuild)
        "details": [
            {
                "context": a["context"], "title": a["title"],
                "post_url": a["post_url"], "status": a["status"],
                "action": a.get("action", "skip"),
                "confidence": a.get("confidence", 0.0),
            }
            for a in all_appeals
        ],
    }
