import os
import sys
import time
import json
import subprocess
import requests
from core.logger import get_module_logger

logger = get_module_logger("gams_insight_reader")

def send_telegram_report(page_name, stt, status, data=None, post_info=None, error_msg=None, link_info=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    owners = []
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if chat_id:
        owners.append(str(chat_id).strip())
        
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    settings_file = os.path.join(plugin_dir, "data", "plugin_settings.json")
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
                p_settings = settings.get("jarvis_telegram_report_assistant", {})
                if p_settings.get("token"):
                    token = p_settings["token"]
                if p_settings.get("owners"):
                    p_owners = p_settings["owners"]
                    if isinstance(p_owners, list):
                        owners.extend([str(o).strip() for o in p_owners])
                    else:
                        owners.append(str(p_owners).strip())
        except Exception as e:
            logger.error(f"Lỗi khi đọc file cấu hình Telegram: {e}")
            
    # Clean and unique owners
    owners = list(set([o for o in owners if o]))
    if not token or not owners:
        logger.warning("Không có cấu hình token hoặc chat ID Telegram để gửi báo cáo tức thời.")
        return
        
    if status == "Xong":
        total_followers = "-"
        if link_info and link_info.get("total_followers"):
            total_followers = link_info["total_followers"]
        if data:
            if data.get("total_followers"):
                total_followers = data["total_followers"]
            
        followers_new = "0"
        interactions = "0"
        views = "0"
        contacts = "0"
        period = "-"
        
        if data:
            followers_new = data.get("Lượt theo dõi") or data.get("Theo dõi") or data.get("Follows") or "0"
            interactions = data.get("Lượt tương tác") or data.get("Tương tác") or data.get("Content interactions") or "0"
            views = data.get("Lượt xem") or data.get("Xem") or data.get("Views") or "0"
            contacts = data.get("Liên hệ mới") or data.get("Người liên hệ mới") or data.get("New contacts") or "0"
            period = data.get("Thời gian") or data.get("Time range") or "-"
            
        latest_post_date = "-"
        latest_post_title = "-"
        if post_info:
            latest_post_date = post_info.get("date", "-")
            latest_post_title = post_info.get("title", "-")
            
        msg = (
            f"🔔 **BÁO CÁO CẬP NHẬT FANPAGE**\n"
            f"🌐 **{page_name}** (STT: {stt})\n"
            f"──────────────────\n"
            f"👥 Tổng Follower: `{total_followers}`\n"
            f"📈 Theo dõi mới: `{followers_new}`\n"
            f"👁️ Lượt xem: `{views}`\n"
            f"🤝 Tương tác: `{interactions}`\n"
            f"📩 Liên hệ mới: `{contacts}`\n"
            f"📅 Chu kỳ: `{period}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✍️ **Bài viết gần nhất:**\n"
            f"📅 `{latest_post_date}`\n"
            f"📝 `{latest_post_title}`"
        )
    else:
        msg = (
            f"🔔 **BÁO CÁO CẬP NHẬT FANPAGE**\n"
            f"🌐 **{page_name}** (STT: {stt})\n"
            f"──────────────────\n"
            f"❌ **Cập nhật thất bại**\n"
            f"⚠️ Chi tiết: `{error_msg or 'Lỗi không xác định'}`"
        )
        
    for oid in owners:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": oid,
                "text": msg,
                "parse_mode": "Markdown"
            }
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code != 200:
                logger.error(f"Gửi Telegram thất bại cho {oid}: {res.text}")
        except Exception as te:
            logger.error(f"Lỗi gửi Telegram cho {oid}: {te}")

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
                        
                        # Send immediate report
                        send_telegram_report(
                            page_name=link.get('page_name', url),
                            stt=i + 1,
                            status="Xong",
                            data=data,
                            post_info=post_info,
                            link_info=link
                        )
                    except Exception as e:
                        logger.warning(f"Lỗi đọc {url}: {e}")
                        dm.update_insight_and_post(i, "Lỗi", None, None)
                        
                        # Send immediate failure report
                        send_telegram_report(
                            page_name=link.get('page_name', url),
                            stt=i + 1,
                            status="Lỗi",
                            error_msg=str(e),
                            link_info=link
                        )

                bm.close_browser()
                return {"status": "success", "message": f"Đã xử lý {len(links)} fanpages."}

        except Exception as e:
            logger.error(f"Plugin gams_insight_reader lỗi: {e}")
            return {"status": "error", "message": str(e)}
