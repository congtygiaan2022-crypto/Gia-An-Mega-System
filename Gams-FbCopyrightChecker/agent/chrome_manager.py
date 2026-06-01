"""
Chrome Profile Manager
Kiểm tra, khởi động và dọn dẹp Chrome process theo đúng profile của tool.
Chỉ kill process nào dùng đúng --user-data-dir của tool — không ảnh hưởng
Chrome khác đang mở của người dùng.
"""
import os
import time
from typing import Optional

import psutil

from modules.logger import get_logger

log = get_logger(__name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ─────────────────────────────────────────────────────────────────
# Tìm Chrome processes đang dùng đúng profile directory này
# ─────────────────────────────────────────────────────────────────

def _find_chrome_pids_for_profile(profile_dir: str) -> list[int]:
    """
    Tìm tất cả PID của Chrome process đang dùng profile_dir.
    Chỉ match process nào có --user-data-dir=<profile_dir> trong cmdline.
    Trả về list[int] PID, rỗng nếu không có.
    """
    profile_dir_norm = os.path.normcase(os.path.normpath(profile_dir))
    pids: list[int] = []

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (proc.info["name"] or "").lower()
            if "chrome" not in name:
                continue
            cmdline = proc.info["cmdline"] or []
            for arg in cmdline:
                arg_norm = os.path.normcase(os.path.normpath(arg.split("=", 1)[-1]))
                if "user-data-dir" in arg and arg_norm == profile_dir_norm:
                    pids.append(proc.info["pid"])
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return pids


def is_profile_open(profile_dir: str) -> bool:
    """Trả về True nếu Chrome đang dùng profile này."""
    return len(_find_chrome_pids_for_profile(profile_dir)) > 0


def _kill_pids(pids: list[int], timeout: float = 5.0) -> int:
    """
    Graceful terminate rồi force kill nếu cần.
    Chỉ kill đúng các PID trong danh sách.
    Trả về số process đã kill thành công.
    """
    if not pids:
        return 0

    procs = []
    for pid in pids:
        try:
            procs.append(psutil.Process(pid))
        except psutil.NoSuchProcess:
            pass

    # Bước 1: gửi terminate (SIGTERM / Windows terminate)
    for p in procs:
        try:
            p.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Bước 2: chờ tối đa timeout giây
    gone, alive = psutil.wait_procs(procs, timeout=timeout)

    # Bước 3: kill cứng những cái chưa chịu thoát
    killed = len(gone)
    for p in alive:
        try:
            p.kill()
            killed += 1
            log.warning(f"Force-killed Chrome PID {p.pid} (profile still locked)")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            killed += 1  # đã thoát trước khi kịp kill

    return killed


# ─────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────

def _remove_singleton_locks(profile_dir: str):
    """Xóa lock files mà Chrome để lại khi bị kill — ngăn Chrome mới khởi động."""
    for name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        path = os.path.join(profile_dir, name)
        try:
            if os.path.exists(path) or os.path.islink(path):
                os.remove(path)
                log.debug(f"Removed lock file: {path}")
        except Exception as e:
            log.debug(f"Could not remove {name}: {e}")


def _patch_crash_exit_flag(profile_dir: str):
    """
    Nếu Preferences có exit_type='Crashed', Chrome sẽ cố restore session
    và thường crash lại trong automation mode.
    Patch thành 'Normal' để Chrome khởi động sạch.
    """
    import json
    prefs_path = os.path.join(profile_dir, "Default", "Preferences")
    if not os.path.exists(prefs_path):
        return
    try:
        with open(prefs_path, "r", encoding="utf-8", errors="replace") as f:
            prefs = json.load(f)
        profile_section = prefs.get("profile", {})
        if profile_section.get("exit_type") == "Crashed":
            profile_section["exit_type"] = "Normal"
            prefs["profile"] = profile_section
            with open(prefs_path, "w", encoding="utf-8") as f:
                json.dump(prefs, f)
            log.info(f"Patched exit_type Crashed→Normal in: {prefs_path}")
    except Exception as e:
        log.debug(f"Could not patch Preferences: {e}")


def ensure_profile_closed(profile_dir: str, wait_after: float = 1.5):
    """
    Nếu Chrome đang dùng profile này → tắt đúng những process đó.
    Sau đó xóa lock files và patch crash flag để Chrome mới khởi động sạch.
    """
    pids = _find_chrome_pids_for_profile(profile_dir)
    if pids:
        log.info(
            f"Profile đang mở (PID {pids}) — đóng lại trước khi khởi động mới..."
        )
        killed = _kill_pids(pids)
        log.info(f"Đã đóng {killed} Chrome process cho profile: {os.path.basename(profile_dir)}")
        if wait_after > 0:
            time.sleep(wait_after)
    else:
        log.debug(f"Profile không bị lock bởi process: {profile_dir}")

    # Xóa lock files (có thể còn lại từ lần crash trước)
    _remove_singleton_locks(profile_dir)
    # Patch exit_type Crashed → Normal
    _patch_crash_exit_flag(profile_dir)


def close_profile(profile_dir: str, wait_after: float = 1.0):
    """
    Đóng Chrome đang dùng profile này.
    Gọi khi hoàn thành tác vụ hoặc khi tool bị dừng.
    """
    pids = _find_chrome_pids_for_profile(profile_dir)
    if not pids:
        return
    killed = _kill_pids(pids, timeout=5.0)
    log.info(f"Profile đóng sau tác vụ: {os.path.basename(profile_dir)} ({killed} process)")
    if wait_after > 0:
        time.sleep(wait_after)


def close_all_tool_profiles(base_profile_dir: Optional[str] = None):
    """
    Đóng TẤT CẢ Chrome profiles thuộc tool (mọi subdirectory trong chrome_profile/).
    Dùng khi tool shutdown hoàn toàn.
    """
    if base_profile_dir is None:
        base_profile_dir = os.path.join(_BASE_DIR, "chrome_profile")

    if not os.path.isdir(base_profile_dir):
        return

    closed_total = 0
    for entry in os.scandir(base_profile_dir):
        if entry.is_dir():
            pids = _find_chrome_pids_for_profile(entry.path)
            if pids:
                killed = _kill_pids(pids)
                closed_total += killed
                log.info(f"Closed profile '{entry.name}' ({killed} processes)")

    if closed_total:
        log.info(f"Tool shutdown: đã đóng {closed_total} Chrome process")
    else:
        log.debug("Tool shutdown: không có Chrome profile nào đang mở")


# ─────────────────────────────────────────────────────────────────
# Context manager — dùng với `with` để tự dọn dẹp
# ─────────────────────────────────────────────────────────────────

class ManagedChromeProfile:
    """
    Context manager: tự động kiểm tra + đóng profile trước khi mở,
    và đóng lại sau khi khối with kết thúc (kể cả khi có exception).

    Ví dụ:
        with ManagedChromeProfile(profile_dir) as profile:
            driver = build_driver_for_account(uid)
            ...
    """

    def __init__(self, profile_dir: str):
        self.profile_dir = profile_dir
        self._driver = None

    def __enter__(self):
        ensure_profile_closed(self.profile_dir)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Đóng Selenium driver trước (nếu có)
        if self._driver is not None:
            try:
                self._driver.quit()
                log.debug("Selenium driver quit OK")
            except Exception:
                pass
            self._driver = None

        # Đảm bảo Chrome process thực sự đã thoát
        close_profile(self.profile_dir)
        return False  # không suppress exception
