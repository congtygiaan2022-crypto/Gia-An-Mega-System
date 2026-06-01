import traceback
import subprocess
import sys
import os
import time
from core.logger import get_module_logger
from core.error_registry import error_registry, MAX_RETRIES, COOLDOWN_SECONDS

logger = get_module_logger("SelfRepair")


class SelfRepair:
    """
    Lớp sửa lỗi tự động với Error Registry guard.
    - Phân tích lỗi
    - Retry có giới hạn (MAX_RETRIES)
    - Cooldown sau khi vượt retry
    - Tự restart nếu lỗi nghiêm trọng (ImportError / NameError)
    """

    def analyze_error(self, error) -> str:
        return traceback.format_exc()

    def restart_system(self):
        logger.warning("SelfRepair: Lỗi nghiêm trọng. Đang khởi động lại hệ thống...")
        main_path = os.path.join(os.getcwd(), "main.py")
        subprocess.Popen([sys.executable, main_path])
        sys.exit(1)

    def repair_loop(self, func, *args, **kwargs):
        """
        Bao bọc một function với Error Registry guard.
        Retry tối đa MAX_RETRIES lần trước khi cooldown.
        """
        error_name = getattr(func, "__name__", str(func))

        try:
            result = func(*args, **kwargs)
            # Hàm thành công → xoá lỗi nếu đang tracked
            if error_name in error_registry.active_errors:
                error_registry.clear(error_name)
            return result

        except Exception as e:
            error_trace = self.analyze_error(e)
            logger.error(f"[SelfRepair] Phát hiện lỗi '{error_name}': {e}")

            # Kiểm tra cooldown block
            if error_registry.is_blocked(error_name):
                logger.warning(
                    f"[SelfRepair] '{error_name}' đang trong cooldown. Bỏ qua."
                )
                return f"Bỏ qua: '{error_name}' đang trong cooldown."

            is_new = error_registry.register(error_name)

            if not is_new:
                retry = error_registry.increment(error_name)
                if retry > MAX_RETRIES:
                    logger.error(
                        f"[SelfRepair] '{error_name}' vượt {MAX_RETRIES} lần retry. "
                        f"Cooldown {COOLDOWN_SECONDS}s."
                    )
                    return f"Error '{error_name}' exceeded retry limit. Cooldown active."
            else:
                logger.info(f"[SelfRepair] Lần đầu gặp lỗi '{error_name}'. Retry 1/{MAX_RETRIES}.")

            # Lỗi nghiêm trọng → restart ngay
            if any(t in str(e) for t in ("NameError", "ImportError", "TypeError")):
                self.restart_system()
                return "Hệ thống đang khởi động lại do lỗi nghiêm trọng."

            # Cooldown ngắn giữa các lần retry
            time.sleep(COOLDOWN_SECONDS)

            return f"Lỗi được SelfRepair ghi nhận: {e}"


# Global instance
repair = SelfRepair()
