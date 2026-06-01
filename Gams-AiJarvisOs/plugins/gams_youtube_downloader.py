import subprocess
import os
import sys
from core.logger import get_module_logger

logger = get_module_logger("gams_youtube_downloader")

class Plugin:
    def __init__(self):
        self.name = "gams_youtube_downloader"
        self.description = "Tải video YouTube chất lượng cao từ liên kết hoặc danh sách phát."

    def run(self, **kwargs):
        cwd = r"E:\Gams-YoutubeDownloader"
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
