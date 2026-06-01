import subprocess
import os
import sys
from core.logger import get_module_logger

logger = get_module_logger("gams_tiktok_downloader")

class Plugin:
    def __init__(self):
        self.name = "gams_tiktok_downloader"
        self.description = "Tải video TikTok hàng loạt không có logo / watermark từ danh sách link hoặc kênh."

    def run(self, **kwargs):
        cwd = r"E:\Gams-TiktokDownloader"
        cmd = [sys.executable, "main.py"]
        
        if kwargs.get("action") == "stop":
            return {"status": "success", "message": "Stopped"}
            
        logger.info(f"Khởi chạy tool {self.name} tại {cwd}...")
        
        from core.logger import run_command_with_logging
        returncode = run_command_with_logging(cmd, cwd=cwd, logger=logger)
        
        if returncode == 0:
            return {"status": "success", "message": "Hoàn thành chạy tool."}
        else:
            return {"status": "error", "message": f"Tool kết thúc với mã lỗi {returncode}"}
