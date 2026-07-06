import sqlite3
import json
from datetime import datetime

DB_FILE = "database.db"

def get_connection():
    # check_same_thread=False vì sẽ có nhiều luồng Playwright cùng đọc dữ liệu
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Bảng global_settings lưu key-value
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Bảng profile_settings lưu cấu hình từng profile
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile_settings (
            profile_name TEXT PRIMARY KEY,
            config_json TEXT
        )
    """)
    
    # Bảng logs lưu lịch sử và trạng thái
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile_logs (
            profile_name TEXT PRIMARY KEY,
            status TEXT,
            logs_json TEXT
        )
    """)
    
    # Bảng processed_posts lưu lịch sử các bài đã reup
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_posts (
            profile_name TEXT,
            platform TEXT,
            post_id TEXT,
            processed_at TEXT,
            PRIMARY KEY (profile_name, platform, post_id)
        )
    """)
    
    conn.commit()
    conn.close()

# --- LOGS & STATUS ---
def init_profile_log(profile_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO profile_logs (profile_name, status, logs_json) VALUES (?, 'Idle', '[]')", (profile_name,))
    conn.commit()
    conn.close()

def set_status(profile_name, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE profile_logs SET status = ? WHERE profile_name = ?", (status, profile_name))
    conn.commit()
    conn.close()

def log_msg(profile_name, msg):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT logs_json FROM profile_logs WHERE profile_name = ?", (profile_name,))
    row = cursor.fetchone()
    if row:
        logs = json.loads(row[0])
        time_str = datetime.now().strftime("[%d/%m %H:%M]")
        full_msg = f"{time_str} {msg}"
        logs.append(full_msg)
        if len(logs) > 50: # Giữ 50 log gần nhất
            logs = logs[-50:]
        cursor.execute("UPDATE profile_logs SET logs_json = ? WHERE profile_name = ?", (json.dumps(logs, ensure_ascii=False), profile_name))
        conn.commit()
    conn.close()

def clear_profile_log(profile_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE profile_logs SET logs_json = '[]' WHERE profile_name = ?", (profile_name,))
    conn.commit()
    conn.close()

def clear_all_profile_logs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE profile_logs SET logs_json = '[]'")
    conn.commit()
    conn.close()

def get_all_status(profiles):
    import os
    conn = get_connection()
    cursor = conn.cursor()
    result = {}
    for p in profiles:
        cursor.execute("SELECT status, logs_json FROM profile_logs WHERE profile_name = ?", (p,))
        row = cursor.fetchone()
        
        status_val = "Idle"
        logs = []
        if row:
            status_val = row[0]
            try:
                logs = json.loads(row[1])
            except:
                logs = []
                
        # 1. Đếm số bài đăng thành công và số lỗi từ logs
        success_count = 0
        errors_count = 0
        for log in logs:
            log_lower = log.lower()
            if "đăng bài thành công" in log_lower or "xem như đăng thành công" in log_lower or "đăng thành công" in log_lower:
                success_count += 1
            if any(keyword in log_lower for keyword in ["lỗi", "loi", "thất bại", "that bai", "error", "exception", "timeout"]):
                if "warning:" not in log_lower and "canh bao:" not in log_lower:
                    errors_count += 1
                    
        # 2. Đọc config từ profile_settings để lấy cấu hình
        cursor.execute("SELECT config_json FROM profile_settings WHERE profile_name = ?", (p,))
        cfg_row = cursor.fetchone()
        cfg = {}
        if cfg_row:
            try:
                cfg = json.loads(cfg_row[0])
            except:
                cfg = {}
                
        # 3. Đếm số lượng ảnh cục bộ trong input_img_dir
        input_img_dir = cfg.get("input_img_dir", "").strip()
        img_count = 0
        if input_img_dir and os.path.exists(input_img_dir):
            try:
                img_count = len([f for f in os.listdir(input_img_dir) if os.path.isfile(os.path.join(input_img_dir, f))])
            except:
                img_count = 0
                
        # 4. Trích xuất cấu hình hiển thị
        ai_source = cfg.get("ai_source", "google")
        fanpage_url = cfg.get("fanpage_url", "").strip()
        fanpage_name = cfg.get("fanpage_name", "").strip()
        
        if not fanpage_name:
            if fanpage_url:
                fanpage_name = fanpage_url.split('/')[-1] if '/' in fanpage_url else fanpage_url
            else:
                fanpage_name = "-"
                
        result[p] = {
            "status": status_val, 
            "logs": logs,
            "mini_stats": {
                "total_posts": success_count,
                "input_img_count": img_count,
                "ai_source": ai_source,
                "total_errors": errors_count,
                "fanpage_name": fanpage_name
            }
        }
    conn.close()
    return result

# --- GLOBAL SETTINGS ---
def get_global_config():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM global_settings WHERE key = 'run_config'")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        cfg = json.loads(row[0])
        if "apply_fb_global" not in cfg:
            cfg["apply_fb_global"] = False
        if "global_facebook_account" not in cfg:
            cfg["global_facebook_account"] = ""
        return cfg
    return {
        "loop_type": "1", "loop_count": "1", 
        "delay_type": "fixed", "delay_fixed": "10", 
        "delay_rand_all_min": "43200", "delay_rand_all_max": "86400",
        "delay_rand_ind_min": "43200", "delay_rand_ind_max": "86400", 
        "delay_times": [],
        "gpt_limit_action": "wait_limit",
        "apply_gpt_limit_global": True,
        "apply_fb_global": False,
        "global_facebook_account": ""
    }

def save_global_config(config_dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO global_settings (key, value) 
        VALUES ('run_config', ?) 
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (json.dumps(config_dict, ensure_ascii=False),))
    conn.commit()
    conn.close()

# --- PROFILE SETTINGS ---
def rename_profile(old_name, new_name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE profile_settings SET profile_name = ? WHERE profile_name = ?", (new_name, old_name))
        cursor.execute("UPDATE profile_logs SET profile_name = ? WHERE profile_name = ?", (new_name, old_name))
        conn.commit()
    except:
        pass
    conn.close()

def get_profile_config(profile_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT config_json FROM profile_settings WHERE profile_name = ?", (profile_name,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return {}

def save_profile_config(profile_name, config_dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO profile_settings (profile_name, config_json) 
        VALUES (?, ?) 
        ON CONFLICT(profile_name) DO UPDATE SET config_json=excluded.config_json
    """, (profile_name, json.dumps(config_dict, ensure_ascii=False)))
    conn.commit()
    conn.close()

# Tự động tạo DB khi module được load
try:
    init_db()
except sqlite3.OperationalError as e:
    if "locked" in str(e).lower() or "busy" in str(e).lower():
        import time
        try:
            time.sleep(0.5)
            init_db()
        except:
            pass
except Exception:
    pass

def mark_post_processed(profile_name, platform, post_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO processed_posts (profile_name, platform, post_id, processed_at) VALUES (?, ?, ?, ?)", 
                   (profile_name, platform, post_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_profile_dashboard_stats(profile_name):
    import os
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Tổng số bài đã reup
    cursor.execute("SELECT COUNT(*) FROM processed_posts WHERE profile_name = ?", (profile_name,))
    total_posts = cursor.fetchone()[0]
    
    # 2. Lịch sử reup gần nhất (15 bài)
    cursor.execute("""
        SELECT platform, post_id, processed_at 
        FROM processed_posts 
        WHERE profile_name = ? 
        ORDER BY processed_at DESC 
        LIMIT 15
    """, (profile_name,))
    history_rows = cursor.fetchall()
    history = []
    for r in history_rows:
        history.append({
            "platform": r[0],
            "post_id": r[1],
            "processed_at": r[2]
        })
        
    # 3. Trạng thái và Logs để parse lỗi & trùng lặp
    cursor.execute("SELECT status, logs_json FROM profile_logs WHERE profile_name = ?", (profile_name,))
    row = cursor.fetchone()
    status = "Idle"
    logs = []
    if row:
        status = row[0]
        try:
            logs = json.loads(row[1])
        except:
            logs = []
            
    # 4. Đọc config từ profile_settings để lấy cấu hình
    cursor.execute("SELECT config_json FROM profile_settings WHERE profile_name = ?", (profile_name,))
    cfg_row = cursor.fetchone()
    cfg = {}
    if cfg_row:
        try:
            cfg = json.loads(cfg_row[0])
        except:
            cfg = {}
            
    # 5. Đếm số lượng ảnh cục bộ trong input_img_dir
    input_img_dir = cfg.get("input_img_dir", "").strip()
    img_count = 0
    if input_img_dir and os.path.exists(input_img_dir):
        try:
            img_count = len([f for f in os.listdir(input_img_dir) if os.path.isfile(os.path.join(input_img_dir, f))])
        except:
            img_count = 0
            
    conn.close()
    
    # Phân tích log tìm lỗi & số bài trùng lặp
    errors = []
    skipped_count = 0
    
    for log in logs:
        log_lower = log.lower()
        if any(keyword in log_lower for keyword in ["lỗi", "loi", "thất bại", "that bai", "error", "exception", "timeout"]):
            if "warning:" not in log_lower and "canh bao:" not in log_lower:
                errors.append(log)
        if any(keyword in log_lower for keyword in ["bỏ qua", "bo qua"]):
            skipped_count += 1
            
    return {
        "profile_name": profile_name,
        "status": status,
        "total_posts": total_posts,
        "history": history,
        "errors": errors[-5:], # Chỉ lấy 5 lỗi gần nhất để show
        "total_errors": len(errors),
        "skipped_count": skipped_count,
        "input_img_count": img_count
    }

def backfill_processed_posts():
    import re
    from datetime import datetime
    conn = get_connection()
    cursor = conn.cursor()
    
    # Đảm bảo bảng đã tồn tại
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_posts (
            profile_name TEXT,
            platform TEXT,
            post_id TEXT,
            processed_at TEXT,
            PRIMARY KEY (profile_name, platform, post_id)
        )
    """)
    
    cursor.execute("SELECT profile_name, logs_json FROM profile_logs")
    rows = cursor.fetchall()
    
    current_year = datetime.now().year
    
    for profile_name, logs_json in rows:
        if not logs_json:
            continue
        try:
            logs = json.loads(logs_json)
        except Exception:
            continue
            
        for log in logs:
            log_lower = log.lower()
            if "✅ đăng bài thành công" in log_lower or "xem như đăng thành công" in log_lower:
                match = re.search(r'\[(\d{2}/\d{2} \d{2}:\d{2})\]', log)
                if match:
                    time_part = match.group(1)
                    try:
                        dt = datetime.strptime(f"{time_part}/{current_year}", "%d/%m %H:%M/%Y")
                        processed_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        processed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    processed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                post_id = f"Post_{processed_at.replace(' ', '_').replace(':', '')}"
                
                cursor.execute("""
                    SELECT COUNT(*) FROM processed_posts 
                    WHERE profile_name = ? AND platform = 'facebook' AND processed_at = ?
                """, (profile_name, processed_at))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT OR IGNORE INTO processed_posts (profile_name, platform, post_id, processed_at) 
                        VALUES (?, 'facebook', ?, ?)
                    """, (profile_name, post_id, processed_at))
                    
    conn.commit()
    conn.close()

# Tự động gọi backfill khi module được tải
try:
    backfill_processed_posts()
except Exception:
    pass


