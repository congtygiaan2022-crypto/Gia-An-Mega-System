"""
Tầng 3 — Action
Retry decorator, per-account Chrome profile, WorkerPool scan đa tài khoản song song.
"""
import functools
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Any, Optional

from modules.config_loader import CONFIG
from modules.logger import get_logger

log = get_logger(__name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_WORKERS = 3  # max Chrome instances chạy song song


# ──────────────────────────────────────────────
# Retry decorator với exponential backoff
# ──────────────────────────────────────────────

def retry(max_attempts: int = 3, backoff: float = 2.0,
          exceptions: tuple = (Exception,)):
    """
    Decorator: thử lại tối đa max_attempts lần với exponential backoff.
    Raise exception cuối cùng nếu hết lượt.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = 1.0
            last_exc: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_attempts:
                        log.warning(
                            f"[retry {attempt}/{max_attempts}] {func.__name__} failed: {e} "
                            f"— retrying in {delay:.1f}s"
                        )
                        time.sleep(delay)
                        delay *= backoff
                    else:
                        log.error(f"[retry] {func.__name__} exhausted {max_attempts} attempts: {e}")
            raise last_exc or RuntimeError(f"{func.__name__} failed (max_attempts={max_attempts})")
        return wrapper
    return decorator


# ──────────────────────────────────────────────
# Per-account Chrome profile
# ──────────────────────────────────────────────

def chrome_profile_dir(uid: str) -> str:
    """
    Trả về đường dẫn thư mục Chrome profile riêng cho mỗi account.
    chrome_profile/<uid>/ — tránh session conflict khi chạy đa tài khoản.
    """
    uid_safe = "".join(c for c in (uid or "default") if c.isalnum() or c in "-_")
    path = os.path.join(_BASE_DIR, "chrome_profile", uid_safe)
    os.makedirs(path, exist_ok=True)
    return path


def build_driver_for_account(uid: str = ""):
    """
    Khởi tạo Chrome driver với profile riêng cho account.
    Tự động kiểm tra và đóng profile nếu đang bị dùng bởi Chrome khác.
    """
    from selenium.webdriver.chrome.options import Options
    from selenium import webdriver
    from modules.fb_login import _chrome_binary, _build_service
    from agent.chrome_manager import ensure_profile_closed

    profile_dir = chrome_profile_dir(uid)

    # Đóng Chrome nào đang dùng profile này trước khi mở mới
    try:
        ensure_profile_closed(profile_dir)
    except Exception as e:
        log.warning(f"ensure_profile_closed failed (non-fatal): {e}")

    cfg = CONFIG["selenium"]
    options = Options()
    binary = _chrome_binary()
    if binary and os.path.exists(binary):
        options.binary_location = binary

    if cfg.get("headless", False):
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-crash-reporter")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-session-crashed-bubble")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_experimental_option("useAutomationExtension", False)

    service = _build_service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(cfg.get("implicit_wait", 10))
    driver.set_page_load_timeout(cfg.get("page_load_timeout", 30))
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    log.info(f"Chrome driver initialized for uid={uid or 'default'} → {profile_dir}")
    return driver


# ──────────────────────────────────────────────
# Worker Pool: scan nhiều account song song
# ──────────────────────────────────────────────

class WorkerPool:
    """
    Quản lý ThreadPoolExecutor để scan nhiều Facebook accounts song song.
    Mỗi account chạy trong thread riêng với Chrome instance độc lập.
    """

    def __init__(self, max_workers: int = MAX_WORKERS):
        self.max_workers = max_workers
        self._results: dict[str, Any] = {}
        self._lock = threading.Lock()

    def run_accounts(
        self,
        accounts: list,
        task_fn: Callable,
        progress_callback: Optional[Callable] = None,
    ) -> dict[str, Any]:
        """
        Chạy task_fn(account) song song trên tất cả accounts.
        task_fn nhận 1 Account object, trả về dict kết quả.
        progress_callback(account_key, result) được gọi sau mỗi account hoàn thành.
        Trả về dict {account_key: result_or_exception}.
        """
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_acc = {
                executor.submit(self._safe_run, task_fn, acc): acc
                for acc in accounts
            }
            for future in as_completed(future_to_acc):
                acc = future_to_acc[future]
                key = acc.uid or acc.email or str(id(acc))
                try:
                    result = future.result()
                except Exception as e:
                    result = {"error": str(e)}
                    log.error(f"Account {key} worker failed: {e}")

                results[key] = result
                if progress_callback:
                    try:
                        progress_callback(key, result)
                    except Exception:
                        pass

        return results

    @staticmethod
    def _safe_run(task_fn: Callable, account) -> Any:
        """Chạy task_fn với try/except để không crash cả pool."""
        try:
            return task_fn(account)
        except Exception as e:
            log.error(f"Worker task error for {account.display_name}: {e}", exc_info=True)
            raise
