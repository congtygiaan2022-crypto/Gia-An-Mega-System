"""
Quản lý khóa (lock) tiến trình để tránh chạy trùng lặp tài khoản.
Hỗ trợ tự động dọn dẹp khóa cũ (stale locks) khi tiến trình trước đó đã tắt/crash.
"""
import os
import sys
import time
import json
import ctypes
import atexit
from modules.logger import get_logger

log = get_logger("lock_manager")

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCKS_DIR = os.path.join(_BASE_DIR, "locks")

_acquired_locks = set()

def _safe_filename(name: str) -> str:
    # Giữ lại ký tự chữ, số và dấu gạch dưới, gạch ngang, chấm
    return "".join(c if c.isalnum() or c in ("_", "-", ".") else "_" for c in name)

def is_process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True

    if sys.platform == "win32":
        try:
            # 0x1000 = PROCESS_QUERY_LIMITED_INFORMATION
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if handle:
                exit_code = ctypes.c_ulong()
                kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
                STILL_ACTIVE = 259
                is_active = (exit_code.value == STILL_ACTIVE)
                kernel32.CloseHandle(handle)
                return is_active
            else:
                # OpenProcess thất bại. Kiểm tra GetLastError
                err = kernel32.GetLastError()
                # 5 = ERROR_ACCESS_DENIED (tiến trình tồn tại nhưng không có quyền query)
                if err == 5:
                    return True
                # 87 = ERROR_INVALID_PARAMETER (không tìm thấy tiến trình)
                return False
        except Exception:
            # Fallback dùng os.kill
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False

def get_lock_file_path(lock_name: str) -> str:
    os.makedirs(LOCKS_DIR, exist_ok=True)
    return os.path.join(LOCKS_DIR, f"{_safe_filename(lock_name)}.lock")

def get_lock_info(lock_name: str) -> dict:
    path = get_lock_file_path(lock_name)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def acquire_lock(lock_name: str) -> bool:
    """
    Cố gắng giữ khóa theo tên.
    Trả về False nếu khóa đang được giữ bởi một tiến trình đang hoạt động khác.
    Trả về True và tự động xóa nếu khóa cũ của tiến trình đã chết (resume quét).
    """
    path = get_lock_file_path(lock_name)
    info = get_lock_info(lock_name)
    if info:
        pid = info.get("pid")
        if pid and is_process_alive(pid):
            log.warning(f"Tài khoản/tính năng '{lock_name}' đang được chạy bởi tiến trình PID {pid} (bắt đầu lúc {info.get('timestamp')}).")
            return False
        else:
            log.info(f"Phát hiện khóa cũ của tiến trình đã đóng (PID {pid}). Đang dọn dẹp để tiếp tục quét (resume)...")
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                log.error(f"Không thể xóa tệp khóa cũ: {e}")
                return False

    # Ghi tệp khóa mới
    new_info = {
        "pid": os.getpid(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(new_info, f, indent=2)
        _acquired_locks.add(lock_name)
        log.info(f"Đã xác lập khóa thành công cho '{lock_name}' (PID: {os.getpid()})")
        return True
    except Exception as e:
        log.error(f"Lỗi tạo tệp khóa '{path}': {e}")
        return False

def release_lock(lock_name: str) -> bool:
    """
    Giải phóng khóa nếu nó thuộc về tiến trình hiện tại.
    """
    path = get_lock_file_path(lock_name)
    info = get_lock_info(lock_name)
    if not info:
        return False
    if info.get("pid") == os.getpid():
        try:
            if os.path.exists(path):
                os.remove(path)
            _acquired_locks.discard(lock_name)
            log.info(f"Đã giải phóng khóa '{lock_name}'")
            return True
        except Exception as e:
            log.error(f"Lỗi giải phóng khóa '{lock_name}': {e}")
            return False
    return False

def _cleanup_all_locks():
    for name in list(_acquired_locks):
        release_lock(name)

# Tự động dọn dẹp khi thoát python
atexit.register(_cleanup_all_locks)
