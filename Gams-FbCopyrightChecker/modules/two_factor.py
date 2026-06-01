"""
TOTP 2FA helper — nhập secret key (base32), xuất mã 6 số mỗi 30 giây.
"""
import pyotp
import json
import os

from modules.config_loader import CONFIG
from modules.logger import get_logger

log = get_logger(__name__)


def get_totp_code(secret: str = None) -> str:
    """
    Tạo mã OTP 6 số từ secret key (base32).
    Nếu không truyền secret, lấy từ config['facebook']['2fa_secret'].
    """
    if secret is None:
        secret = CONFIG["facebook"].get("2fa_secret", "").strip()

    if not secret:
        raise ValueError("2FA secret chưa được cài đặt. Thêm '2fa_secret' vào config.json.")

    # Xóa spaces và dashes (định dạng Google Authenticator hiển thị có dấu cách)
    secret = secret.replace(" ", "").replace("-", "").upper()

    totp = pyotp.TOTP(secret)
    code = totp.now()
    remaining = totp.interval - (__import__('time').time() % totp.interval)
    log.debug(f"2FA code generated (valid for {remaining:.0f}s)")
    return code


def is_valid_secret(secret: str) -> bool:
    """Kiểm tra secret key có đúng định dạng base32 không."""
    try:
        pyotp.TOTP(secret.replace(" ", "").replace("-", "").upper()).now()
        return True
    except Exception:
        return False


def set_secret_interactive() -> str:
    """
    Cho phép người dùng nhập secret key từ terminal và lưu vào config.json.
    Trả về mã 6 số đầu tiên để xác nhận.
    """
    print("\n=== Cài đặt 2FA ===")
    print("Nhập secret key (base32) từ ứng dụng Facebook / Google Authenticator:")
    secret = input("Secret key: ").strip().replace(" ", "")

    if not is_valid_secret(secret):
        print("[LỖI] Secret key không hợp lệ. Vui lòng kiểm tra lại.")
        return ""

    # Lưu vào config.json
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["facebook"]["2fa_secret"] = secret
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

    code = pyotp.TOTP(secret).now()
    print("\n[OK] Đã lưu secret key.")
    print(f"     Mã 2FA hiện tại: {code}")
    return code
