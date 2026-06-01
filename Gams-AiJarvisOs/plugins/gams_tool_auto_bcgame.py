import subprocess
import os
import sys
from core.logger import get_module_logger

logger = get_module_logger("gams_tool_auto_bcgame")

class Plugin:
    def __init__(self):
        self.name = "gams_tool_auto_bcgame"
        self.description = "Tự động đặt cược và chạy kịch bản game trên BC.Game."

    def run(self, **kwargs):
        cwd = r"E:\Gams-ToolAutoBcgame"
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
