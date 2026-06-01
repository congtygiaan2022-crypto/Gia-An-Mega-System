import argparse
import logging
import os
import sys

# Configure stdout to display in CMD properly
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout
)
log = logging.getLogger("run_cli")

def main():
    parser = argparse.ArgumentParser(description="Run Facebook Copyright Checker for a specific account via CLI")
    parser.add_argument("--account-id", type=int, required=True, help="Database ID of the account")
    parser.add_argument("--auto-delete", action="store_true", help="Automatically delete flagged posts")
    args = parser.parse_args()

    # Append root path
    root_dir = os.path.dirname(os.path.abspath(__file__))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    from modules.account_manager import get_manager
    from modules.config_loader import CONFIG
    from modules.fb_login import build_driver, login
    from modules.copyright_checker import run_full_copyright_check
    from modules.database import Database
    from agent.act import chrome_profile_dir
    from agent.chrome_manager import ensure_profile_closed

    mgr = get_manager()
    # Find account by id
    all_accs = mgr.get_all()
    acc = next((a for a in all_accs if a.id == args.account_id), None)

    if not acc:
        log.error(f"Account with ID {args.account_id} not found in DB.")
        sys.exit(1)

    log.info(f"Starting check for account: {acc.display_name}")

    # Xác định profile dir cho tài khoản này
    uid = getattr(acc, "uid", "") or str(acc.id) or "cli"
    profile_dir = chrome_profile_dir(uid)

    # Temporary modify config for this run
    CONFIG["facebook"]["email"] = acc.email
    CONFIG["facebook"]["password"] = acc.password
    CONFIG["facebook"]["2fa_secret"] = acc.secret_2fa

    # Đảm bảo profile sạch trước khi mở
    try:
        ensure_profile_closed(profile_dir)
    except Exception:
        pass

    driver = None
    db = None
    try:
        driver = build_driver()
        log.info("Logging into Facebook...")
        if not login(driver):
            log.error("Login failed. Cannot proceed with checking.")
            sys.exit(1)

        db = Database()
        fanpages = acc.fanpages or []
        log.info(f"Loaded {len(fanpages)} fanpages for this account.")

        result = run_full_copyright_check(
            driver, db, fanpages, auto_delete=args.auto_delete,
            log_callback=log.info,
            account_name=acc.display_name,
            profile_dir=profile_dir,
        )

        # Cập nhật driver nếu Chrome đã bị rebuild trong quá trình quét
        if result.get("driver") and result["driver"] is not driver:
            driver = result["driver"]

        log.info(f"Check finished: {result['total_appeals']} flagged, {result['deleted']} deleted.")

    except Exception as e:
        log.error(f"Error during check: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if db:
            db.close()
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

        input("\n[Nhấn Enter để thoát cửa sổ này...]")

if __name__ == "__main__":
    main()
