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
            os.makedirs(self.data_dir)

    def is_running(self):
        if not os.path.exists(self.pid_file):
            return False
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                # Check if it's actually our python process
                if "python" in proc.name().lower() and any("telegram_bot_service.py" in arg for arg in proc.cmdline()):
                    return True
            return False
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra trạng thái bot: {e}")
            return False

    def start_service(self):
        logger.info("Đang khởi động dịch vụ Telegram Bot...")
        try:
            # Launch in a visible CMD window as requested by user
            # Using /k to keep window open if any error happens during bootstrap
            import subprocess
            cmd = f'start "Jarvis_Manual_Telegram_Bot" cmd /k "python \"{self.service_script}\""'
            subprocess.Popen(cmd, shell=True)
            logger.info("Dịch vụ bot đã được chạy trong cửa sổ mới.")
            return True
        except Exception as e:
            logger.error(f"Không thể khởi động dịch vụ bot: {e}")
            return False

    def stop_service(self):
        if not os.path.exists(self.pid_file):
            return True
        try:
            with open(self.pid_file, 'r') as f:
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
        
        if action == "stop":
            # The scheduler will kill the process tree, but we can try graceful stop if they ever add one
            return {"status": "success", "message": "Signal stop."}
            
        logger.info("Starting Telegram Bot Service directly in-process...")
        try:
            from plugins.lib.telegram_bot_service import run_bot
            run_bot()
            return {"status": "success", "message": "Bot finished."}
        except Exception as e:
            logger.error(f"Error running bot service: {e}")
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    # Test execution
    p = Plugin()
    print(p.run())
