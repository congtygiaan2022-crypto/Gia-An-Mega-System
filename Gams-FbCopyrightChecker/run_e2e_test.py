"""
Script chạy thử 1 vòng đầy đủ: đăng nhập → profile → fanpage → quét bản quyền
Dùng account đầu tiên trong accounts.json, chạy headless.
"""
import sys
import io
import os
import traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

# Patch config để chạy headless
from modules.config_loader import CONFIG
CONFIG['selenium']['headless'] = True

from modules.account_manager import get_manager
from modules.database import Database
from modules.logger import get_logger
from agent.act import build_driver_for_account, chrome_profile_dir
from agent.chrome_manager import ManagedChromeProfile

log = get_logger('e2e_test')
errors = []

def section(title):
    print(f'\n{"="*60}')
    print(f'  {title}')
    print('='*60)

# ── 0. Lấy account ────────────────────────────────────────────
section('BƯỚC 0: Lấy account từ accounts.json')
manager = get_manager()
accounts = manager.get_all()
if not accounts:
    print('FAIL: Không có account nào trong accounts.json')
    sys.exit(1)

acc = accounts[0]
print(f'Account: {acc.display_name}')
print(f'Email   : {acc.email}')
print(f'UID     : {acc.uid or "(chưa có)"}')
print(f'2FA     : {"có" if acc.secret_2fa else "không"}')
print(f'Fanpages: {len(acc.fanpages)}')

# Patch config facebook để dùng credentials thật
CONFIG['facebook']['email']      = acc.email or acc.uid
CONFIG['facebook']['password']   = acc.password
CONFIG['facebook']['2fa_secret'] = acc.secret_2fa

# ── 1. Khởi động Chrome ──────────────────────────────────────
section('BƯỚC 1: Khởi động Chrome (headless, per-account profile)')
uid = acc.uid or acc.email or 'default'
profile_dir = chrome_profile_dir(uid)
print(f'Profile dir: {profile_dir}')

driver = None
db = Database()

try:
    with ManagedChromeProfile(profile_dir) as managed:
        try:
            driver = build_driver_for_account(uid)
            managed._driver = driver
            print('OK: Chrome khởi động thành công')
        except Exception as e:
            print(f'FAIL: Chrome không khởi động được: {e}')
            traceback.print_exc()
            sys.exit(1)

        # ── 2. Đăng nhập ─────────────────────────────────────────
        section('BƯỚC 2: Đăng nhập Facebook')
        from modules.fb_login import login
        try:
            ok = login(driver)
            if ok:
                print(f'OK: Đăng nhập thành công — URL: {driver.current_url}')
            else:
                print(f'FAIL: Đăng nhập thất bại — URL: {driver.current_url}')
                errors.append('login_failed')
        except Exception as e:
            print(f'FAIL: Exception khi đăng nhập: {e}')
            traceback.print_exc()
            errors.append(f'login_exception: {e}')

        # ── 3. Lấy profile info ───────────────────────────────────
        section('BƯỚC 3: Lấy thông tin profile')
        from modules.fb_profile import get_profile_info
        try:
            profile = get_profile_info(driver)
            print(f'Tên     : {profile.get("name") or "(không lấy được)"}')
            print(f'UID     : {profile.get("uid") or "(không lấy được)"}')
            print(f'URL     : {profile.get("profile_url") or "(không lấy được)"}')
            if not profile.get('name') and not profile.get('uid'):
                errors.append('profile_empty')
                print('WARN: Không lấy được tên/uid — có thể chưa login thành công')
            else:
                print('OK')
        except Exception as e:
            print(f'FAIL: {e}')
            traceback.print_exc()
            errors.append(f'profile_exception: {e}')

        # ── 4. Lấy fanpages ───────────────────────────────────────
        section('BƯỚC 4: Lấy danh sách fanpage')
        from modules.fb_profile import get_fanpages
        fanpages = []
        try:
            fanpages = get_fanpages(driver)
            print(f'Số fanpage tìm thấy: {len(fanpages)}')
            for p in fanpages[:5]:
                print(f'  - {p.get("name")} | {p.get("url")}')
            print('OK')
        except Exception as e:
            print(f'FAIL: {e}')
            traceback.print_exc()
            errors.append(f'fanpages_exception: {e}')

        # ── 5. Quét bản quyền ─────────────────────────────────────
        section('BƯỚC 5: Quét bản quyền (profile cá nhân)')
        from modules.copyright_checker import run_full_copyright_check
        try:
            # Chỉ quét 1 fanpage đầu tiên nếu có để tiết kiệm thời gian
            test_fanpages = fanpages[:1]
            result = run_full_copyright_check(
                driver, db,
                fanpages=test_fanpages,
                auto_delete=False,
                account_name=acc.display_name,
                log_callback=lambda msg: print(f'  [scan] {msg}'),
                profile_dir=profile_dir,
            )
            print('\nKết quả:')
            print(f'  Tổng vi phạm : {result["total_appeals"]}')
            print(f'  Đã xóa       : {result["deleted"]}')
            for d in result['details'][:5]:
                print(f'  - [{d["context"]}] {d["title"][:60]} | action={d["action"]} | conf={d.get("confidence",0):.0%}')
            print('OK')
        except Exception as e:
            print(f'FAIL: {e}')
            traceback.print_exc()
            errors.append(f'copyright_check_exception: {e}')

        # ── 6. Test agent perceive ────────────────────────────────
        section('BƯỚC 6: Test agent perceive (observe_page)')
        from agent.perceive import observe_page, emit_event
        try:
            obs = observe_page(driver)
            print(f'URL       : {obs.url}')
            print(f'Title     : {obs.title[:60]}')
            print(f'Page type : {obs.page_type}')
            print(f'Text len  : {len(obs.visible_text)} chars')
            emit_event('e2e_test', {'url': obs.url, 'page_type': obs.page_type})
            print('OK: event ghi vào logs/events.jsonl')
        except Exception as e:
            print(f'FAIL: {e}')
            traceback.print_exc()
            errors.append(f'perceive_exception: {e}')

        # ── 7. Test agent decide ──────────────────────────────────
        section('BƯỚC 7: Test agent decide (classify_violation)')
        from agent.decide import classify_violation
        try:
            decision = classify_violation(obs)
            print(f'Method     : {decision.method}')
            print(f'Violation  : {decision.is_violation}')
            print(f'Confidence : {decision.confidence:.0%}')
            print(f'Action     : {decision.action}')
            print(f'Reason     : {decision.reason[:80]}')
            print('OK')
        except Exception as e:
            print(f'FAIL: {e}')
            traceback.print_exc()
            errors.append(f'decide_exception: {e}')

except Exception as e:
    print(f'\nFATAL: {e}')
    traceback.print_exc()
    errors.append(f'fatal: {e}')
finally:
    db.close()

# ── Tổng kết ──────────────────────────────────────────────────
section('TỔNG KẾT')
if not errors:
    print('ALL PASS — Tool chạy OK, không có lỗi')
else:
    print(f'CÓ {len(errors)} LỖI:')
    for e in errors:
        print(f'  - {e}')
