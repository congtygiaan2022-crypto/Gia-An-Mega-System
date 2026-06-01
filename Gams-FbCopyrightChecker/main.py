import os
"""
fb_copyright_checker — main entry point

Cách dùng:
  python main.py              # mở Dashboard GUI  (mặc định)
  python main.py cli          # chạy CLI không có giao diện
  python main.py api          # khởi động FastAPI REST server (port 8000)
  python main.py setup-2fa    # nhập và lưu secret key 2FA
  python main.py show-2fa     # hiển thị mã 6 số hiện tại
"""
import atexit
import signal
import sys
import time

# Add Jarvis OS core for global logger
JARVIS_CORE_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')), 'Gams-AiJarvisOs', 'core')
if JARVIS_CORE_PATH not in sys.path:
    sys.path.insert(0, JARVIS_CORE_PATH)
try:
    import global_logger
except ImportError:
    global_logger = None

# Fix UTF-8 encoding trên Windows (tránh lỗi tiếng Việt)
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

from modules.config_loader import CONFIG
from modules.logger import get_logger

log = get_logger("main")


# ── Shutdown hook: đóng mọi Chrome profile của tool khi thoát ───────────────

def _shutdown_chrome_profiles():
    """Đóng tất cả Chrome profiles thuộc tool — gọi khi app thoát."""
    try:
        from agent.chrome_manager import close_all_tool_profiles
        close_all_tool_profiles()
    except Exception as e:
        log.debug(f"shutdown chrome profiles: {e}")

atexit.register(_shutdown_chrome_profiles)

def _signal_handler(sig, frame):
    log.info(f"Nhận tín hiệu {sig} — đang dọn dẹp...")
    if global_logger:
        global_logger.log_history("FbCopyrightChecker", f"Nhận tín hiệu {sig}")
    _shutdown_chrome_profiles()
    sys.exit(0)

signal.signal(signal.SIGINT,  _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ─────────────────────────────────────────────────────────────────────────────

from modules.two_factor import get_totp_code, set_secret_interactive


def cmd_setup_2fa():
    set_secret_interactive()


def cmd_show_2fa():
    try:
        code = get_totp_code()
        print(f"\nMã 2FA hiện tại: {code}\n")
    except ValueError as e:
        print(f"[LỖI] {e}")
        print("Chạy:  python main.py setup-2fa  để cài đặt secret key.")


def run_cli():
    from modules.database import Database
    from modules.fb_login import build_driver, login
    from modules.fb_profile import get_profile_info, get_fanpages, save_profile_to_config
    from modules.copyright_checker import run_full_copyright_check
    from agent.act import chrome_profile_dir
    from agent.chrome_manager import ManagedChromeProfile

    log.info("=== FB Copyright Checker (CLI) đang khởi động ===")
    db = Database()

    # Xác định profile dir cho CLI (dùng uid từ config nếu có)
    uid = CONFIG["facebook"].get("uid", "") or "cli"
    profile_dir = chrome_profile_dir(uid)

    with ManagedChromeProfile(profile_dir) as managed:
        driver = build_driver()
        managed._driver = driver  # để context manager quit() khi xong

        try:
            if not login(driver):
                log.critical("Không thể đăng nhập. Dừng chương trình.")
                sys.exit(1)

            log.info("Đang lấy thông tin tài khoản...")
            profile = get_profile_info(driver)
            save_profile_to_config(profile)
            log.info(f"Profile: {profile.get('name')} — {profile.get('profile_url')}")

            log.info("Đang lấy danh sách fanpage...")
            fanpages = get_fanpages(driver)
            log.info(f"Tìm thấy {len(fanpages)} fanpage")

            interval    = CONFIG["checker"]["scan_interval_seconds"]
            auto_delete = CONFIG["checker"]["auto_delete_flagged"]

            while True:
                log.info("--- Bắt đầu quét bản quyền ---")
                try:
                    result = run_full_copyright_check(
                        driver, db, fanpages,
                        auto_delete=auto_delete,
                        account_name=profile.get("name", "CLI"),
                        profile_dir=profile_dir,
                    )
                    # Cập nhật driver: run_full_copyright_check có thể đã rebuild Chrome
                    if result.get("driver") and result["driver"] is not driver:
                        driver = result["driver"]
                        managed._driver = driver
                    log.info(f"Kết quả: {result['total_appeals']} vi phạm | {result['deleted']} đã xóa")
                except Exception as scan_err:
                    log.error(f"Lỗi lần quét này (sẽ thử lại): {scan_err}", exc_info=True)
                    if global_logger:
                        import traceback
                        global_logger.report_bug("FbCopyrightChecker", "run_full_copyright_check", str(scan_err), {"traceback": traceback.format_exc()})
                log.info(f"Quét tiếp sau {interval} giây. Nhấn Ctrl+C để dừng.")
                time.sleep(interval)

        except KeyboardInterrupt:
            log.info("Người dùng đã dừng chương trình.")
        except Exception as e:
            log.critical(f"Lỗi không xử lý được: {e}", exc_info=True)
            if global_logger:
                import traceback
                global_logger.report_bug("FbCopyrightChecker", "main", str(e), {"traceback": traceback.format_exc()})
        finally:
            db.close()
            log.info("=== FB Copyright Checker đã dừng ===")
            # ManagedChromeProfile.__exit__ sẽ tự quit driver + close profile


def run_api():
    try:
        import uvicorn
    except ImportError:
        print("[LỖI] uvicorn chưa cài. Chạy: pip install uvicorn fastapi")
        sys.exit(1)

    api_cfg = CONFIG.get("api", {})
    host = api_cfg.get("host", "0.0.0.0")
    port = api_cfg.get("port", 8000)
    log.info(f"=== FB Copyright Checker API Server tại http://{host}:{port}/docs ===")
    uvicorn.run("api.server:app", host=host, port=port, reload=False, log_level="info")


def run_gui():
    from gui.dashboard import run_dashboard
    run_dashboard()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "gui"
    if cmd == "setup-2fa":
        cmd_setup_2fa()
    elif cmd == "show-2fa":
        cmd_show_2fa()
    elif cmd == "cli":
        run_cli()
    elif cmd == "api":
        run_api()
    else:
        run_gui()

