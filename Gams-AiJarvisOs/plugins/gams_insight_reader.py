import os
import sys
import time
import json
import subprocess
from core.logger import get_module_logger

logger = get_module_logger("gams_insight_reader")

class Plugin:
    def __init__(self):
        self.name = "gams_insight_reader"
        self.description = "Đọc số liệu Insight từ các Fanpage Facebook thông qua Business Manager. Hỗ trợ đọc lượt follow, tương tác, thời gian và bài đăng mới nhất."

    def run(self, **kwargs):
        if kwargs.get("action") == "stop":
            logger.info("gams_insight_reader: Nhận lệnh stop. Đang dừng.")
            return {"status": "success", "message": "Stopped."}
            
        logger.info(f"Executing plugin: gams_insight_reader with args: {kwargs}")
        try:
            # Launch the insight reader in an isolated subprocess
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            lib_path = os.path.join(plugin_dir, "lib", "gams_utils.py")

            if not os.path.exists(lib_path):
                return {"status": "error", "message": f"Không tìm thấy lib: {lib_path}"}

            script = os.path.join(plugin_dir, "lib", "run_insight.py")
            if os.path.exists(script):
                from core.logger import run_command_with_logging
                returncode = run_command_with_logging([sys.executable, script], logger=logger)
                if returncode == 0:
                    return {"status": "success", "message": "Đã đọc insight thành công."}
                else:
                    return {"status": "error", "message": f"Script kết thúc với mã lỗi {returncode}"}
            else:
                # Fallback: run inline using gams_utils
                sys.path.insert(0, os.path.join(plugin_dir, "lib"))
                from gams_utils import DataManager, BrowserManager
                import datetime

                data_file = os.path.join(plugin_dir, "data", "gams_insight", "links.json")
                dm = DataManager(data_file)
                links = dm.links
                if not links:
                    return {"status": "success", "message": "Không có link Fanpage nào để đọc."}

                # We need a portable path for BrowserManager. 
                # For now we'll assume a default or common path, but in a real system this should be in config.
                portable_path = os.getenv("CHROME_PORTABLE_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
                bm = BrowserManager(portable_path)
                for i, link in enumerate(links):
                    url = link.get("url", "")
                    if not url or link.get("status") == "Bỏ qua":
                        continue
                    try:
                        bm.navigate_to(url)
                        time.sleep(3)
                        data = bm.extract_insight_data()
                        
                        try:
                            post_info = bm.extract_latest_post_date()
                        except Exception as pe:
                            logger.warning(f"Không thể đọc bài đăng mới nhất cho {url}: {pe}")
                            post_info = None
                            
                        dm.update_insight_and_post(i, "Xong", data, post_info)
                        logger.info(f"Đã đọc insight và bài đăng mới nhất cho: {link.get('page_name', url)}")
                    except Exception as e:
                        logger.warning(f"Lỗi đọc {url}: {e}")
                        dm.update_insight_and_post(i, "Lỗi", None, None)

                bm.close_browser()
                return {"status": "success", "message": f"Đã xử lý {len(links)} fanpages."}

        except Exception as e:
            logger.error(f"Plugin gams_insight_reader lỗi: {e}")
            return {"status": "error", "message": str(e)}
