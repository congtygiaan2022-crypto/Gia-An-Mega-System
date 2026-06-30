import os
import sys
import time
import json
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

    owners = list(set([o for o in owners if o]))
    if not token or not owners:
        logger.warning("Không có cấu hình token hoặc chat ID Telegram để gửi báo cáo tức thời.")
        return

    if status == "Xong":
        total_followers = "-"
        if link_info and link_info.get("total_followers"):
            total_followers = link_info["total_followers"]
        if data and data.get("total_followers"):
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
                "parse_mode": "Markdown",
            }
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code != 200:
                logger.error(f"Gửi Telegram thất bại cho {oid}: {res.text}")
        except Exception as te:
            logger.error(f"Lỗi gửi Telegram cho {oid}: {te}")


class Plugin:
    def __init__(self):
        self.name = "gams_insight_reader"
        self.description = (
            "Đọc số liệu Insight từ các Fanpage Facebook thông qua Business Manager. "
            "Hỗ trợ đọc lượt follow, tương tác, thời gian và bài đăng mới nhất."
        )

    def run(self, **kwargs):
        if kwargs.get("action") == "stop":
            logger.info("gams_insight_reader: Nhận lệnh stop. Đang dừng.")
            return {"status": "success", "message": "Stopped."}

        logger.info(f"Executing plugin: gams_insight_reader with args: {kwargs}")
        try:
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
                return {"status": "error", "message": f"Script kết thúc với mã lỗi {returncode}"}

            lib_dir = os.path.join(plugin_dir, "lib")
            if lib_dir not in sys.path:
                sys.path.insert(0, lib_dir)

            from gams_utils import DataManager, BrowserManager, is_browser_disconnected_exception

            data_file = os.path.join(plugin_dir, "data", "gams_insight", "links.json")
            dm = DataManager(data_file)
            links = dm.links
            if not links:
                return {"status": "success", "message": "Không có link Fanpage nào để đọc."}

            portable_path = os.getenv(
                "CHROME_PORTABLE_PATH",
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            )
            bm = BrowserManager(portable_path)

            try:
                pages_processed = 0
                for i, link in enumerate(links):
                    url = link.get("url", "")
                    if not url or link.get("status") == "Bỏ qua":
                        continue

                    # Periodic browser restart every 15 pages to clean memory
                    if pages_processed > 0 and pages_processed % 15 == 0:
                        logger.info("Đã xử lý 15 trang, tự động khởi động lại trình duyệt...")
                        try:
                            bm.relaunch_browser()
                        except Exception as re:
                            logger.warning(f"Lỗi khi khởi động lại trình duyệt: {re}")

                    pages_processed += 1
                    page_success = False
                    page_attempts = 0
                    max_page_attempts = 2
                    
                    while page_attempts < max_page_attempts and not page_success:
                        page_attempts += 1
                        try:
                            # If we are retrying after a browser disconnect, proactively relaunch browser
                            if page_attempts > 1:
                                logger.info(f"Khởi động lại trình duyệt cho lần thử {page_attempts}/{max_page_attempts}...")
                                try:
                                    bm.relaunch_browser()
                                except Exception as re:
                                    logger.warning(f"Lỗi khi khởi động lại trình duyệt: {re}")

                            if not bm.navigate_to(url):
                                raise ValueError("Không thể truy cập hoặc tải trang Fanpage (Lỗi trình duyệt hoặc timeout).")

                            # Dynamic wait up to 15s for Facebook Business Suite async elements to load
                            insight_keys = [
                                "Lượt xem", "Lượt tương tác", "Lượt theo dõi", 
                                "Liên hệ mới", "Lượt xem trang", "Số người tiếp cận",
                                "Views", "Content interactions", "Follows", "New contacts",
                                "Lượt tương tác với nội dung", "Số lượt xem trang", "Lượt truy cập"
                            ]
                            
                            data = {}
                            start_time = time.time()
                            has_insights = False
                            while time.time() - start_time < 15:
                                data = bm.extract_insight_data()
                                has_insights = isinstance(data, dict) and any(k in data for k in insight_keys)
                                if has_insights:
                                    break
                                time.sleep(1.5)

                            if not has_insights:
                                raise ValueError("Không trích xuất được số liệu Insight (Trang lỗi hoặc sai giao diện).")

                            try:
                                post_info = bm.extract_latest_post_date()
                            except Exception as pe:
                                if is_browser_disconnected_exception(pe) or not bm.check_alive():
                                    raise pe
                                logger.warning(f"Không thể đọc bài đăng mới nhất cho {url}: {pe}")
                                post_info = None

                            # Navigate to Home to get total followers count
                            total_followers = None
                            try:
                                import urllib.parse
                                parsed = urllib.parse.urlparse(url)
                                params = urllib.parse.parse_qs(parsed.query)
                                business_id = params.get("business_id", ["1016985112612772"])[0]
                                asset_id = params.get("asset_id", [link.get("page_id", "")])[0]
                                if asset_id:
                                    total_followers = bm.extract_total_followers_from_home(business_id, asset_id)
                            except Exception as fe:
                                if is_browser_disconnected_exception(fe) or not bm.check_alive():
                                    raise fe
                                logger.warning(f"Không thể đọc tổng follow từ Home cho {url}: {fe}")

                            if total_followers:
                                if not isinstance(data, dict):
                                    data = {}
                                data["total_followers"] = total_followers
                                logger.info(f"Đã đọc tổng follow: {total_followers} cho {link.get('page_name', url)}")

                            dm.update_insight_and_post(i, "Xong", data, post_info)
                            logger.info(f"Đã đọc insight và bài đăng mới nhất cho: {link.get('page_name', url)}")

                            send_telegram_report(
                                page_name=link.get("page_name", url),
                                stt=i + 1,
                                status="Xong",
                                data=data,
                                post_info=post_info,
                                link_info=link,
                            )
                            page_success = True
                        except Exception as e:
                            err_str = str(e)
                            # Check if the error is due to browser disconnection
                            is_disconnect = "HTTPConnectionPool" in err_str or not bm.check_alive()
                            
                            if is_disconnect and page_attempts < max_page_attempts:
                                logger.warning(f"Mất kết nối trình duyệt khi đọc {url} (Thử lần {page_attempts}/{max_page_attempts}): {e}")
                                time.sleep(5)
                            else:
                                logger.warning(f"Lỗi đọc {url} (Lần thử {page_attempts}/{max_page_attempts}): {e}")
                                if is_disconnect:
                                    err_str = "Mất kết nối trình duyệt (Chrome bị tắt đột ngột)."
                                dm.update_insight_and_post(i, "Lỗi", None, None, error_msg=err_str)

                                send_telegram_report(
                                    page_name=link.get("page_name", url),
                                    stt=i + 1,
                                    status="Lỗi",
                                    error_msg=err_str,
                                    link_info=link,
                                )
                                break
            finally:
                try:
                    bm.close_browser()
                except Exception as close_err:
                    logger.warning(f"Lỗi khi đóng trình duyệt: {close_err}")

            return {"status": "success", "message": f"Đã xử lý {len(links)} fanpages."}

        except Exception as e:
            logger.error(f"Plugin gams_insight_reader lỗi: {e}")
            return {"status": "error", "message": str(e)}


def run(**kwargs):
    return Plugin().run(**kwargs)


__all__ = ["Plugin", "run", "send_telegram_report"]