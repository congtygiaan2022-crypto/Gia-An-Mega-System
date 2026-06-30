import os
import sys
import subprocess
import psutil
import time
import json
from core.logger import get_module_logger

logger = get_module_logger("jarvis_telegram_report_assistant")


class Plugin:
    def __init__(self):
        self.name = "jarvis_telegram_report_assistant"
        self.description = "Trợ lý báo cáo Telegram 24/24. Tự động gửi báo cáo insight và hỗ trợ lệnh điều khiển."
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.plugin_dir, "data")
        self.pid_file = os.path.join(self.data_dir, "telegram_bot.pid")
        self.service_script = os.path.join(self.plugin_dir, "lib", "telegram_bot_service.py")

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)

    def is_running(self):
        if not os.path.exists(self.pid_file):
            return False
        try:
            with open(self.pid_file, "r", encoding="utf-8") as f:
                pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                if "python" in proc.name().lower() and any(
                    "telegram_bot_service.py" in str(arg) for arg in proc.cmdline()
                ):
                    return True
            return False
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra trạng thái bot: {e}")
            return False

    def start_service(self):
        logger.info("Đang khởi động dịch vụ Telegram Bot...")
        try:
            import sys
            title = "Jarvis_Manual_Telegram_Bot"
            cmd = f'cmd.exe /k "title {title} && \"{sys.executable}\" \"{self.service_script}\""'
            
            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                close_fds=True
            )
            logger.info("Dịch vụ bot đã được chạy trong cửa sổ mới.")
            return True
        except Exception as e:
            logger.error(f"Không thể khởi động dịch vụ bot: {e}")
            return False

    def stop_service(self):
        if not os.path.exists(self.pid_file):
            return True
        try:
            with open(self.pid_file, "r", encoding="utf-8") as f:
                pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=5)
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            logger.info("Dịch vụ bot đã dừng.")
            return True
        except Exception as e:
            logger.error(f"Lỗi khi dừng dịch vụ bot: {e}")
            return False

    def run(self, **kwargs):
        action = kwargs.get("action", "check")

        if action == "status" or action == "check":
            running = self.is_running()
            if not running:
                logger.info("Bot is not running. Starting Telegram Bot service...")
                ok = self.start_service()
                return {
                    "status": "success" if ok else "error",
                    "running": ok,
                    "message": "Bot was not running. Automatically started it." if ok else "Failed to start bot.",
                }
            return {
                "status": "success",
                "running": True,
                "message": "Bot is running.",
            }

        if action == "start":
            if self.is_running():
                return {"status": "success", "message": "Bot is already running."}
            ok = self.start_service()
            return {
                "status": "success" if ok else "error",
                "message": "Bot started." if ok else "Failed to start bot.",
            }

        if action == "stop":
            ok = self.stop_service()
            return {
                "status": "success" if ok else "error",
                "message": "Bot stopped." if ok else "Failed to stop bot.",
            }

        if action == "run":
            logger.info("Starting Telegram Bot Service directly in-process...")
            try:
                from plugins.lib.telegram_bot_service import run_bot
            except ImportError:
                lib_dir = os.path.join(self.plugin_dir, "lib")
                if lib_dir not in sys.path:
                    sys.path.insert(0, lib_dir)
                from telegram_bot_service import run_bot

            try:
                run_bot()
                return {"status": "success", "message": "Bot finished."}
            except Exception as e:
                logger.error(f"Error running bot service: {e}")
                return {"status": "error", "message": str(e)}

        return {"status": "error", "message": f"Unknown action: {action}"}


def run(**kwargs):
    return Plugin().run(**kwargs)


if __name__ == "__main__":
    p = Plugin()
    print(p.run())