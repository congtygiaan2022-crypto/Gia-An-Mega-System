import time
from core.logger import get_module_logger

logger = get_module_logger("ErrorRegistry")

MAX_RETRIES = 3
COOLDOWN_SECONDS = 300  # 5 phút cooldown sau khi vượt retry limit


class ErrorRegistry:
    """
    Quản lý trạng thái lỗi để tránh repair loop vô hạn.
    - Đăng ký lỗi lần đầu → cho phép fix
    - Nếu lỗi tái xuất hiện → tăng retry counter
    - Nếu retry > MAX_RETRIES → block và cooldown
    - Sau khi fix thành công → xoá khỏi registry
    """

    def __init__(self):
        # { error_name: {"count": int, "first_seen": float, "blocked_until": float} }
        self.active_errors: dict = {}

    def register(self, error_name: str) -> bool:
        """
        Đăng ký lỗi mới.
        Trả về True nếu lỗi chưa tồn tại (cho phép xử lý).
        Trả về False nếu đã tồn tại (loop guard).
        """
        now = time.time()

        if error_name in self.active_errors:
            entry = self.active_errors[error_name]

            # Kiểm tra xem có đang trong cooldown không
            if entry.get("blocked_until", 0) > now:
                remaining = int(entry["blocked_until"] - now)
                logger.warning(
                    f"[ErrorRegistry] '{error_name}' is in cooldown. "
                    f"{remaining}s remaining before next retry."
                )
                return False

            return False  # Lỗi đang được xử lý

        # Lỗi mới
        self.active_errors[error_name] = {
            "count": 1,
            "first_seen": now,
            "blocked_until": 0,
        }
        logger.info(f"[ErrorRegistry] New error detected: '{error_name}'")
        return True

    def increment(self, error_name: str) -> int:
        """
        Tăng số lần retry. Trả về số retry hiện tại.
        Nếu vượt MAX_RETRIES → kích hoạt cooldown.
        """
        if error_name not in self.active_errors:
            return 0

        self.active_errors[error_name]["count"] += 1
        retry = self.active_errors[error_name]["count"]

        logger.warning(f"[ErrorRegistry] '{error_name}' - Retry {retry}/{MAX_RETRIES}")

        if retry > MAX_RETRIES:
            blocked_until = time.time() + COOLDOWN_SECONDS
            self.active_errors[error_name]["blocked_until"] = blocked_until
            logger.error(
                f"[ErrorRegistry] '{error_name}' exceeded {MAX_RETRIES} retries. "
                f"Cooldown of {COOLDOWN_SECONDS}s activated."
            )

        return retry

    def get_retry(self, error_name: str) -> int:
        """Lấy số lần retry hiện tại."""
        return self.active_errors.get(error_name, {}).get("count", 0)

    def is_blocked(self, error_name: str) -> bool:
        """Kiểm tra xem lỗi có đang bị block (cooldown) không."""
        entry = self.active_errors.get(error_name)
        if not entry:
            return False
        return entry.get("blocked_until", 0) > time.time()

    def clear(self, error_name: str):
        """Xoá lỗi sau khi fix thành công."""
        if error_name in self.active_errors:
            del self.active_errors[error_name]
            logger.info(f"[ErrorRegistry] '{error_name}' fixed successfully. Removed from registry.")

    def status(self) -> dict:
        """Trả về toàn bộ trạng thái registry (để debug/log)."""
        return dict(self.active_errors)


# Global singleton
error_registry = ErrorRegistry()
