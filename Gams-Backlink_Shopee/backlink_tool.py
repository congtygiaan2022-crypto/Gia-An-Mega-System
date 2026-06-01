#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
"""
╔══════════════════════════════════════════════════════════╗
║          SHOPEE BACKLINK TOOL  —  Hybrid Engine          ║
║  Tự động lấy tên sản phẩm từ danh sách link Shopee      ║
╚══════════════════════════════════════════════════════════╝
"""

import sys
import time
import threading
import re
import urllib.parse
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from tqdm import tqdm
from colorama import init, Fore, Style

# ─────────────────────────────────────────────
#   CẤU HÌNH  —  Chỉnh sửa tại đây
# ─────────────────────────────────────────────
NUM_THREADS     = 3          # Số Chrome chạy song song (khuyến nghị 2-4)
INPUT_FILE      = "Link_shopee.txt"
OUTPUT_FILE     = "ket_qua.txt"
PROFILE_BASE    = "chrome_profile"
MAX_RETRIES     = 3          # Thử lại tối đa khi lỗi
PAGE_TIMEOUT    = 25         # Giây chờ trang load
DELAY_PER_REQ   = 1.5        # Giây nghỉ giữa các request
HEADLESS        = False      # Chạy Chrome ẩn hay hiện (nên để False để tránh robot check)
USE_CHROME_ONLY = True       # Chạy trực tiếp bằng Chrome giả lập, bỏ qua Phase 1 (Requests) để tránh bị Shopee chặn bot
# ─────────────────────────────────────────────

init(autoreset=True)  # Colorama

BASE_DIR = Path(__file__).parent
PROFILE_DIR = BASE_DIR / PROFILE_BASE

# ══════════════════════════════════════════════
#   Shared state
# ══════════════════════════════════════════════
write_lock   = threading.Lock()
print_lock   = threading.Lock()
stats = {
    "success": 0,
    "failed":  0,
    "skipped": 0,
    "phase1_total": 0,
    "phase1_done": 0,
    "phase2_total": 0,
    "phase2_done": 0,
}
stats_lock = threading.Lock()
dashboard_callback = None
should_stop = False
total_urls_count = 0


# ══════════════════════════════════════════════
#   Console helpers
# ══════════════════════════════════════════════
BANNER = (
    f"{Fore.CYAN}===================================================={Style.RESET_ALL}\n"
    f"{Fore.YELLOW}   SHOPEE BACKLINK TOOL  --  Hybrid Engine v2.0   {Style.RESET_ALL}\n"
    f"{Fore.CYAN}  Tu dong lay ten san pham tu link Shopee (Multi-Thread) {Style.RESET_ALL}\n"
    f"{Fore.CYAN}===================================================={Style.RESET_ALL}\n"
)

def cprint(msg, color=Fore.WHITE, prefix_type="INFO", pbar=None):
    prefix = ""
    if prefix_type == "INFO":
        prefix = f"{Fore.BLUE}[INFO]{Style.RESET_ALL} "
    elif prefix_type == "SUCCESS":
        prefix = f"{Fore.GREEN}[OK]{Style.RESET_ALL}   "
    elif prefix_type == "ERROR":
        prefix = f"{Fore.RED}[ERR]{Style.RESET_ALL}  "
    elif prefix_type == "WARN":
        prefix = f"{Fore.YELLOW}[WARN]{Style.RESET_ALL} "
        
    line = f"{prefix}{color}{msg}{Style.RESET_ALL}"
    
    if dashboard_callback:
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_msg = ansi_escape.sub('', msg)
        dashboard_callback(clean_msg, prefix_type)

    with print_lock:
        try:
            if pbar:
                pbar.write(line)
            else:
                print(line)
        except UnicodeEncodeError:
            safe = line.encode("ascii", errors="replace").decode("ascii")
            if pbar:
                pbar.write(safe)
            else:
                print(safe)


# ══════════════════════════════════════════════
#   Resume: đọc kết quả đã có
# ══════════════════════════════════════════════
def load_existing_results(output_path: Path) -> dict:
    existing = {}
    if not output_path.exists():
        return existing
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) == 3:
                try:
                    idx  = int(parts[0].strip())
                    name = parts[1].strip()
                    url  = parts[2].strip()
                    existing[idx] = (name, url)
                except ValueError:
                    pass
    return existing


# ══════════════════════════════════════════════
#   Đọc danh sách link đầu vào
# ══════════════════════════════════════════════
def load_input_urls(input_path: Path) -> list:
    urls = []
    with open(input_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            url = line.strip()
            if url and url.startswith("http"):
                urls.append((i, url))
    return urls


# ══════════════════════════════════════════════
#   Chrome driver factory
def clear_profile_locks(profile_path: Path):
    """Xóa các file lock của Chrome để tránh lỗi DevToolsActivePort khi khởi động lại"""
    if not profile_path.exists():
        return
    lock_files = [
        profile_path / "lock",
        profile_path / "lockfile",           # Windows Chrome dùng 'lockfile', không phải 'lock'
        profile_path / "SingletonLock",
        profile_path / "SingletonCookie",
        profile_path / "SingletonSocket",
        profile_path / "DevToolsActivePort",
        profile_path / "Default" / "lock",
        profile_path / "Default" / "lockfile",
        profile_path / "Default" / "SingletonLock",
        profile_path / "Default" / "SingletonCookie",
        profile_path / "Default" / "SingletonSocket",
        profile_path / "Default" / "DevToolsActivePort",
    ]
    for p in lock_files:
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass

def clear_profile_cookies(profile_path: Path):
    """Xóa file cookies để xóa dấu hiệu bot bị Shopee gắn thẻ phạt"""
    if not profile_path.exists():
        return
    cookie_paths = [
        profile_path / "Default" / "Network" / "Cookies",
        profile_path / "Default" / "Cookies",
        profile_path / "Default" / "Network" / "Cookies-journal",
        profile_path / "Default" / "Cookies-journal"
    ]
    for p in cookie_paths:
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass

def force_kill_chrome_for_profile(profile_path: Path):
    """
    Ép tắt Chrome process đang dùng profile này.
    Cần thiết trước khi restart để tránh file lock khiến sync_profile_data thất bại.
    """
    if profile_path is None:
        return
    profile_name = profile_path.name  # e.g. "shopee_profile_1"
    try:
        ps_script = (
            "Get-CimInstance Win32_Process | "
            f"Where-Object {{ $_.Name -eq 'chrome.exe' -and $_.CommandLine -like '*{profile_name}*' }} | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
        )
        subprocess.run(
            ['powershell', '-NoProfile', '-WindowStyle', 'Hidden', '-Command', ps_script],
            capture_output=True, timeout=10
        )
    except Exception:
        pass
    time.sleep(2)

def fix_local_state_profile(dest_profile: Path):
    """
    Sửa file Local State của profile thread để Chrome luôn mở đúng profile 'Default'
    (tránh bị mở nhầm sang profile cá nhân/làm việc của người dùng).
    """
    local_state_path = dest_profile / "Local State"
    if not local_state_path.exists():
        return
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)

        profile_section = local_state.get("profile", {})

        # Chỉ giữ lại profile 'Default' trong danh sách, xóa các profile khác
        info_cache = profile_section.get("info_cache", {})
        if info_cache:
            default_entry = info_cache.get("Default", {})
            profile_section["info_cache"] = {"Default": default_entry} if default_entry else {}

        # Đặt profile cuối cùng được dùng là 'Default'
        profile_section["last_used"] = "Default"
        local_state["profile"] = profile_section

        with open(local_state_path, "w", encoding="utf-8") as f:
            json.dump(local_state, f)
    except Exception:
        # Nếu không sửa được, xóa Local State để Chrome tự tạo lại (sạch nhất)
        try:
            local_state_path.unlink()
        except Exception:
            pass

CHROME_LOCK_NAMES = {
    "lockfile", "DevToolsActivePort",
    "SingletonLock", "SingletonSocket", "SingletonCookie",
}

def sync_profile_data(src_profile: Path, dest_profile: Path):
    """Clone profile gốc sang profile luồng, bỏ qua các file bị Chrome khóa"""
    import shutil

    if not src_profile.exists():
        return

    def _ignore_locks(directory, contents):
        """Bỏ qua lock files khi copy để tránh lỗi 'file in use'"""
        return [f for f in contents if f in CHROME_LOCK_NAMES]

    # Xóa profile cũ nếu tồn tại để clone sạch
    if dest_profile.exists():
        shutil.rmtree(dest_profile, ignore_errors=True)

    try:
        # Python 3.9+: ignore_errors=True tiếp tục copy kể cả khi gặp file bị lock
        shutil.copytree(str(src_profile), str(dest_profile),
                        ignore=_ignore_locks,
                        ignore_errors=True,
                        dirs_exist_ok=False)
    except TypeError:
        # Python < 3.9: không có ignore_errors → dùng copytree thường + bỏ qua exception
        try:
            shutil.copytree(str(src_profile), str(dest_profile),
                            ignore=_ignore_locks,
                            dirs_exist_ok=False)
        except Exception:
            pass
    except Exception:
        pass

    # Fallback nếu copytree không tạo được gì: copy file-by-file thủ công
    if not dest_profile.exists() or not any(dest_profile.iterdir()):
        dest_profile.mkdir(parents=True, exist_ok=True)
        for rel_path, path_type in [
            ("Default/Network/Cookies", "file"),
            ("Default/Cookies", "file"),
            ("Default/Preferences", "file"),
            ("Default/Secure Preferences", "file"),
            ("Default/Local Storage", "dir"),
            ("Default/IndexedDB", "dir"),
            ("Default/Session Storage", "dir"),
            ("Local State", "file"),
        ]:
            src_p = src_profile / rel_path
            dest_p = dest_profile / rel_path
            if not src_p.exists():
                continue
            try:
                dest_p.parent.mkdir(parents=True, exist_ok=True)
                if path_type == "file":
                    shutil.copy2(src_p, dest_p)
                else:
                    if dest_p.exists():
                        shutil.rmtree(dest_p, ignore_errors=True)
                    shutil.copytree(str(src_p), str(dest_p), ignore_errors=True)
            except Exception:
                pass

    # Luôn sửa Local State sau khi copy để ép Chrome dùng đúng profile 'Default'
    fix_local_state_profile(dest_profile)

# ══════════════════════════════════════════════
#   Cookies & Deduplication Helpers
# ══════════════════════════════════════════════
import json

def load_config():
    global NUM_THREADS, HEADLESS, USE_CHROME_ONLY
    config_path = BASE_DIR / "config.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                NUM_THREADS = int(data.get("NUM_THREADS", NUM_THREADS))
                HEADLESS = bool(data.get("HEADLESS", HEADLESS))
                USE_CHROME_ONLY = bool(data.get("USE_CHROME_ONLY", USE_CHROME_ONLY))
        except Exception as e:
            print(f"Loi doc config.json: {e}")

def write_and_sort_result(idx: int, product_name: str, short_url: str):
    """
    Ghi kết quả mới và tự động sắp xếp lại file kết quả theo số thứ tự (real-time)
    """
    output_path = BASE_DIR / OUTPUT_FILE
    
    with write_lock:
        # 1. Đọc tất cả các dòng hiện có
        existing_lines = {}
        if output_path.exists():
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split("|", 1)
                        try:
                            line_idx = int(parts[0].strip())
                            existing_lines[line_idx] = line
                        except ValueError:
                            pass
            except Exception:
                pass
                
        # 2. Bổ sung/cập nhật dòng kết quả mới
        new_line = f"{idx}|{product_name}|{short_url}"
        existing_lines[idx] = new_line
        
        # 3. Ghi đè lại toàn bộ file theo thứ tự đã sắp xếp
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for k in sorted(existing_lines.keys()):
                    f.write(existing_lines[k] + "\n")
                f.flush()
        except Exception as e:
            cprint(f"Lỗi ghi file kết quả: {e}", Fore.RED, "ERROR")

def load_saved_cookies() -> dict:
    """Đọc cookies từ file cookies.json (từ selenium) và format sang dạng dict cho thư viện requests"""
    cookies_path = PROFILE_DIR / "cookies.json"
    if not cookies_path.exists():
        return {}
    try:
        with open(cookies_path, "r", encoding="utf-8") as f:
            cookies_list = json.load(f)
            return {c["name"]: c["value"] for c in cookies_list}
    except Exception as e:
        cprint(f"Khong the doc cookies.json: {e}", Fore.YELLOW, "WARN")
        return {}

def load_existing_resolved_urls(output_path: Path) -> set:
    """Đọc các URL đã được quét thành công từ file kết quả để đối chiếu tránh trùng lặp"""
    resolved_urls = set()
    if not output_path.exists():
        return resolved_urls
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|", 2)
                if len(parts) == 3:
                    name = parts[1].strip()
                    url = parts[2].strip()
                    if name and name != "[KHÔNG LẤY ĐƯỢC TÊN]":
                        resolved_urls.add(url.lower().strip())
    except Exception as e:
        cprint(f"Loi doc ket qua de check trung: {e}", Fore.YELLOW, "WARN")
    return resolved_urls

# ══════════════════════════════════════════════
#   Chrome driver factory
# ══════════════════════════════════════════════
def create_driver(thread_id: int, is_multi: bool = False, force_sync: bool = True) -> tuple[webdriver.Chrome, Path]:
    if not is_multi:
        profile_path = PROFILE_DIR / "shopee_profile"
    else:
        profile_path = PROFILE_DIR / f"shopee_profile_{thread_id}"
        master_profile = PROFILE_DIR / "shopee_profile"
        if force_sync and master_profile.exists() and master_profile != profile_path:
            sync_profile_data(master_profile, profile_path)

    profile_path.mkdir(parents=True, exist_ok=True)
    clear_profile_locks(profile_path)

    opts = Options()
    opts.add_argument(f"--user-data-dir={profile_path.resolve()}")
    opts.add_argument("--profile-directory=Default")

    # Anti-detection (gộp excludeSwitches vào 1 lần gọi để tránh bị ghi đè)
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)

    # Ổn định & hiệu năng
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,800")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--log-level=3")

    if HEADLESS:
        opts.add_argument("--headless=new")

    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    }
    opts.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=opts)

    # Stealth JS toàn diện: che các fingerprint Shopee hay dùng để detect bot
    stealth_js = """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['vi-VN', 'vi', 'en-US', 'en']});
        window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}, app: {}};
        try {
            const origQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (p) =>
                p.name === 'notifications'
                    ? Promise.resolve({state: Notification.permission})
                    : origQuery(p);
        } catch(e) {}
    """
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": stealth_js})
    driver.set_page_load_timeout(PAGE_TIMEOUT)
    return driver, profile_path


# ══════════════════════════════════════════════
#   Làm sạch tên sản phẩm
# ══════════════════════════════════════════════
def clean_title(raw: str) -> str:
    suffixes = [
        " | Shopee Việt Nam",
        " | Shopee Vietnam",
        " - Shopee",
        " | Shopee",
        "- Mua bán online",
        " | Mua và Bán Trên Ứng Dụng Di Động Hoặc Website",
    ]
    title = raw.strip()
    for sfx in suffixes:
        if title.endswith(sfx):
            title = title[: -len(sfx)].strip()
    title = re.sub(r"\s+", " ", title).strip()
    
    # Kiem tra neu tieu de la mac dinh/loi/homepage
    lower_title = title.lower()
    if (
        not lower_title 
        or lower_title == "shopee" 
        or "shopee việt nam" in lower_title 
        or "shopee vietnam" in lower_title 
        or "hot deals" in lower_title 
        or "best prices" in lower_title
        or "verify" in lower_title
        or "robot" in lower_title
    ):
        return "[KHÔNG LẤY ĐƯỢC TÊN]"
    return title


# ══════════════════════════════════════════════
#   Giải mã tên sản phẩm từ URL path (FAST PATH)
# ══════════════════════════════════════════════
def extract_name_from_url(url: str) -> str:
    """
    Trích xuất tên sản phẩm từ URL nếu có dạng:
    shopee.vn/Ten-San-Pham-i.12345.67890
    """
    unquoted = urllib.parse.unquote(url)
    
    # Bỏ query parameters
    clean_url = unquoted.split("?")[0]
    
    # Tìm chuỗi trước i.shop_id.product_id
    m = re.search(r'shopee\.vn/([^/]+)-i\.\d+\.\d+', clean_url, re.IGNORECASE)
    if m:
        name_dashed = m.group(1)
        # Thay thế gạch ngang bằng khoảng trắng
        name = name_dashed.replace("-", " ").strip()
        # Đảm bảo không bị rỗng
        if name:
            return name
            
    # Hỗ trợ thêm dạng url rút gọn khác nếu có
    return ""
def is_valid_product_url(url: str) -> bool:
    """
    Kiem tra xem URL sau redirect co phai link san pham hop le hay khong.
    Truoc khi day cho Chrome, phai chac chan day la link san pham,
    chu khong phai link trang chu hoac trang verify.
    """
    unquoted = urllib.parse.unquote(url)
    if "-i." in unquoted:
        return True
    if re.search(r'shopee\.vn/[^/]+/\d+/\d+', unquoted):
        return True
    if re.search(r'shopee\.vn/product/\d+/\d+', unquoted):
        return True
    return False



# ══════════════════════════════════════════════
#   Phân chia task cho các thread
# ══════════════════════════════════════════════
def split_tasks(task_list: list, n: int) -> list[list]:
    buckets = [[] for _ in range(n)]
    for i, task in enumerate(task_list):
        buckets[i % n].append(task)
    return buckets


# ══════════════════════════════════════════════
#   Sắp xếp lại file kết quả theo index
# ══════════════════════════════════════════════
def sort_output_file():
    output_path = BASE_DIR / OUTPUT_FILE
    if not output_path.exists():
        return
    lines = {}
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|", 1)
            try:
                idx = int(parts[0].strip())
                lines[idx] = line
            except ValueError:
                pass
    with open(output_path, "w", encoding="utf-8") as f:
        for idx in sorted(lines.keys()):
            f.write(lines[idx] + "\n")


# ══════════════════════════════════════════════
#   PHASE 1: Redirect & Direct Parse worker
# ══════════════════════════════════════════════
def resolve_redirect_worker(idx: int, short_url: str, headers: dict, cookies: dict = None) -> tuple[int, str, str, str, bool]:
    """
    Gửi request lấy redirect URL (kèm cookies của phiên đăng nhập shopee nếu có)
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(short_url, headers=headers, cookies=cookies, timeout=12, allow_redirects=True)
            final_url = r.url
            
            # Thử parse tên sản phẩm từ redirect URL
            parsed_name = extract_name_from_url(final_url)
            if parsed_name:
                return idx, short_url, final_url, parsed_name, True
            else:
                # Không có tên trong path (Ví dụ: shopee.vn/opaanlp/1234/5678)
                return idx, short_url, final_url, "", False
                
        except Exception:
            if attempt == MAX_RETRIES:
                break
            time.sleep(1)
            
    # Lỗi kết nối hoặc không redirect được -> ném cho Chrome xử lý
    return idx, short_url, short_url, "", False


# ══════════════════════════════════════════════
#   PHASE 2: Chrome Worker
# ══════════════════════════════════════════════
SHOPEE_TITLE_SELECTORS = [
    ".product-briefing--name",
    "[class*='product-name'] h1",
    "h1[class*='product']",
    "div[class*='product-title']",
    ".page-product [class*='name']",
]

def dismiss_popups(driver: webdriver.Chrome):
    CLOSE_SELECTORS = [
        "button.shopee-popup__close-btn",
        "[class*='close-btn']",
        "[class*='close_btn']",
        "button[class*='close']",
    ]
    for sel in CLOSE_SELECTORS:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            if el.is_displayed():
                el.click()
                time.sleep(0.5)
        except Exception:
            pass

def chrome_worker(thread_id: int, task_queue: list, pbar: tqdm, is_multi: bool = False):
    """
    task_queue: [(index, short_url, redirect_url), ...]
    """
    import shutil

    driver = None
    # Tính sẵn profile_path để kill zombie Chrome từ lần chạy trước (trước khi create_driver)
    if is_multi:
        profile_path = PROFILE_DIR / f"shopee_profile_{thread_id}"
    else:
        profile_path = PROFILE_DIR / "shopee_profile"

    try:
        cprint(f"Khoi dong Chrome #{thread_id}...", Fore.CYAN, "INFO", pbar)
        force_kill_chrome_for_profile(profile_path)   # Dọn zombie trước khi sync+start
        driver, profile_path = create_driver(thread_id, is_multi)
        cprint(f"Chrome #{thread_id} san sang [OK]", Fore.GREEN, "SUCCESS", pbar)

        for idx, short_url, redirect_url in task_queue:
            if should_stop:
                cprint(f"[T{thread_id}] Dung theo yeu cau.", Fore.YELLOW, "WARN", pbar)
                break
            success = False
            product_name = "[KHÔNG LẤY ĐƯỢC TÊN]"
            
            # Phân tích shop_id và product_id để tạo URL chuẩn
            shop_id, product_id = None, None
            m1 = re.search(r'-i\.(\d+)\.(\d+)', redirect_url)
            if m1:
                shop_id, product_id = m1.group(1), m1.group(2)
            else:
                m2 = re.search(r'shopee\.vn/[^/]+/(\d+)/(\d+)', redirect_url)
                if m2:
                    shop_id, product_id = m2.group(1), m2.group(2)
                else:
                    m3 = re.search(r'shopee\.vn/product/(\d+)/(\d+)', redirect_url)
                    if m3:
                        shop_id, product_id = m3.group(1), m3.group(2)
            
            if shop_id and product_id:
                clean_url = f"https://shopee.vn/product/{shop_id}/{product_id}"
            else:
                clean_url = redirect_url.split("?")[0]

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    driver.get(clean_url)
                    
                    # Đóng popup quảng cáo/cookie
                    dismiss_popups(driver)

                    # Chờ title sản phẩm thật HOẶC phát hiện trang "không tồn tại" (thoát sớm, không chờ 25s)
                    wait = WebDriverWait(driver, PAGE_TIMEOUT)
                    not_found = [False]

                    def title_or_not_found(drv):
                        # Phát hiện sớm trang sản phẩm bị xóa/không tồn tại
                        try:
                            body = drv.execute_script("return document.body ? document.body.innerText : ''")
                            if "không tồn tại" in body.lower():
                                not_found[0] = True
                                return True
                        except Exception:
                            pass
                        # Kiểm tra title sản phẩm thật
                        t = drv.title
                        if not t or len(t) <= 5 or "shopee" not in t.lower():
                            return False
                        return clean_title(t) != "[KHÔNG LẤY ĐƯỢC TÊN]"

                    try:
                        wait.until(title_or_not_found)
                    except TimeoutException:
                        # Kiểm tra lần cuối sau khi timeout
                        try:
                            body = driver.execute_script("return document.body ? document.body.innerText : ''")
                            if "không tồn tại" in body.lower():
                                not_found[0] = True
                        except Exception:
                            pass

                    # Sản phẩm không tồn tại → ghi nhãn rõ, không retry
                    if not_found[0]:
                        product_name = "[SẢN PHẨM KHÔNG TỒN TẠI]"
                        success = True
                        cprint(f"#{idx} [T{thread_id}] San pham khong ton tai, bo qua.", Fore.YELLOW, "WARN", pbar)
                        break

                    # 1. Thử lấy từ CSS Selectors
                    found_by_css = False
                    for selector in SHOPEE_TITLE_SELECTORS:
                        try:
                            el = driver.find_element(By.CSS_SELECTOR, selector)
                            txt = el.text.strip()
                            if txt and len(txt) > 3:
                                product_name = clean_title(txt)
                                found_by_css = True
                                break
                        except NoSuchElementException:
                            pass
                    
                    # 2. Nếu không tìm thấy, lấy từ document title
                    if not found_by_css:
                        raw_title = driver.title
                        if raw_title and len(raw_title) > 5:
                            product_name = clean_title(raw_title)

                    # Kiem tra neu thanh cong
                    if product_name and product_name != "[KHÔNG LẤY ĐƯỢC TÊN]":
                        success = True
                        break
                    else:
                        # Bi chan bot hoac redirect. Kich hoat self-healing (khoi dong lai Chrome, giu nguyen profile de luu login)
                        cprint(f"#{idx} [T{thread_id}] Shopee chan bot/Redirect ve trang loi. Dang khoi dong lai Chrome (Lan {attempt}/{MAX_RETRIES})...", Fore.YELLOW, "WARN", pbar)
                        try:
                            driver.quit()
                        except Exception:
                            pass
                        force_kill_chrome_for_profile(profile_path)
                        time.sleep(min(3 * attempt, 12))
                        driver, profile_path = create_driver(thread_id, is_multi, force_sync=False)
                        
                except TimeoutException:
                    cprint(f"#{idx} [T{thread_id}] Timeout lan {attempt}/{MAX_RETRIES}. Dang khoi dong lai Chrome...", Fore.YELLOW, "WARN", pbar)
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    force_kill_chrome_for_profile(profile_path)
                    time.sleep(min(3 * attempt, 12))
                    driver, profile_path = create_driver(thread_id, is_multi, force_sync=False)

                except Exception as e:
                    cprint(f"#{idx} [T{thread_id}] Loi Chrome lan {attempt}: {str(e).splitlines()[0]}", Fore.YELLOW, "WARN", pbar)
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    force_kill_chrome_for_profile(profile_path)
                    time.sleep(min(3 * attempt, 12))
                    driver, profile_path = create_driver(thread_id, is_multi, force_sync=False)

            # Ghi kết quả
            write_and_sort_result(idx, product_name, short_url)

            with stats_lock:
                if success:
                    stats["success"] += 1
                    color = Fore.GREEN
                    icon  = "[OK]"
                else:
                    stats["failed"] += 1
                    color = Fore.RED
                    icon  = "[XX]"
                stats["phase2_done"] += 1

            cprint(
                f"[T{thread_id}] #{idx:>4}  {product_name[:60]}",
                color,
                "SUCCESS" if success else "ERROR",
                pbar
            )
                
            pbar.update(1)
            time.sleep(DELAY_PER_REQ)

    except Exception as e:
        cprint(f"Worker #{thread_id} crashed: {e}", Fore.RED, "ERROR", pbar)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        
        cprint(f"Chrome #{thread_id} da dong.", Fore.CYAN, "INFO", pbar)


# ══════════════════════════════════════════════
#   MAIN
# ══════════════════════════════════════════════
def main():
    print(BANNER)
    load_config()



    input_path  = BASE_DIR / INPUT_FILE
    output_path = BASE_DIR / OUTPUT_FILE

    # ── Kiểm tra file input
    if not input_path.exists():
        cprint(f"Khong tim thay file input: {INPUT_FILE}", Fore.RED, "ERROR")
        sys.exit(1)

    global should_stop, total_urls_count
    should_stop = False
    
    # ── Đọc danh sách URL
    all_urls = load_input_urls(input_path)
    total    = len(all_urls)
    total_urls_count = total
    cprint(f"Tong so link trong file input: {Fore.YELLOW}{total:,}", Fore.CYAN)

    # ── Đọc checkpoint (resume) & Lọc trùng lặp thông minh
    resolved_urls = load_existing_resolved_urls(output_path)
    existing = load_existing_results(output_path)
    done_indices = set(existing.keys())

    pending = []
    seen_urls = set()
    for i, u in all_urls:
        u_lower = u.lower().strip()
        
        # 1. Tránh chạy lại index đã có kết quả
        if i in done_indices:
            continue
            
        # 2. Tránh trùng lặp với URL đã chạy thành công trước đó (dòng khác)
        if u_lower in resolved_urls:
            continue
            
        # 3. Tránh trùng lặp ngay trong file input
        if u_lower in seen_urls:
            continue
        seen_urls.add(u_lower)
        
        pending.append((i, u))

    skipped = total - len(pending)
    
    with stats_lock:
        stats["skipped"] = skipped

    cprint(f"Da hoan thanh / Trung lap: {Fore.GREEN}{skipped:,} link", Fore.CYAN)
    cprint(f"Can xu ly them:        {Fore.YELLOW}{len(pending):,} link", Fore.CYAN)
    
    if not pending:
        cprint("Tat ca link da duoc xu ly! Khong can chay lai.", Fore.GREEN, "SUCCESS")
        sort_output_file()
        cprint(f"Ket qua duoc sap xep va luu tai: {output_path}", Fore.GREEN, "SUCCESS")
        return

    # ══════════════════════════════════════════════
    #   PHASE 1: Quét redirect & Tự bóc tách tên bằng Requests (FAST PATH)
    # ══════════════════════════════════════════════
    needs_chrome = []
    start_time = time.time()
    
    if USE_CHROME_ONLY:
        cprint("Bo qua Phase 1 theo cau hinh USE_CHROME_ONLY. Chuyen thang sang Phase 2 (Chrome)...", Fore.YELLOW, "WARN")
        with stats_lock:
            stats["phase1_total"] = len(pending)
            stats["phase1_done"] = len(pending)
            stats["phase2_total"] = len(pending)
            stats["phase2_done"] = 0
        needs_chrome = [(idx, url, url) for idx, url in pending]
    else:
        cprint("Khoi chay Phase 1: Giai ma redirect bang Requests...", Fore.CYAN)
        with stats_lock:
            stats["phase1_total"] = len(pending)
            stats["phase1_done"] = 0
            stats["phase2_total"] = 0
            stats["phase2_done"] = 0
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        pbar_p1 = tqdm(
            total=len(pending), 
            desc="Phase 1 (FAST)", 
            unit="link", 
            colour="yellow"
        )

        cookies = load_saved_cookies()
        if cookies:
            cprint(f"Nap thanh cong {len(cookies)} cookies tu phien dang nhap Shopee.", Fore.GREEN, "SUCCESS")
        else:
            cprint("Chay requests khong co cookies. Neu bi chan bot hay bam nut Dang nhap shopee tren dashboard.", Fore.YELLOW, "WARN")

        # Chạy multi-thread requests để resolve redirect nhanh
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(resolve_redirect_worker, idx, url, headers, cookies): (idx, url)
                for idx, url in pending
            }
            
            for future in as_completed(futures):
                if should_stop:
                    cprint("Da nhan yeu cau dung. Dang dung Phase 1...", Fore.YELLOW, "WARN")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                idx, short_url = futures[future]
                try:
                    idx, short_url, final_url, product_name, is_fast = future.result()
                    
                    if is_fast:
                        write_and_sort_result(idx, product_name, short_url)
                        
                        with stats_lock:
                            stats["success"] += 1
                            
                        cprint(f"#{idx:>4}  {product_name[:60]} (FAST)", Fore.GREEN, "SUCCESS", pbar_p1)
                    else:
                        # Cần Chrome để xử lý. Nếu final_url không hợp lệ (bị redirect về trang chủ/trang verify),
                        # ta phải dùng short_url gốc để Chrome tự thực hiện lại redirection chuẩn.
                        target_url = final_url if is_valid_product_url(final_url) else short_url
                        needs_chrome.append((idx, short_url, target_url))
                        cprint(f"#{idx:>4}  Cần chuyển sang Chrome (Không thể resolve bằng Requests)", Fore.BLUE, "INFO", pbar_p1)
                        
                except Exception as e:
                    cprint(f"Lỗi resolve #{idx}: {e}", Fore.RED, "ERROR", pbar_p1)
                    needs_chrome.append((idx, short_url, short_url))
                    
                with stats_lock:
                    stats["phase1_done"] += 1
                    
                pbar_p1.update(1)
                
        pbar_p1.close()
        cprint(f"Xong Phase 1! Tim thay {len(needs_chrome)} link can xu ly bang Chrome.", Fore.GREEN, "SUCCESS")

    # ══════════════════════════════════════════════
    #   PHASE 2: Chạy Chrome giả lập cho các link đặc biệt (SLOW PATH)
    # ══════════════════════════════════════════════
    if needs_chrome:
        n_threads = NUM_THREADS
        with stats_lock:
            stats["phase2_total"] = len(needs_chrome)
            stats["phase2_done"] = 0
            
        if n_threads > 1:
            cprint(f"Khoi chay Phase 2: Chay song song {n_threads} luong Chrome...", Fore.CYAN)
        else:
            cprint("Khoi chay Phase 2: Chay Chrome gia lap tuan tu...", Fore.CYAN)
            
        cprint("Meo: Ban co the dang nhap tai khoan Shopee tren cua so Chrome de tranh bi quet va giu phien dang nhap.", Fore.YELLOW, "WARN")
        
        # Sắp xếp danh sách cần chạy Chrome theo index để theo dõi dễ hơn
        needs_chrome.sort(key=lambda x: x[0])
        
        task_chunks = split_tasks(needs_chrome, n_threads)
        
        pbar_p2 = tqdm(
            total=len(needs_chrome),
            desc="Phase 2 (CHROME)",
            unit="link",
            colour="cyan"
        )
        
        is_multi = (n_threads > 1)
        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [
                executor.submit(chrome_worker, tid, chunk, pbar_p2, is_multi)
                for tid, chunk in enumerate(task_chunks, start=1)
                if chunk
            ]
            for future in as_completed(futures):
                if should_stop:
                    cprint("Da nhan yeu cau dung. Dang dong cac trinh duyet Phase 2...", Fore.YELLOW, "WARN")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                try:
                    future.result()
                except Exception as e:
                    pbar_p2.write(f"[MAIN] Chrome thread crashed: {e}")
                    
        pbar_p2.close()
        
    # ── Sắp xếp file kết quả sau khi hoàn thành
    cprint("Dang sap xep lai file ket qua...", Fore.CYAN)
    sort_output_file()
    
    elapsed = time.time() - start_time
    mins, secs = divmod(int(elapsed), 60)
    
    cprint("Hoan thanh toan bo danh sach!", Fore.GREEN, "SUCCESS")
    
    print(f"""
{Fore.CYAN}===================================================={Style.RESET_ALL}
{Fore.CYAN}                 TONG KET TIEN TRINH                {Style.RESET_ALL}
{Fore.CYAN}===================================================={Style.RESET_ALL}
  {Fore.GREEN}[OK] Thanh cong:{Style.RESET_ALL}   {stats['success']:>5,} link
  {Fore.RED}[XX] That bai:{Style.RESET_ALL}     {stats['failed']:>5,} link
  {Fore.YELLOW}[--] Da co truoc:{Style.RESET_ALL}  {stats['skipped']:>5,} link
  {Fore.CYAN}[T ] Thoi gian:{Style.RESET_ALL}    {mins}m {secs}s

  {Fore.GREEN}[F ] File ket qua: {output_path}{Style.RESET_ALL}
""")

    final_results = load_existing_results(output_path)
    print(f"  {Fore.CYAN}[>>] Tong so dong trong file ket qua: {len(final_results):,} / {total:,}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Da dung boi nguoi dung. Ket qua da luu vao {OUTPUT_FILE}.{Style.RESET_ALL}")
        print(f"{Fore.CYAN}    Chay lai script de tiep tuc tu noi da dung.{Style.RESET_ALL}\n")
        sys.exit(0)
