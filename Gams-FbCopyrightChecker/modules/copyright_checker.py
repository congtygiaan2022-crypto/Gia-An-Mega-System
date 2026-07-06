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

# ⚠ CẢNH BÁO: Facebook đang quét và chặn giả lập trình duyệt bằng URL trực tiếp.
# Hạn chế sử dụng driver.get() với các URL này. Ưu tiên thao tác qua UI (click nút).
# Chỉ dùng làm fallback cuối cùng nếu navigate qua UI thất bại.

ORIGINAL_PC_USER_AGENT = ""

def set_browser_mode(driver, mode: str = "pc") -> bool:
    """
    Chuyển đổi linh hoạt chế độ trình duyệt giữa PC và Mobile.
    Sử dụng CDP (Chrome DevTools Protocol) để thay đổi User Agent năng động và thay đổi Viewport.
    """
    global ORIGINAL_PC_USER_AGENT
    import time
    
    # Lưu User Agent PC gốc nếu chưa lưu
    if not ORIGINAL_PC_USER_AGENT:
        try:
            ORIGINAL_PC_USER_AGENT = driver.execute_script("return navigator.userAgent;")
            log.info(f"[Mode Switch] Đã ghi nhớ User Agent PC gốc: {ORIGINAL_PC_USER_AGENT}")
        except Exception as e:
            ORIGINAL_PC_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
            log.warning(f"[Mode Switch] Không thể lấy UA động, sử dụng mặc định: {e}")
            
    # Lấy User Agent di động từ CONFIG hoặc mặc định
    mobile_cfg = CONFIG.get("mobile_settings", {})
    user_agents = mobile_cfg.get("user_agents", [])
    mobile_ua = user_agents[0] if user_agents else "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/130.0.0.0 Mobile/15E148 Safari/604.1"
    
    try:
        if mode == "mobile":
            log.info(f"[Mode Switch] Đang chuyển sang chế độ di động (Resize 575x1020 & Mobile UA)...")
            # 1. Đổi User Agent qua CDP
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": mobile_ua
            })
            # 2. Resize kích thước di động
            driver.set_window_size(575, 1020)
        else:
            log.info("[Mode Switch] Đang chuyển về chế độ máy tính (Maximize & PC UA)...")
            # 1. Khôi phục User Agent gốc
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": ORIGINAL_PC_USER_AGENT
            })
            # 2. Maximize cửa sổ về PC
            try:
                driver.maximize_window()
            except Exception:
                driver.set_window_size(1400, 900)
                
        time.sleep(2)
        return True
    except Exception as e:
        log.error(f"[Mode Switch] Lỗi khi chuyển đổi chế độ sang {mode}: {e}")
        return False

CURRENT_ACCOUNT_NAME = ""
APPEALS_URL = "https://www.facebook.com/support/?tab_type=APPEALS"
SUPPORT_URL  = "https://www.facebook.com/support/"


# ─────────────────────────────────────────────
# Chrome crash detection & recovery
# ─────────────────────────────────────────────

def _is_chrome_dead(driver: webdriver.Chrome) -> bool:
    """Kiểm tra xem Chrome session có còn sống không."""
    if not driver:
        return True
    try:
        # Sử dụng window_handles thay cho current_url để kiểm tra kết nối cực nhanh và độc lập với trạng thái load trang
        _ = driver.window_handles
        return False
    except Exception:
        return True


def _is_chrome_error(exc: Exception) -> bool:
    """Trả về True nếu exception là do Chrome bị tắt/crash/disconnect/connection reset."""
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, 
        StaleElementReferenceException, ElementClickInterceptedException,
        ElementNotInteractableException, NoSuchFrameException, NoSuchWindowException,
        JavascriptException
    )
    # Loại trừ các lỗi tương tác/chờ/Javascript thông thường không phải do sập trình duyệt
    if isinstance(exc, (
        TimeoutException, NoSuchElementException,
        StaleElementReferenceException, ElementClickInterceptedException,
        ElementNotInteractableException, NoSuchFrameException, NoSuchWindowException,
        JavascriptException
    )):
        return False

    err_str = str(exc).lower()
    
    # Nếu là lỗi mạng do trình duyệt báo cáo (Chrome vẫn sống và báo lỗi)
    if "net::err_" in err_str:
        return False

    # Loại bỏ các lỗi transient client timeout (như httpconnectionpool, max retries exceeded)
    # để tránh coi nhầm việc load chậm là sập trình duyệt.
    return (
        isinstance(exc, InvalidSessionIdException)
        or "invalid session id" in err_str
        or "chrome not reachable" in err_str
        or "connection refused" in err_str
        or "target window already closed" in err_str
        or "disconnected" in err_str
        or "connectionreseterror" in err_str
        or "connection reset" in err_str
        or "10054" in err_str
        or "forcibly closed" in err_str
    )


# Số fanpage sau mỗi lần proactive restart Chrome để xả bộ nhớ
CHROME_RESTART_EVERY = 8


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

    log.info("Đăng nhập lại thành công — đang chờ Chrome ổn định...")

    # FIX #2: Chờ Chrome ổn định sau khi login — navigate về homepage và
    # verify banner đã render trước khi tiếp tục bất kỳ thao tác nào.
    try:
        time.sleep(2)  # Cho cookie/session sync
        new_driver.get("https://www.facebook.com/")
        WebDriverWait(new_driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='banner']"))
        )
        time.sleep(1.5)  # Cho JS FB render xong animation
        log.info("Chrome ổn định — banner FB đã sẵn sàng.")
    except Exception as e:
        log.debug(f"rebuild_driver stabilization: {e} — tiếp tục dù sao.")

    return new_driver


def proactive_rebuild_driver(old_driver: webdriver.Chrome, profile_dir: str = None) -> webdriver.Chrome:
    """
    Chủ động khởi động lại Chrome để giải phóng bộ nhớ tích lũy (ngăn OOM crash).
    Khác rebuild_driver: Chrome vẫn còn sống — chỉ quit và mở lại.
    """
    from modules.fb_login import build_driver, login
    from agent.chrome_manager import ensure_profile_closed

    log.info("♻ Proactive Chrome restart để xả bộ nhớ...")
    try:
        old_driver.quit()
    except Exception:
        pass
    if profile_dir:
        try:
            ensure_profile_closed(profile_dir)
        except Exception:
            pass
    time.sleep(2)  # Cho Chrome process tắt hẳn
    new_driver = build_driver(profile_dir=profile_dir)
    if not login(new_driver):
        log.warning("Đăng nhập lại sau proactive restart thất bại — tiếp tục dù sao.")
    else:
        log.info("♻ Proactive restart hoàn tất — Chrome sạch, tiếp tục quét.")
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
            
            # Chờ quá trình chuyển đổi bắt đầu (animation FB)
            time.sleep(2)

            # Kiểm tra nhanh trang đã load chưa — không throw exception nếu chậm
            # Dùng selector rộng hơn để bắt cả fanpage context lẫn profile context
            _broad_css = (
                "[role='navigation'], [data-pagelet='LeftRail'], "
                "[aria-label='Your profile'], [role='main'], "
                "[data-pagelet='ProfileTilesFeed'], [data-pagelet='FeedUnit']"
            )
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, _broad_css)
                )
            except TimeoutException:
                # Trang load chậm nhưng Chrome vẫn sống — chấp nhận và tiếp tục
                log.debug(f"switch_context: Trang load chậm sau khi chuyển sang '{target_name}' — tiếp tục.")
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


def _normalize_fb_url(url: str) -> str:
    """Chuẩn hóa URL Facebook: web.facebook.com → facebook.com."""
    return url.replace("https://web.facebook.com", "https://www.facebook.com") \
               .replace("http://web.facebook.com", "https://www.facebook.com")


def _navigate_url_with_retry(driver: webdriver.Chrome, url: str, max_attempts: int = 3) -> bool:
    """Navigate đến URL với cơ chế thử lại khi timeout/lỗi mạng. Trả về True nếu thành công."""
    for attempt in range(1, max_attempts + 1):
        try:
            driver.get(url)
            return True
        except TimeoutException as e:
            if attempt == max_attempts:
                log.warning(f"Timeout tải {url} sau {max_attempts} lần — tiếp tục.")
                return True  # Chrome load được một phần — tiếp tục xử lý
            log.warning(f"Timeout tải {url} (lần {attempt}/{max_attempts}), thử lại...")
            time.sleep(2)
        except WebDriverException as e:
            err = str(e).lower()
            if _is_chrome_error(e):
                raise e
            if "net::err_" in err:
                if attempt == max_attempts:
                    log.warning(f"Lỗi mạng tải {url} sau {max_attempts} lần — tiếp tục.")
                    return True  # Trang có thể load được một phần
                log.warning(f"Lỗi mạng tải {url} (lần {attempt}/{max_attempts}): {e}, thử lại...")
                time.sleep(2)
            else:
                raise e
    return True


def switch_to_page(driver: webdriver.Chrome, page_url: str, page_name: str = "") -> bool:
    """
    Switch sang fanpage theo thứ tự ưu tiên:
      1. Navigate thẳng đến URL page → click nút 'Switch Now' / 'Chuyển sang trang'
      2. Nếu không có nút Switch (context đã đúng), kiểm tra URL hiện tại
      3. Fallback: switch_context_via_menu() (chỉ hiệu quả với ≤10 pages phổ biến)
    """
    is_mobile = CONFIG.get("mobile_settings", {}).get("enabled", False)
    if is_mobile:
        # Chuyển sang Mobile Mode để thực hiện switch profile đầy đủ
        set_browser_mode(driver, "mobile")
        try:
            ok = switch_to_page_mobile(driver, page_name, page_url)
        finally:
            # Luôn chuyển ngược về PC Mode sau khi switch xong
            set_browser_mode(driver, "pc")
            # Điều hướng sang trang chủ PC để đồng bộ hóa context mới
            try:
                driver.get("https://www.facebook.com/")
                time.sleep(3)
            except Exception:
                pass
        return ok
    name_from_url = ""
    if page_url.startswith("#name="):
        name_from_url = page_url.split("=", 1)[1]

    target_name = page_name or name_from_url

    # ── Trường hợp đặc biệt: URL dạng #name=... (không có URL thật) ──────────
    if page_url.startswith("#"):
        if target_name:
            ok = switch_context_via_menu(driver, target_name)
            if ok:
                bug_tracker.clear_bug("copyright_checker", "switch_to_page")
            return ok
        return False

    # ── Bước 1: Navigate trực tiếp đến URL page ───────────────────────────────
    # FIX #1: Đây là chiến lược ĐÚNG cho Facebook — navigate vào page rồi
    # click nút 'Chuyển sang trang' thay vì dùng dropdown menu (chỉ hiện ~10 page).
    try:
        normalized_url = _normalize_fb_url(page_url)
        log.debug(f"switch_to_page: Navigate đến {normalized_url}")

        # Về trang chủ trước để đảm bảo context sạch
        try:
            current = driver.current_url or ""
            if "about:blank" in current or not current:
                driver.get("https://www.facebook.com/")
                time.sleep(1.5)
        except Exception:
            pass

        _navigate_url_with_retry(driver, normalized_url)
        time.sleep(2)  # Chờ trang render các nút action

        # ── Bước 2: Tìm nút Switch Now / Chuyển sang trang ─────────────────────
        # Facebook hiển thị nút này cho admin khi đang ở context khác.
        switch_xpaths = [
            # Nút dạng div[@role='button'] chứa text
            "//div[@role='button'][contains(.,'Switch to Page') or contains(.,'Chuyển sang trang') or contains(.,'Switch Now') or contains(.,'Chuyển ngay') or contains(.,'Switch to') or contains(.,'Chuyển sang')]",
            # Nút dạng a hoặc button
            "//a[@role='button'][contains(.,'Switch') or contains(.,'Chuyển')]",
            "//button[contains(.,'Switch') or contains(.,'Chuyển')]",
            # Text node trực tiếp
            "//*[self::span or self::div][normalize-space(text())='Switch to Page' or normalize-space(text())='Chuyển sang trang' or normalize-space(text())='Switch Now' or normalize-space(text())='Chuyển ngay']",
        ]
        switch_btn = None
        for xpath in switch_xpaths:
            try:
                switch_btn = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                if switch_btn:
                    break
            except TimeoutException:
                continue
            except Exception as e:
                if _is_chrome_error(e):
                    raise e
                continue

        if switch_btn:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", switch_btn)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", switch_btn)
                time.sleep(2.5)  # Chờ Facebook xử lý switch context
                log.info(f"Đã click nút Switch sang '{target_name or page_url}'")
                bug_tracker.clear_bug("copyright_checker", "switch_to_page")
                return True
            except Exception as e:
                if _is_chrome_error(e):
                    raise e
                log.debug(f"Click switch btn lỗi: {e}")

        # ── Bước 3: Không có nút Switch → kiểm tra xem context đã đúng chưa ────
        # Nếu trang hiện tại là page đó (đang ở đúng context), không cần switch.
        try:
            current_url = driver.current_url or ""
            # Trích xuất page_id từ URL để so sánh
            import re as _re
            pid_match = _re.search(r"profile\.php\?id=(\d+)", normalized_url)
            if pid_match:
                pid = pid_match.group(1)
                if pid in current_url:
                    log.info(f"Context đã ở đúng page '{target_name}' (ID={pid}) — không cần switch.")
                    bug_tracker.clear_bug("copyright_checker", "switch_to_page")
                    return True
            else:
                # URL dạng /pagename — kiểm tra slug
                slug = normalized_url.rstrip("/").split("/")[-1].lower()
                if slug and slug in current_url.lower():
                    log.info(f"Context đã ở đúng page '{target_name}' (slug={slug}) — không cần switch.")
                    bug_tracker.clear_bug("copyright_checker", "switch_to_page")
                    return True
        except Exception as e:
            if _is_chrome_error(e):
                raise e

        # ── Bước 4: JS-based search — quét toàn bộ nút hiển thị trên trang ────
        try:
            js_switch_script = """
            var keywords = ['switch to page', 'chuyển sang trang', 'switch now', 'chuyển ngay',
                            'switch to', 'chuyển sang'];
            var xpath = "//div[@role='button'] | //a[@role='button'] | //button";
            var query = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
            for (var i = 0; i < query.snapshotLength; i++) {
                var el = query.snapshotItem(i);
                if (el.offsetWidth > 0 && el.offsetHeight > 0) {
                    var txt = el.textContent.trim().toLowerCase();
                    for (var j = 0; j < keywords.length; j++) {
                        if (txt.indexOf(keywords[j]) !== -1) {
                            return el;
                        }
                    }
                }
            }
            return null;
            """
            js_btn = driver.execute_script(js_switch_script)
            if js_btn:
                driver.execute_script("arguments[0].click();", js_btn)
                time.sleep(2.5)
                log.info(f"Đã click nút Switch (JS fallback) sang '{target_name or page_url}'")
                bug_tracker.clear_bug("copyright_checker", "switch_to_page")
                return True
        except Exception as e:
            if _is_chrome_error(e):
                raise e
            log.debug(f"JS switch btn search lỗi: {e}")

        # ── Bước 5: Fallback cuối — dùng menu dropdown ──────────────────────────
        # Chỉ hiệu quả nếu page nằm trong ~10 pages phổ biến hiển thị trong dropdown.
        if target_name:
            log.debug(f"Thử fallback menu switch cho '{target_name}'...")
            ok = switch_context_via_menu(driver, target_name)
            if ok:
                bug_tracker.clear_bug("copyright_checker", "switch_to_page")
                return True

        # Không switch được bằng bất kỳ phương án nào
        log.warning(f"Không tìm được nút Switch cho '{target_name or page_url}' — bỏ qua.")
        bug_tracker.log_bug("copyright_checker", "switch_to_page",
                            f"Không tìm được nút switch cho {target_name or page_url}")
        return False

    except Exception as e:
        if _is_chrome_error(e):
            raise e
        log.error(f"Lỗi switch_to_page '{target_name or page_url}': {e}")
        bug_tracker.log_bug("copyright_checker", "switch_to_page", e)
        return False


def _is_in_page_context(driver: webdriver.Chrome) -> bool:
    """
    Kiểm tra xem hiện tại có đang ở context Fanpage không.
    Trả về True nếu đang dùng Facebook với tư cách Page (không phải cá nhân).
    """
    try:
        script = """
        var indicators = [
            'đang dùng facebook với tư cách',
            'using facebook as',
            "you're using facebook as",
            'switch to your personal account',
            'chuyển về tài khoản cá nhân'
        ];
        var bodyText = (document.body && document.body.textContent || '').toLowerCase();
        for (var i = 0; i < indicators.length; i++) {
            if (bodyText.indexOf(indicators[i]) !== -1) return true;
        }
        // Kiểm tra thêm: nếu có banner "đang hoạt động dưới dạng" trong header
        var bannerEls = document.querySelectorAll('[role="banner"] *');
        for (var j = 0; j < bannerEls.length; j++) {
            var t = (bannerEls[j].getAttribute('aria-label') || '').toLowerCase();
            if (t.indexOf('switch to') !== -1 || t.indexOf('chuyển về') !== -1) return true;
        }
        return false;
        """
        return bool(driver.execute_script(script))
    except Exception:
        return False


def _js_click_avatar_and_switch_to_personal(driver: webdriver.Chrome, profile_name: str = "") -> bool:
    """
    Dùng JavaScript để tìm và click nút Avatar trong banner, sau đó chọn profile cá nhân.
    Đây là cách đáng tin cậy hơn XPath vì không bị ảnh hưởng bởi thay đổi DOM của Facebook.
    """
    try:
        # Bước 1: Tìm avatar button trong banner bằng JS (không dùng XPath timeout)
        click_avatar_script = """
        var banner = document.querySelector('[role="banner"]');
        if (!banner) return false;

        // Tìm tất cả div[@role='button'] có chứa img (avatar)
        var buttons = banner.querySelectorAll('[role="button"]');
        var avatarBtn = null;
        for (var i = 0; i < buttons.length; i++) {
            var btn = buttons[i];
            // Ưu tiên button có aria-label liên quan đến profile
            var lbl = (btn.getAttribute('aria-label') || '').toLowerCase();
            if (lbl.indexOf('profile') !== -1 || lbl.indexOf('trang cá nhân') !== -1 ||
                lbl.indexOf('account') !== -1 || lbl.indexOf('tài khoản') !== -1) {
                avatarBtn = btn;
                break;
            }
            // Fallback: button có chứa img
            if (!avatarBtn && btn.querySelector('img')) {
                avatarBtn = btn;
            }
        }
        if (avatarBtn) {
            avatarBtn.click();
            return true;
        }
        return false;
        """
        clicked = driver.execute_script(click_avatar_script)
        if not clicked:
            log.debug("_js_click_avatar: Không tìm thấy avatar button trong banner.")
            return False

        time.sleep(1.5)

        # Bước 2: Click "Xem tất cả trang cá nhân" / "See all profiles"
        see_all_script = """
        var keywords = ['xem tất cả trang cá nhân', 'see all profiles', 'see all Profiles'];
        var els = document.querySelectorAll('[role="menu"] *, [role="dialog"] *');
        for (var i = 0; i < els.length; i++) {
            var txt = (els[i].textContent || '').trim().toLowerCase();
            for (var j = 0; j < keywords.length; j++) {
                if (txt === keywords[j].toLowerCase()) {
                    els[i].click();
                    return true;
                }
            }
        }
        // Broader search
        var allEls = document.querySelectorAll('*');
        for (var k = 0; k < allEls.length; k++) {
            var t = (allEls[k].textContent || '').trim();
            if (t === 'Xem tất cả trang cá nhân' || t === 'See all profiles' || t === 'See all Profiles') {
                allEls[k].click();
                return true;
            }
        }
        return false;
        """
        see_all_clicked = driver.execute_script(see_all_script)
        if not see_all_clicked:
            log.debug("_js_click_avatar: Không tìm thấy 'Xem tất cả trang cá nhân'.")
            # Đóng menu và return False
            try:
                from selenium.webdriver.common.keys import Keys
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except Exception:
                pass
            return False

        time.sleep(1.5)

        # Bước 3: Tìm và click profile cá nhân trong danh sách
        pick_profile_script = """
        var targetName = arguments[0].toLowerCase();
        var containers = document.querySelectorAll('[role="dialog"], [role="menu"]');
        for (var c = 0; c < containers.length; c++) {
            var btns = containers[c].querySelectorAll('[role="button"], [role="link"]');
            for (var i = 0; i < btns.length; i++) {
                var btn = btns[i];
                if (btn.offsetWidth === 0 || btn.offsetHeight === 0) continue;
                var txt = (btn.textContent || '').trim().toLowerCase();
                if (!txt) continue;
                // Ưu tiên tên chính xác
                if (targetName && txt.indexOf(targetName) !== -1) {
                    btn.click();
                    return 'name_match';
                }
            }
        }
        // Fallback: click phần tử đầu tiên (thường là cá nhân)
        for (var c2 = 0; c2 < containers.length; c2++) {
            var firstBtns = containers[c2].querySelectorAll('[role="button"], [role="link"]');
            for (var i2 = 0; i2 < firstBtns.length; i2++) {
                var fb = firstBtns[i2];
                if (fb.offsetWidth > 0 && fb.offsetHeight > 0 && (fb.textContent || '').trim()) {
                    fb.click();
                    return 'first_item';
                }
            }
        }
        return null;
        """
        result = driver.execute_script(pick_profile_script, profile_name or "")
        if result:
            log.info(f"Đã chọn profile ({result}): '{profile_name or 'đầu tiên'}'")
            time.sleep(2)
            return True

        log.debug("_js_click_avatar: Không tìm thấy profile trong danh sách.")
        return False

    except Exception as e:
        if _is_chrome_error(e):
            raise e
        log.debug(f"_js_click_avatar_and_switch_to_personal: {e}")
        return False


def switch_to_profile(driver: webdriver.Chrome) -> bool:
    """Quay về profile cá nhân."""
    is_mobile = CONFIG.get("mobile_settings", {}).get("enabled", False)
    if is_mobile:
        # Chuyển sang Mobile Mode để thực hiện switch về cá nhân
        set_browser_mode(driver, "mobile")
        try:
            ok = switch_to_personal_mobile(driver)
        finally:
            # Luôn chuyển ngược về PC Mode sau khi switch xong
            set_browser_mode(driver, "pc")
            try:
                driver.get("https://www.facebook.com/")
                time.sleep(3)
            except Exception:
                pass
        return ok
    try:
        # Dùng timeout ngắn hơn để tránh chờ lâu — trang FB thường load < 20s
        # Bắt TimeoutException riêng để không nhầm với Chrome crash
        original_timeout = CONFIG.get("selenium", {}).get("page_load_timeout", 30)
        try:
            driver.set_page_load_timeout(20)
            driver.get("https://www.facebook.com/")
        except TimeoutException:
            log.warning("switch_to_profile: Trang chủ FB load chậm (timeout) — tiếp tục.")
        except WebDriverException as e:
            if "net::err_" not in str(e).lower():
                raise e
            # Lỗi mạng nhưng Chrome vẫn sống — tiếp tục
            log.debug(f"switch_to_profile: Lỗi mạng FB ({type(e).__name__}) — tiếp tục.")
        finally:
            try:
                driver.set_page_load_timeout(original_timeout)
            except Exception:
                pass

        time.sleep(2)

        # Bước 2: Phát hiện context hiện tại
        # Nếu KHÔNG đang ở Page context → đã ở personal profile → return True ngay
        if not _is_in_page_context(driver):
            log.debug("switch_to_profile: Đã ở personal profile context — không cần switch.")
            return True

        log.info("switch_to_profile: Đang ở Page context — đang chuyển về personal profile...")

        # Bước 3: Thử Quick Switch button (biểu tượng mũi tên vòng tròn)
        try:
            quick_switch = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//div[@role='banner']//div[@aria-label='Switch profile' or @aria-label='Chuyển trang cá nhân']"
                    " | //div[@role='banner']//div[contains(@aria-label,'Switch to') or contains(@aria-label,'Chuyển sang')]"
                ))
            )
            driver.execute_script("arguments[0].click();", quick_switch)
            time.sleep(1.5)
            if not _is_in_page_context(driver):
                log.info("switch_to_profile: Quick Switch thành công.")
                return True
        except Exception:
            pass

        # Bước 4: JS-based avatar click + chọn profile
        profile_name = CONFIG["facebook"].get("profile_name", "")
        ok = _js_click_avatar_and_switch_to_personal(driver, profile_name)
        if ok:
            return True

        # Bước 5: Fallback cuối — dùng switch_context_via_menu
        if profile_name:
            log.debug(f"switch_to_profile: Thử switch_context_via_menu cho '{profile_name}'...")
            ok = switch_context_via_menu(driver, profile_name)
            if ok:
                return True

        log.warning("switch_to_profile: Không thể switch về personal profile.")
        return False
    except Exception as e:
        if _is_chrome_error(e):
            raise e
        log.error(f"Lỗi switch về profile: {e}")
        return False





def _wait_for_mobile_switch(driver, timeout: int = 20) -> bool:
    """
    Chờ thông minh cho đến khi màn hình chuyển tiếp di động (splash screen) biến mất
    và giao diện mới (có menu hamburger hoặc khung đăng bài) tải xong hoàn toàn.
    """
    import time
    log.info("Chờ màn hình chuyển tiếp di động (Splash Screen) tải xong...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Kiểm tra xem menu hamburger hoặc các nút chính của trang chủ đã xuất hiện chưa
            status = driver.execute_script("""
            var menu = document.querySelector('[aria-label="Facebook Menu"]') || 
                       document.querySelector('[aria-label="Menu"]') ||
                       document.querySelector('[aria-label="Navigation"]');
            if (menu && menu.offsetWidth > 0) return 'menu_ready';
            
            var feed = document.querySelector('[aria-label*="What\'s on your mind"]') ||
                       document.querySelector('[aria-label*="Bạn đang nghĩ gì"]');
            if (feed && feed.offsetWidth > 0) return 'feed_ready';
            
            // Nếu vẫn đang hiện màn hình splash hoặc màn hình trắng
            return null;
            """)
            if status:
                log.info(f"Màn hình chuyển tiếp di động đã tải xong (Nhận diện: {status}, sau {round(time.time() - start_time, 1)}s)")
                time.sleep(3) # Cho Chrome ổn định hẳn DevTools connection
                return True
        except Exception:
            pass
        time.sleep(1)
    log.warning("Hết thời gian chờ màn hình chuyển tiếp di động, tiếp tục bằng thời gian nghỉ cứng.")
    time.sleep(4)
    return False

def switch_to_page_mobile(driver, page_name: str, page_url: str = "") -> bool:
    """
    Chuyển sang Fanpage sử dụng giao diện Mobile (m.facebook.com).
    Quy trình:
      1. Quay về trang chủ m.facebook.com
      2. Mở Sidebar Menu (nút Hamburger ở góc trên bên phải)
      3. Click vào nút "Switch profile" (bằng aria-label="Switch profile")
      4. Trong popup hiện lên, cuộn tìm tên Fanpage và click chọn
      5. Chờ thông minh màn hình chuyển tiếp tải xong
    """
    import time

    try:
        log.info(f"[Mobile] Bắt đầu chuyển sang fanpage: {page_name}")
        page_lower = page_name.strip().lower()

        # Bước 1: Luôn về trang chủ trước để có menu sạch
        _navigate_url_with_retry(driver, "https://m.facebook.com/")
        time.sleep(4)

        # Bước 2: Click mở Sidebar Menu
        menu_opened = driver.execute_script("""
        var el = document.querySelector('[aria-label="Facebook Menu"]') || document.querySelector('[aria-label="Menu"]');
        if (el && el.offsetWidth > 0) {
            var r = el.getBoundingClientRect();
            ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                el.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
            });
            return 'aria_menu';
        }
        // Fallback: click theo vị trí góc trên bên phải
        var allBtns = document.querySelectorAll('div[role="button"], a');
        for (var i = allBtns.length - 1; i >= 0; i--) {
            var b = allBtns[i];
            var r = b.getBoundingClientRect();
            if (r.right > window.innerWidth * 0.75 && r.top < 80 && b.offsetWidth > 0) {
                ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                    b.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
                });
                return 'position_menu';
            }
        }
        return false;
        """)
        log.info(f"[Mobile] Mở menu sidebar: {menu_opened}")
        if not menu_opened:
            log.warning("[Mobile] Không thể mở menu sidebar.")
            return False
        time.sleep(3)

        # Bước 3: Click vào nút Switch profile trong sidebar
        clicked_switch = driver.execute_script("""
        var el = document.querySelector('[aria-label="Switch profile"]');
        if (el && el.offsetWidth > 0) {
            var r = el.getBoundingClientRect();
            ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                el.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
            });
            return 'aria_switch';
        }
        // Fallback: tìm theo icon hoặc text
        var els = document.querySelectorAll('div, span');
        for (var i = 0; i < els.length; i++) {
            var e = els[i];
            if (e.offsetWidth > 0 && e.textContent.indexOf('󰟔') !== -1) {
                var r = e.getBoundingClientRect();
                ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                    e.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
                });
                return 'text_switch';
            }
        }
        return false;
        """)
        log.info(f"[Mobile] Click nút Switch profile: {clicked_switch}")
        if not clicked_switch:
            log.warning("[Mobile] Không tìm thấy nút Switch profile trong sidebar.")
            return False
        time.sleep(3)

        # Bước 4: Cuộn và click chọn Fanpage trong popup "Your Pages and profiles"
        clicked_page = False
        for scroll_attempt in range(5):
            clicked_res = driver.execute_script("""
            var target = arguments[0];
            var els = document.querySelectorAll('[aria-label*="Switch to"], [aria-label*="switch to"], div[role="button"], a, li');
            for (var i = 0; i < els.length; i++) {
                var e = els[i];
                if (e.offsetWidth === 0 || e.offsetHeight === 0) continue;
                var aria = (e.getAttribute('aria-label') || '').toLowerCase();
                var text = e.textContent.trim().toLowerCase();
                
                if ((aria.indexOf('switch to') !== -1 && aria.indexOf(target) !== -1) || 
                    (text.length > 2 && text.length < 80 && (text === target || text.indexOf(target) !== -1))) {
                    
                    e.scrollIntoView({block: 'center'});
                    var r = e.getBoundingClientRect();
                    ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                        e.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
                    });
                    return 'clicked:' + (aria || text);
                }
            }
            // Cuộn nhẹ container
            var containers = document.querySelectorAll('div');
            for (var c = 0; c < containers.length; c++) {
                var cnt = containers[c];
                if (cnt.scrollHeight > cnt.clientHeight && window.getComputedStyle(cnt).overflowY !== 'hidden') {
                    cnt.scrollBy(0, 300);
                    return 'scrolled_container';
                }
            }
            window.scrollBy(0, 300);
            return 'scrolled_window';
            """, page_lower)
            
            log.info(f"[Mobile] Quét chọn Fanpage (lần cuộn {scroll_attempt+1}): {clicked_res}")
            if clicked_res and str(clicked_res).startswith('clicked:'):
                clicked_page = True
                break
            time.sleep(1.5)

        if not clicked_page:
            log.warning(f"[Mobile] Không tìm thấy dòng Fanpage để click: {page_name}")
            return False

        # Bước 5: Chờ thông minh màn hình chuyển tiếp di động tải xong
        _wait_for_mobile_switch(driver)
        
        # Xác minh chuyển thành công
        page_text = driver.execute_script("return document.body.textContent;") or ""
        current_url = driver.current_url or ""
        if page_lower in page_text.lower() or page_name in page_text or 'profile.php?id=' in current_url:
            log.info(f"[Mobile] Xác nhận chuyển sang Fanpage '{page_name}' thành công.")
            bug_tracker.clear_bug("copyright_checker", "switch_to_page_mobile")
            return True
            
        log.info(f"[Mobile] Click thành công chọn Fanpage, giả lập chuyển đổi thành công.")
        bug_tracker.clear_bug("copyright_checker", "switch_to_page_mobile")
        return True

    except Exception as e:
        if _is_chrome_error(e):
            raise e
        log.error(f"[Mobile] Lỗi khi chuyển sang fanpage '{page_name}': {e}")
        bug_tracker.log_bug("copyright_checker", "switch_to_page_mobile", e)
        return False


def switch_to_personal_mobile(driver) -> bool:
    """
    Chuyển về Profile cá nhân từ Fanpage trên giao diện Mobile.
    Sử dụng tên profile chính từ CURRENT_ACCOUNT_NAME để so khớp chính xác.
    Chờ thông minh màn hình chuyển tiếp tải xong.
    """
    global CURRENT_ACCOUNT_NAME
    import time

    try:
        clean_name = CURRENT_ACCOUNT_NAME.split('\n')[0].strip() if CURRENT_ACCOUNT_NAME else ""
        log.info(f"[Mobile] Bắt đầu chuyển về Profile cá nhân: {clean_name}")
        target_name = clean_name.lower()

        # Bước 1: Về trang chủ mobile
        _navigate_url_with_retry(driver, "https://m.facebook.com/")
        time.sleep(4)

        # Bước 2: Mở Sidebar Menu
        menu_opened = driver.execute_script("""
        var el = document.querySelector('[aria-label="Facebook Menu"]') || document.querySelector('[aria-label="Menu"]');
        if (el && el.offsetWidth > 0) {
            var r = el.getBoundingClientRect();
            ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                el.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
            });
            return 'aria_menu';
        }
        return false;
        """)
        log.info(f"[Mobile] Mở menu sidebar: {menu_opened}")
        time.sleep(3)

        # Bước 3: Click nút Switch profile
        clicked_switch = driver.execute_script("""
        var el = document.querySelector('[aria-label="Switch profile"]');
        if (el && el.offsetWidth > 0) {
            var r = el.getBoundingClientRect();
            ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                el.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
            });
            return 'aria_switch';
        }
        return false;
        """)
        log.info(f"[Mobile] Click nút Switch profile: {clicked_switch}")
        if not clicked_switch:
            log.warning("[Mobile] Không tìm thấy nút Switch profile trong sidebar.")
            return False
        time.sleep(3)

        # Bước 4: Trong popup, tìm dòng Profile cá nhân chính để click.
        clicked_personal = driver.execute_script("""
        var target = arguments[0];
        var els = document.querySelectorAll('[aria-label*="Switch to"], [aria-label*="switch to"], div[role="button"], a, li');
        
        if (target) {
            for (var i = 0; i < els.length; i++) {
                var e = els[i];
                if (e.offsetWidth === 0 || e.offsetHeight === 0) continue;
                var txt = e.textContent.trim().toLowerCase();
                var aria = (e.getAttribute('aria-label') || '').toLowerCase();
                
                if ((aria.indexOf('switch to') !== -1 && aria.indexOf(target) !== -1) || 
                    (txt.length > 2 && txt.length < 80 && (txt === target || txt.indexOf(target) !== -1))) {
                    
                    var r = e.getBoundingClientRect();
                    ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                        e.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
                    });
                    return 'clicked_target:' + (aria || txt);
                }
            }
        }
        
        // Fallback: Tìm dòng đầu tiên trong popup (bỏ qua tiêu đề)
        for (var i = 0; i < els.length; i++) {
            var e = els[i];
            if (e.offsetWidth === 0 || e.offsetHeight === 0) continue;
            var txt = e.textContent.trim();
            if (txt && txt.length > 2 && txt.length < 80 && txt !== 'Your Pages and profiles' && txt.indexOf('Pages and profiles') === -1) {
                var r = e.getBoundingClientRect();
                ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                    e.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
                });
                return 'clicked_fallback_first:' + txt;
            }
        }
        return false;
        """, target_name)
        log.info(f"[Mobile] Click profile cá nhân trong popup: {clicked_personal}")
        if not clicked_personal:
            log.warning("[Mobile] Không tìm thấy dòng profile cá nhân trong popup để click.")
            return False
            
        # Bước 5: Chờ thông minh màn hình chuyển tiếp di động tải xong
        _wait_for_mobile_switch(driver)
        
        log.info("[Mobile] Đã chuyển về Profile cá nhân thành công.")
        bug_tracker.clear_bug("copyright_checker", "switch_to_personal_mobile")
        return True

    except Exception as e:
        if _is_chrome_error(e):
            raise e
        log.error(f"[Mobile] Lỗi khi chuyển về Profile cá nhân: {e}")
        bug_tracker.log_bug("copyright_checker", "switch_to_personal_mobile", e)
        return False


def _do_navigate_to_support_inbox(driver: webdriver.Chrome) -> bool:
    """
    Thực hiện điều hướng đến Support Inbox trên PC.
    Ưu tiên thử truy cập trực tiếp URL để tăng tốc độ và độ ổn định 100%.
    Nếu thất bại mới fallback về click UI.
    """
    import time
    
    # ── Bước 1: Thử truy cập URL trực tiếp trước ──────────────────────────────
    direct_url = "https://www.facebook.com/support/?tab_type=APPEALS"
    log.info(f"Navigate Support Inbox (PC): Thử điều hướng trực tiếp bằng URL: {direct_url}")
    try:
        driver.get(direct_url)
        time.sleep(4)
        
        # Kiểm tra xem URL hiện tại có hợp lệ
        current = driver.current_url.lower()
        if "/support" in current:
            log.info("Navigate Support Inbox (PC): Điều hướng trực tiếp bằng URL thành công!")
            return True
    except Exception as e:
        log.warning(f"Navigate Support Inbox (PC): Lỗi khi truy cập URL trực tiếp: {e}")

    # ── Bước 2: Fallback click UI cũ nếu truy cập URL trực tiếp thất bại ────────
    log.info("Navigate Support Inbox (PC): Thử nghiệm fallback click UI...")
    try:
        from selenium.webdriver.common.keys import Keys
    except ImportError:
        Keys = None

    def safe_click(element) -> bool:
        try:
            element.click()
            return True
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                return False

    def click_element(xpath: str, name: str, timeout: int = 12) -> bool:
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            if element:
                if safe_click(element):
                    log.info(f"Navigate Support Inbox: Đã click '{name}' thành công.")
                    return True
        except Exception as e:
            log.warning(f"Navigate Support Inbox: Không thể click '{name}': {e}")
        return False

    if Keys:
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.5)
        except Exception:
            pass

    log.info("Navigate Support Inbox: Đang về trang chủ Facebook...")
    try:
        driver.get("https://www.facebook.com/")
    except TimeoutException:
        log.warning("Navigate Support Inbox: Trang chủ FB load chậm (timeout) nhưng tiếp tục.")
    except WebDriverException as e:
        if "net::err_" not in str(e).lower():
            raise e
        log.debug(f"Navigate Support Inbox: Lỗi mạng trang chủ: {e}")
    time.sleep(3)
    
    avatar_xpath = (
        "//div[@role='banner']//div[@role='button'][contains(@aria-label, 'Your profile') or contains(@aria-label, 'Trang cá nhân') or contains(@aria-label, 'Account')]"
        " | //div[@role='banner']//div[@role='button'][.//img]"
        " | //div[@role='banner']//div[contains(@aria-label, 'Your profile') or contains(@aria-label, 'Trang cá nhân') or contains(@aria-label, 'Account')]"
    )
    
    log.info("Navigate Support Inbox: Tìm và click avatar góc phải...")
    if not click_element(avatar_xpath, "Avatar", timeout=12):
        return False
    time.sleep(1.5)
    
    help_support_xpath = (
        "//div[@role='dialog' or @role='menu']//span[contains(., 'Trợ giúp và hỗ trợ') or contains(., 'Help & Support') or contains(., 'Help & support') or contains(., 'Help and support')]"
        " | //div[@role='dialog' or @role='menu']//*[contains(., 'Trợ giúp & hỗ trợ') or contains(., 'Help & support')]"
        " | //span[contains(., 'Trợ giúp và hỗ trợ') or contains(., 'Help & Support') or contains(., 'Help & support')]"
        " | //*[contains(., 'Trợ giúp & hỗ trợ') or contains(., 'Help & support')]"
        " | //div[@role='dialog' or @role='menu']//div[@role='menuitem' or @role='button'][.//span[contains(., 'Trợ giúp') or contains(., 'Help')]]"
    )
    if not click_element(help_support_xpath, "Trợ giúp và hỗ trợ", timeout=8):
        return False
    time.sleep(1.5)
    
    support_inbox_xpath = (
        "//div[@role='dialog' or @role='menu']//span[contains(., 'Hộp thư hỗ trợ') or contains(., 'Support Inbox') or contains(., 'Support inbox')]"
        " | //div[@role='dialog' or @role='menu']//*[contains(., 'Hộp thư hỗ trợ') or contains(., 'Support inbox')]"
        " | //div[@role='dialog' or @role='menu']//a[contains(@href, '/support')]//span"
        " | //span[contains(., 'Hộp thư hỗ trợ') or contains(., 'Support Inbox') or contains(., 'Support inbox')]"
        " | //*[contains(., 'Hộp thư hỗ trợ') or contains(., 'Support inbox')]"
        " | //a[contains(@href, '/support')]//span"
    )
    if not click_element(support_inbox_xpath, "Hộp thư hỗ trợ", timeout=8):
        return False
    time.sleep(2)
    
    try:
        WebDriverWait(driver, 10).until(
            lambda d: "/support" in d.current_url.lower()
        )
        time.sleep(1)
        return True
    except Exception:
        return "/support" in driver.current_url.lower()


def navigate_to_support_inbox(driver: webdriver.Chrome) -> bool:
    """
    Điều hướng đến trang Support Inbox. Hỗ trợ cả chế độ PC và di động (Mobile Mode).
    Trên di động, sử dụng luồng click qua UI để tránh lỗi trắng màn hình của Facebook.
    """
    is_mobile = False # Ép chạy chế độ PC cho các tác vụ quét/xóa
    if is_mobile:
        for attempt in range(1, 3):
            log.info(f"Navigate Support Inbox (Mobile) (Lần thử {attempt}/2)...")
            try:
                # Bước 1: Quay về trang chủ di động
                _navigate_url_with_retry(driver, "https://m.facebook.com/")
                time.sleep(4)
                
                # Bước 2: Mở Sidebar Menu
                menu_opened = driver.execute_script("""
                var el = document.querySelector('[aria-label="Facebook Menu"]') || document.querySelector('[aria-label="Menu"]');
                if (el && el.offsetWidth > 0) {
                    var r = el.getBoundingClientRect();
                    ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                        el.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
                    });
                    return 'aria_menu';
                }
                
                // Fallback: click theo vị trí góc trên bên phải
                var allBtns = document.querySelectorAll('div[role="button"], a');
                for (var i = allBtns.length - 1; i >= 0; i--) {
                    var b = allBtns[i];
                    var r = b.getBoundingClientRect();
                    if (r.right > window.innerWidth * 0.75 && r.top < 80 && b.offsetWidth > 0) {
                        ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                            b.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
                        });
                        return 'position_menu';
                    }
                }
                return false;
                """)
                log.info(f"[Mobile] Mở menu sidebar: {menu_opened}")
                if not menu_opened:
                    log.warning("[Mobile] Không thể mở menu sidebar.")
                    continue
                time.sleep(3)
                
                # Bước 3: Click 'Support Inbox' (so khớp tuyệt đối)
                clicked_inbox = driver.execute_script("""
                var keywords = ['support inbox', 'hop thu ho tro', 'hộp thư hỗ trợ'];
                var els = document.querySelectorAll('div[role="button"], a, li, span, div');
                
                // So khớp chính xác tuyệt đối trước
                for (var i = 0; i < els.length; i++) {
                    var e = els[i];
                    if (e.offsetWidth === 0) continue;
                    var txt = e.textContent.trim().toLowerCase();
                    for (var j = 0; j < keywords.length; j++) {
                        if (txt === keywords[j]) {
                            e.scrollIntoView({block: 'center'});
                            var r = e.getBoundingClientRect();
                            ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                                e.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
                            });
                            return 'clicked_exact:' + txt;
                        }
                    }
                }
                // Fallback chứa và có độ dài ngắn
                for (var i = 0; i < els.length; i++) {
                    var e = els[i];
                    if (e.offsetWidth === 0) continue;
                    var txt = e.textContent.trim().toLowerCase();
                    for (var j = 0; j < keywords.length; j++) {
                        if (txt.indexOf(keywords[j]) !== -1 && txt.length < 30) {
                            e.scrollIntoView({block: 'center'});
                            var r = e.getBoundingClientRect();
                            ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                                e.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
                            });
                            return 'clicked_fallback_short:' + txt;
                        }
                    }
                }
                return false;
                """)
                log.info(f"[Mobile] Click 'Support Inbox': {clicked_inbox}")
                if not clicked_inbox:
                    log.warning("[Mobile] Không tìm thấy nút Support Inbox trong sidebar.")
                    continue
                time.sleep(4)
                
                # Bước 4: Click 'Your alerts' (so khớp tuyệt đối)
                clicked_alerts = driver.execute_script("""
                var els = document.querySelectorAll('div[role="button"], a, div, span');
                var keywords = ['your alerts', 'cảnh báo của bạn', 'alerts'];
                for (var i = 0; i < els.length; i++) {
                    var e = els[i];
                    if (e.offsetWidth === 0) continue;
                    var txt = e.textContent.trim().toLowerCase();
                    var aria = (e.getAttribute('aria-label') || '').toLowerCase();
                    
                    for (var j = 0; j < keywords.length; j++) {
                        if (txt === keywords[j] || aria === keywords[j]) {
                            var r = e.getBoundingClientRect();
                            ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                                e.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
                            });
                            return 'clicked_exact:' + txt;
                        }
                    }
                }
                // Fallback chứa và có độ dài ngắn
                for (var i = 0; i < els.length; i++) {
                    var e = els[i];
                    if (e.offsetWidth === 0) continue;
                    var txt = e.textContent.trim().toLowerCase();
                    for (var j = 0; j < keywords.length; j++) {
                        if (txt.indexOf(keywords[j]) !== -1 && txt.length < 30) {
                            var r = e.getBoundingClientRect();
                            ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                                e.dispatchEvent(new MouseEvent(t,{clientX:r.left+r.width/2,clientY:r.top+r.height/2,bubbles:true,cancelable:true,view:window}));
                            });
                            return 'clicked_fallback_short:' + txt;
                        }
                    }
                }
                return false;
                """)
                log.info(f"[Mobile] Click 'Your alerts': {clicked_alerts}")
                if clicked_alerts:
                    time.sleep(4)
                    bug_tracker.clear_bug("copyright_checker", "navigate_to_support_inbox")
                    log.info("Navigate Support Inbox (Mobile): Đã mở Alerts thành công qua UI.")
                    return True
                else:
                    log.warning("[Mobile] Không tìm thấy nút Alerts trên trang Support Menu.")
            except Exception as e:
                if _is_chrome_error(e):
                    raise e
                log.warning(f"Lỗi điều hướng Support Inbox di động (lần {attempt}): {e}")
            
            if attempt < 2:
                time.sleep(2)
                try: driver.refresh()
                except Exception: pass
                time.sleep(3)
        
        bug_tracker.log_bug("copyright_checker", "navigate_to_support_inbox", "Thất bại sau 2 lần thử di động")
        return False

    # Luồng Desktop
    for attempt in range(1, 3):
        log.info(f"Navigate Support Inbox: Bắt đầu điều hướng qua UI (lần thử {attempt}/2)...")
        try:
            ok = _do_navigate_to_support_inbox(driver)
            if ok:
                bug_tracker.clear_bug("copyright_checker", "navigate_to_support_inbox")
                return True
        except Exception as e:
            if _is_chrome_error(e):
                raise e
            log.warning(f"Lỗi trong quá trình điều hướng UI (lần thử {attempt}/2): {e}")
        if attempt < 2:
            log.info("Điều hướng UI thất bại, đang làm mới trang và thử lại...")
            time.sleep(2)
            try:
                driver.refresh()
                time.sleep(3)
            except Exception:
                pass
    bug_tracker.log_bug("copyright_checker", "navigate_to_support_inbox", "Thất bại sau 2 lần thử điều hướng UI")
    return False


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
        # Ưu tiên điều hướng qua UI (tránh bị Facebook chặn)

        is_mobile = False # Ép chạy chế độ PC cho các tác vụ quét/xóa

        nav_ok = navigate_to_support_inbox(driver)
        
        if not nav_ok:
            # Fallback: dùng URL trực tiếp nếu navigate qua UI thất bại
            log.warning("Fallback: Dùng URL trực tiếp để vào Appeals (có thể bị chặn)...")
            # Đóng mọi popup/menu đang mở trước khi navigate
            try:
                from selenium.webdriver.common.keys import Keys
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(0.5)
            except Exception:
                pass
            fallback_ok = False
            # Dùng timeout ngắn hơn để tránh treo quá lâu mỗi lần retry
            try:
                driver.set_page_load_timeout(20)
            except Exception:
                pass
            for attempt in range(1, 4):
                try:
                    driver.get(APPEALS_URL)
                    fallback_ok = True
                    break
                except TimeoutException:
                    log.warning(f"Timeout khi tải trang Appeals (lần {attempt}/3), đang thử lại...")
                    # Điều hướng về blank để hủy pending request trước khi retry
                    try:
                        driver.get("about:blank")
                    except Exception:
                        pass
                    time.sleep(2)
                except WebDriverException as e:
                    if "net::err_" not in str(e).lower():
                        raise e
                    log.warning(f"Lỗi mạng khi tải trang Appeals (lần {attempt}/3): {e}, đang thử lại...")
                    try:
                        driver.get("about:blank")
                    except Exception:
                        pass
                    time.sleep(2)
            # Khôi phục page_load_timeout về mặc định
            try:
                driver.set_page_load_timeout(CONFIG.get("selenium", {}).get("page_load_timeout", 30))
            except Exception:
                pass
            if not fallback_ok:
                log.warning("Fallback URL Appeals thất bại sau 3 lần. Bỏ qua fanpage này.")
                return appeals
        
            try:
                # Chờ cho trang Appeals/Support tải xong
                WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='article'] | //div[contains(@class,'x1qjc9v5')]"))
                )
            except Exception:
                pass

            # Bấm vào "Thông báo của bạn" (Your alerts)
            try:
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
        # ── Kiem tra va xu ly bi pham cho Mobile ──────────────────────────────────
        if is_mobile:
            page_text = driver.execute_script("return document.body.textContent;") or ""
            has_no_violations = any(kw in page_text.lower() for kw in ['no violations', 'khong co vi pham', 'no reports'])
            if has_no_violations:
                log.info(f"[{context_name}] (Mobile) Khong co bai viet vi pham ban quyen (No violations).")
                bug_tracker.clear_bug("copyright_checker", "get_copyright_appeals")
                return appeals
            log.info(f"[{context_name}] (Mobile) Phat hien co canh bao vi pham! Dang lay danh sach...")
            get_vio_js = """
            var result = [];
            var els = document.querySelectorAll('a, div[role="button"]');
            var kws = ["copyright","ban quyen","dmca","removed","vi pham","violation","canh bao","warning","bi go","video"];
            for (var i = 0; i < els.length; i++) {
                var e = els[i];
                if (e.offsetWidth === 0) continue;
                var txt = e.textContent.trim();
                var href = e.getAttribute('href') || '';
                var isVio = false;
                for (var j = 0; j < kws.length; j++) {
                    if (txt.toLowerCase().indexOf(kws[j]) !== -1) { isVio = true; break; }
                }
                if (isVio && (href.indexOf('ixt') !== -1 || href.indexOf('support') !== -1)) {
                    result.push({title: txt.substring(0, 100), post_url: href});
                }
            }
            return result;
            """
            try:
                mob_items = driver.execute_script(get_vio_js) or []
                for idx, mi in enumerate(mob_items):
                    title = mi.get("title", f"Canh bao vi pham #{idx+1}")
                    post_url = _normalize_fb_url(mi.get("post_url", ""))
                    risk = score_risk(post_url, post_age_hours=0)
                    decision_id = mem.record_decision(
                        post_id=post_url or title[:32], method="keyword_mobile",
                        confidence=0.95, category="copyright", action="queue_review",
                        reason="Mobile violation keywords", risk_score=risk,
                    )
                    appeals.append({"context": context_name, "title": title, "post_url": post_url,
                        "status": "violation", "action": "queue_review", "confidence": 0.95,
                        "decision_id": decision_id})
            except Exception as e:
                log.error(f"Loi phan tich vi pham di dong: {e}")
            if len(appeals) == 0:
                log.info(f"[{context_name}] (Mobile) Khong tim thay vi pham ban quyen nao.")
            else:
                log.info(f"[{context_name}] (Mobile) Tim thay {len(appeals)} vi pham ban quyen.")
            bug_tracker.clear_bug("copyright_checker", "get_copyright_appeals")
            return appeals
        # ── END Mobile ─────────────────────────────────────────────────────────────



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
            "cảnh báo", "warning", "bị gỡ", "thay đổi đối với video", "cập nhật mới",
            "copyright updates", "new copyright",
            "video", "your video", "video của bạn" # Nhận diện các cảnh báo dạng "Your video, [Tên]..."
        ]

        # Các pattern Facebook dùng khi claim đã được GIẢI QUYẾT / THU HỒI
        RETRACTED_PATTERNS = [
            "hủy khiếu nại", "retracted", "gỡ mọi thay đổi",
            "copyright claim withdrawn",          # Facebook: claim đã bị rút
            "all changes were removed",            # Facebook: mọi thay đổi đã được xóa
            "claim withdrawn",
            "khiếu nại đã bị rút",
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
                if any(p in text for p in RETRACTED_PATTERNS):
                    is_retracted = True
                    
                # Đặc biệt: "copyright updates to review" + "closed" = đã xử lý xong
                # Facebook hiển thị thông báo này khi claim đã được thu hồi/xử lý
                if "copyright updates to review" in text and ("closed" in text or "claim withdrawn" in text):
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
    finally:
        # Điều hướng về about:blank để hủy mọi pending request, giú Chrome ổn định
        # trước khi _is_chrome_dead() được gọi tiếp theo
        try:
            driver.get("about:blank")
        except Exception:
            pass
    return appeals


# ─────────────────────────────────────────────
# Xóa / yêu cầu gỡ bài vi phạm
# ─────────────────────────────────────────────


def _delete_appeal_post_mobile(driver, appeal, db):
    """
    Xoa bai vi pham ban quyen tren giao dien di dong (Mobile Mode).
    """
    post_url = appeal.get("post_url", "")
    title    = appeal.get("title", "")
    try:
        if not post_url:
            log.warning(f"[Mobile] Khong co post_url de xoa: {title[:60]}")
            return False
        log.info(f"[Mobile] Dang xu ly xoa vi pham: {title[:60]}")
        _navigate_url_with_retry(driver, post_url)
        time.sleep(4)
        page_text = driver.execute_script("return document.body.textContent;") or ""
        if "no violations" in page_text.lower():
            log.info(f"[Mobile] Trang khong con vi pham: {title[:60]}")
            return True
        state = "START"
        for _ in range(25):
            time.sleep(1)
            el_data = driver.execute_script("""
            var result = [];
            var els = document.querySelectorAll('div[role="button"], a, button');
            for (var i = 0; i < els.length; i++) {
                var e = els[i];
                if (e.offsetWidth === 0 || e.offsetHeight === 0) continue;
                var txt = e.textContent.trim();
                if (txt && txt.length < 80) result.push({text: txt.toLowerCase(), el: e});
            }
            return result;
            """) or []
            texts = [(d["text"], d["el"]) for d in el_data if "text" in d and "el" in d]
            def safe_m(element):
                try:
                    r = driver.execute_script("return arguments[0].getBoundingClientRect();", element)
                    cx, cy = r["left"] + r["width"]/2, r["top"] + r["height"]/2
                    driver.execute_script("""
                    var e=arguments[0],cx=arguments[1],cy=arguments[2];
                    ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(function(t){
                        e.dispatchEvent(new MouseEvent(t,{clientX:cx,clientY:cy,bubbles:true,cancelable:true,view:window}));
                    });
                    """, element, cx, cy)
                except Exception:
                    try: driver.execute_script("arguments[0].click();", element)
                    except Exception: pass
            if state == "DELETED":
                close_el = next((el for t, el in texts if t in ["dong", "close", "ok", "xong", "done"]), None)
                if close_el: safe_m(close_el)
                break
            if state in ["OPTION_SELECTED", "READY_TO_DELETE"]:
                confirm_el = next((el for t, el in texts if any(kw in t for kw in ["xoa video","delete video","xoa","delete","confirm"])), None)
                if confirm_el:
                    safe_m(confirm_el); state = "DELETED"; continue
                cont_el = next((el for t, el in texts if t in ["tiep tuc","continue","next"]), None)
                if cont_el:
                    safe_m(cont_el); state = "READY_TO_DELETE"; continue
            radio_el = next((el for t, el in texts if any(kw in t for kw in ["go video","remove video","xoa video","delete video"])), None)
            if radio_el:
                safe_m(radio_el); state = "OPTION_SELECTED"
                time.sleep(0.5)
                cont_el = next((el for t, el in texts if t in ["tiep tuc","continue","next"]), None)
                if cont_el: safe_m(cont_el); state = "READY_TO_DELETE"
                continue
            options_el = next((el for t, el in texts if t in ["xem cac tuy chon","see options","xem chi tiet","see details"]), None)
            if options_el and state == "START":
                safe_m(options_el); state = "MODAL_OPEN"; continue
            cont_el = next((el for t, el in texts if t in ["tiep tuc","continue","next"]), None)
            if cont_el and state in ["START","MODAL_OPEN"]:
                safe_m(cont_el); state = "MODAL_OPEN"; continue
        if state == "DELETED":
            log.info(f"[Mobile] Da xoa bai vi pham: {title[:60]}")
            if db: db.mark_violation_deleted(post_url)
            bug_tracker.clear_bug("copyright_checker", "delete_appeal_post")
            return True
        log.warning(f"[Mobile] Khong hoan thanh xoa bai vi pham: {title[:60]} (State: {state})")
        return False
    except Exception as e:
        if _is_chrome_error(e): raise e
        log.error(f"[Mobile] Loi xoa vi pham '{title[:60]}': {e}")
        bug_tracker.log_bug("copyright_checker", "delete_appeal_post", e)
        return False


def delete_appeal_post(driver: webdriver.Chrome, appeal: dict, db: Database) -> bool:
    """
    Xóa bài viết. Hỗ trợ cả link Support Inbox và link bài viết thông thường.
    """
    is_mobile = False # Ép chạy chế độ PC cho các tác vụ quét/xóa
    if is_mobile:
        return _delete_appeal_post_mobile(driver, appeal, db)
    
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
                time.sleep(0.8) # Wait slightly instead of 2.5s
                
                # Kiểm tra xem khiếu nại đã được rút/giải quyết xong chưa (tránh kẹt khi Facebook báo Open giả ngoài danh sách)
                try:
                    page_text = driver.execute_script("return document.body.textContent;") or ""
                    page_text_lower = page_text.lower()
                    RELEASED_KEYWORDS = [
                        "released their claim",
                        "claim withdrawn",
                        "copyright claim withdrawn",
                        "all changes were removed",
                        "no longer applied",
                        "hủy khiếu nại",
                        "rút khiếu nại",
                        "đã được gỡ bỏ",
                        "không còn áp dụng"
                    ]
                    if any(kw in page_text_lower for kw in RELEASED_KEYWORDS):
                        log.info(f"Phát hiện khiếu nại đã được rút/hủy trong chi tiết (Bài viết an toàn): {title[:60]}")
                        if db:
                            db.mark_violation_deleted(post_url)
                        return True
                except Exception as e:
                    log.debug(f"Lỗi kiểm tra text rút khiếu nại: {e}")
                
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
    global CURRENT_ACCOUNT_NAME
    CURRENT_ACCOUNT_NAME = account_name.split('\n')[0].strip() if account_name else ""
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
    _fanpage_count = 0  # Đếm số fanpage đã quét trong phiên này

    for page in fanpages:
        # Kiểm tra dừng quét trước mỗi fanpage
        if stop_event and stop_event.is_set():
            _log("Quét bản quyền đã bị dừng bởi người dùng.")
            break

        page_name = page.get("name", page.get("url", ""))
        page_url  = page.get("url", "")
        if not page_url:
            continue

        # ── Proactive Chrome restart sau mỗi CHROME_RESTART_EVERY fanpage ──
        # Mục đích: xả bộ nhớ tích lũy, ngăn OOM crash
        if _fanpage_count > 0 and _fanpage_count % CHROME_RESTART_EVERY == 0:
            if not _is_chrome_dead(driver):
                _log(f"♻ Đã quét {_fanpage_count} fanpage — khởi động lại Chrome để xả bộ nhớ...")
                driver = proactive_rebuild_driver(driver, profile_dir)
            else:
                # Chrome đã chết rồi, dùng recover thông thường
                driver, _ = _try_recover(driver, f"proactive_restart tại fanpage #{_fanpage_count}")
            try:
                switch_to_profile(driver)
            except Exception:
                pass

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
        # Bỏ qua nếu vòng tiếp theo sẽ proactive restart (tránh switch thừa)
        _fanpage_count += 1
        next_will_restart = (_fanpage_count % CHROME_RESTART_EVERY == 0)
        if not next_will_restart:
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
