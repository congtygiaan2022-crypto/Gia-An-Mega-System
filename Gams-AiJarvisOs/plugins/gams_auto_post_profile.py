import subprocess
import os
import sys
from core.logger import get_module_logger

logger = get_module_logger("gams_auto_post_profile")

class Plugin:
    def __init__(self):
        self.name = "gams_auto_post_profile"
        self.description = "Tự động đăng bài viết, hình ảnh lên trang cá nhân Facebook (Profile) cá nhân."

    def run(self, **kwargs):
        cwd = r"E:\Gams-AutoPostProfile"
        cmd = [sys.executable, "gui.py"]
        
        if kwargs.get("action") == "stop":
            return {"status": "success", "message": "Stopped"}
            
        logger.info(f"Khởi chạy tool {self.name} tại {cwd}...")
        
        from core.logger import run_command_with_logging
        returncode = run_command_with_logging(cmd, cwd=cwd, logger=logger)
        
        if returncode == 0:
            return {"status": "success", "message": "Hoàn thành chạy tool."}
        else:
            return {"status": "error", "message": f"Tool kết thúc với mã lỗi {returncode}"}
