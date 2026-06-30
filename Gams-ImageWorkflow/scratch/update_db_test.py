import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db_manager

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Cập nhật cấu hình Global
g_cfg = db_manager.get_global_config()
g_cfg["apply_fb_global"] = True
g_cfg["global_facebook_account"] = "999999999999|MatKhauChung|JBSWY3DPEHPK3PXP|mailchung@gmail.com"
db_manager.save_global_config(g_cfg)

print("Đã cập nhật cấu hình Facebook chung (Global config) thành công.")
print("Global config hiện tại:", db_manager.get_global_config())
