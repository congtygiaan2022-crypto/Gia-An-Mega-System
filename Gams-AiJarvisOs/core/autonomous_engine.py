import os
import threading
import time
from agents.debug_agent import DebugAgent
from agents.system_monitor import SystemMonitor
from agents.code_fix_agent import CodeFixAgent
from core.logger import get_module_logger
from core.error_registry import error_registry, MAX_RETRIES

logger = get_module_logger("AutonomousEngine")


class AutonomousEngine:
    def __init__(self):
        self.debug_agent = DebugAgent()
        self.system_monitor = SystemMonitor()
        self.code_fix_agent = CodeFixAgent()
        self.running = False

    def start(self):
        if self.running:
            return
        self.running = True
        logger.info("Autonomous Engine đang khởi động các worker nền...")

        threading.Thread(target=self._system_monitor_loop, daemon=True).start()
        threading.Thread(target=self._debug_loop, daemon=True).start()

    def _system_monitor_loop(self):
        while self.running:
            try:
                self.system_monitor.run()
            except Exception as e:
                logger.error(f"System Monitor failure: {e}")
            time.sleep(30)  # Kiểm tra mỗi 30 giây

    def _debug_loop(self):
        while self.running:
            try:
                errors = self.debug_agent.run()
                if isinstance(errors, list) and errors:
                    logger.warning(
                        f"Autonomous Engine phát hiện {len(errors)} lỗi. Đang xử lý..."
                    )
                    for error_msg in errors:
                        module = self.debug_agent.identify_faulty_module(error_msg)
                        self._handle_error(module, error_msg)
            except Exception as e:
                logger.error(f"Debug loop failure: {e}")
            time.sleep(60)  # Quét log mỗi 1 phút

    # ------------------------------------------------------------------
    # Error Guard: đăng ký → retry check → fix → validate
    # ------------------------------------------------------------------

    def _handle_error(self, module: str, error_msg: str):
        """
        Xử lý lỗi với Error Registry guard:
        1. Kiểm tra Whitelist: Chỉ cho phép tự sửa các Plugin trong thư mục plugins/
        2. Nếu lỗi đang bị block (cooldown) → bỏ qua
        3. Nếu lỗi mới → đăng ký và fix
        4. Nếu lỗi tái xuất → tăng retry; nếu vượt limit → cooldown & bỏ qua
        """
        if "." in module or "Registry" in module or "Engine" in module or module == "CoreComponent":
             # Các core modules thường có dấu . hoặc tên đặc thù, hoặc được DebugAgent dán nhãn CoreComponent
             return

        # Coi như module là tên file trong plugins/
        plugin_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins", f"{module}.py")
        if not os.path.exists(plugin_path):
            # Không phải plugin hợp lệ (file .py vật lý phải tồn tại trong plugins/) 
            # tránh tự tạo file bừa bãi
            return

        # Lỗi đang trong cooldown → không làm gì
        if error_registry.is_blocked(module):
            return

        is_new = error_registry.register(module)

        if not is_new:
            # Lỗi đã tồn tại → tăng retry
            retry = error_registry.increment(module)
            if retry > MAX_RETRIES:
                logger.error(
                    f"[AutonomousEngine] '{module}' vượt retry limit. "
                    "Dừng cố gắng fix, chờ cooldown."
                )
                return
            logger.info(
                f"[AutonomousEngine] Thử lại fix '{module}' lần {retry}/{MAX_RETRIES}"
            )
        else:
            logger.info(f"[AutonomousEngine] Lần đầu phát hiện lỗi '{module}'. Bắt đầu fix...")

        # Gửi yêu cầu fix tới CodeFixAgent
        self.code_fix_agent.propose_fix(module, error_msg)

        # Cooldown ngắn trước khi validate (tránh validate quá sớm)
        time.sleep(5)

        # Validate và clear nếu thành công
        self._validate_fix(module)

    def _validate_fix(self, module: str):
        """
        Thử import lại module sau khi fix.
        Nếu thành công → clear khỏi ErrorRegistry.
        Nếu thất bại → để registry tự quản lý retry.
        """
        try:
            # Reload module để kiểm tra patch có hợp lệ không
            import importlib
            importlib.invalidate_caches()
            importlib.import_module(module)
            logger.info(f"[AutonomousEngine] Validate thành công: '{module}'. Fix được chấp nhận.")
            error_registry.clear(module)
        except Exception as e:
            logger.warning(
                f"[AutonomousEngine] Validate thất bại cho '{module}': {e}. "
                "Registry giữ nguyên để retry sau."
            )


# Global instance
autonomous_engine = AutonomousEngine()
