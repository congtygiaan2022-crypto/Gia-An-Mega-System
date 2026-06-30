"""
Test hoàn chỉnh luồng đăng bài FB:
- Dùng ảnh & text có sẵn (temp_test_img.png / temp_test_text.txt)
- Chạy SocialPoster với URL Fanpage thật
- Xem log chi tiết từng bước
"""
import time
import sys
import os
from playwright.sync_api import sync_playwright
import profile_manager
from social_poster import SocialPoster

sys.stdout.reconfigure(encoding='utf-8')

# ============ CẤU HÌNH TEST ============
PROFILE_NAME = "Yui Hatano"
# Dùng URL fanpage đầu tiên từ lỗi trong log
FANPAGE_URL = "https://business.facebook.com/latest/composer/?asset_id=1016130821593526&business_id=1016985112612772"

# Dùng file text & ảnh có sẵn
TXT_PATH  = os.path.join(os.getcwd(), "temp_test_text.txt")
IMG_PATH  = os.path.join(os.getcwd(), "temp_test_img.png")
# =======================================

def main():
    print("=" * 60)
    print(f"TEST ĐƠN VỊ: Đăng bài Fanpage FB")
    print(f"Profile  : {PROFILE_NAME}")
    print(f"URL      : {FANPAGE_URL}")
    print(f"Text     : {TXT_PATH} -> exists={os.path.exists(TXT_PATH)}")
    print(f"Image    : {IMG_PATH} -> exists={os.path.exists(IMG_PATH)}")
    print("=" * 60)

    if not os.path.exists(TXT_PATH):
        print("❌ Thiếu file text! Tạo file tạm...")
        with open(TXT_PATH, "w", encoding="utf-8") as f:
            f.write("🌺 Test đăng bài tự động ☀️✨")

    if not os.path.exists(IMG_PATH):
        print("❌ Thiếu file ảnh! Dùng ảnh dummy...")
        IMG_PATH_USE = os.path.join(os.getcwd(), "dummy.png")
    else:
        IMG_PATH_USE = IMG_PATH

    pm = profile_manager.ProfileManager("profiles")

    with sync_playwright() as p:
        print(f"\n[{PROFILE_NAME}] Khởi động trình duyệt...")
        context = pm.launch_browser_for_profile(p, PROFILE_NAME, headless=False)

        poster = SocialPoster(context, FANPAGE_URL)
        try:
            print(f"[{PROFILE_NAME}] Bắt đầu đăng bài...\n")
            start = time.time()
            result = poster.post_to_fanpage(
                PROFILE_NAME,
                TXT_PATH,
                IMG_PATH_USE,
                cleanup=False   # Không xóa file test
            )
            elapsed = time.time() - start
            if result:
                print(f"\n✅ THÀNH CÔNG! Đăng bài hoàn tất sau {elapsed:.1f}s")
            else:
                print(f"\n⚠️ Hàm trả về False sau {elapsed:.1f}s")
        except Exception as e:
            print(f"\n❌ LỖI: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print(f"\n[{PROFILE_NAME}] Đóng trình duyệt...")
            try:
                context.close()
            except Exception:
                pass

    print("\n" + "=" * 60)
    print("TEST KẾT THÚC")
    print("=" * 60)

if __name__ == "__main__":
    main()
