import sqlite3
import json
import os
import re
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
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
    
    # Bảng content_fingerprints lưu fingerprint nội dung để lọc trùng
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_name TEXT NOT NULL,
            platform TEXT NOT NULL,
            post_id TEXT NOT NULL,
            text_simhash INTEGER DEFAULT 0,
            media_hash TEXT DEFAULT '',
            media_type TEXT DEFAULT '',
            created_at TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fp_profile ON content_fingerprints (profile_name)")
    
    conn.commit()
    conn.close()

# --- PROCESSED POSTS HELPERS ---
def is_post_processed(profile_name, platform, post_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM processed_posts WHERE profile_name = ? AND platform = ? AND post_id = ?", (profile_name, platform, post_id))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def mark_post_processed(profile_name, platform, post_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO processed_posts (profile_name, platform, post_id, processed_at) VALUES (?, ?, ?, ?)", 
                   (profile_name, platform, post_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# --- CONTENT FINGERPRINTS HELPERS ---
def save_content_fingerprint(profile_name, platform, post_id, text_simhash, media_hash, media_type):
    """Lưu fingerprint nội dung của một bài viết vào database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO content_fingerprints 
        (profile_name, platform, post_id, text_simhash, media_hash, media_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (profile_name, platform, post_id, text_simhash, media_hash, media_type,
           datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_content_fingerprints(profile_name, limit=200):
    """Lấy danh sách fingerprints gần nhất của một profile để so sánh trùng."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT text_simhash, media_hash, media_type
        FROM content_fingerprints
        WHERE profile_name = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (profile_name, limit))
    rows = cursor.fetchall()
    conn.close()
    return [
        {"text_simhash": r[0], "media_hash": r[1], "media_type": r[2]}
        for r in rows
    ]

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
                
        # 1. Tổng số bài đã reup
        cursor.execute("SELECT COUNT(*) FROM processed_posts WHERE profile_name = ?", (p,))
        total_posts = cursor.fetchone()[0]
        
        # 2. Phân loại theo media_type
        cursor.execute("SELECT media_type, COUNT(*) FROM content_fingerprints WHERE profile_name = ? GROUP BY media_type", (p,))
        media_breakdown = dict(cursor.fetchall())
        
        # 3. Phân tích log tìm lỗi & số bài trùng lặp
        errors_count = 0
        skipped_count = 0
        for log in logs:
            log_lower = log.lower()
            if any(keyword in log_lower for keyword in ["lỗi", "loi", "thất bại", "that bai", "error", "exception", "timeout"]):
                if "warning:" not in log_lower and "canh bao:" not in log_lower:
                    errors_count += 1
            if any(keyword in log_lower for keyword in ["bỏ qua", "bo qua", "được xử lý/đăng trước đó"]):
                skipped_count += 1
                
        # 4. Đọc config từ profile_settings để lấy cấu hình nguồn & fanpage name
        cursor.execute("SELECT config_json FROM profile_settings WHERE profile_name = ?", (p,))
        cfg_row = cursor.fetchone()
        cfg = {}
        if cfg_row:
            try:
                cfg = json.loads(cfg_row[0])
            except:
                cfg = {}
                
        fanpage_name = cfg.get("fanpage_name", "").strip()
        if not fanpage_name:
            fanpage_url = cfg.get("fanpage_url", "").strip()
            if fanpage_url:
                fanpage_name = fanpage_url.split('/')[-1] if '/' in fanpage_url else fanpage_url
            else:
                fanpage_name = "-"
                
        has_instagram = len(cfg.get("instagram_urls", [])) > 0
        has_x = len(cfg.get("x_urls", [])) > 0
        has_threads = len(cfg.get("threads_urls", [])) > 0
        
        result[p] = {
            "status": status_val, 
            "logs": logs,
            "mini_stats": {
                "total_posts": total_posts,
                "image_count": media_breakdown.get("image", 0),
                "video_count": media_breakdown.get("video", 0),
                "skipped_count": skipped_count,
                "total_errors": errors_count,
                "fanpage_name": fanpage_name,
                "has_instagram": has_instagram,
                "has_x": has_x,
                "has_threads": has_threads
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
    
    config = {}
    is_new_or_empty = False
    
    if row:
        config = json.loads(row[0])
    else:
        is_new_or_empty = True

    # Tìm thư mục cơ sở mặc định (Ưu tiên E:\Download\SoftAI)
    base_dir = r"E:\Download\SoftAI"
    if not os.path.exists(base_dir):
        base_dir = os.path.dirname(os.path.abspath(__file__))

    import re
    safe_profile_name = re.sub(r'[\\/:*?"<>|]', '', str(profile_name))
    profile_base = os.path.join(base_dir, "reup_data", safe_profile_name)

    # Kiểm tra các folder, nếu rỗng thì điền mặc định và tạo thư mục
    updated = False
    
    if not config.get("output_txt_dir"):
        config["output_txt_dir"] = os.path.join(profile_base, "output_text")
        updated = True
        
    if not config.get("input_img_dir"):
        config["input_img_dir"] = os.path.join(profile_base, "input_media_temp")
        updated = True
        
    if not config.get("output_img_dir"):
        config["output_img_dir"] = os.path.join(profile_base, "output_images")
        updated = True

    if not config.get("reup_media_type"):
        config["reup_media_type"] = "all"
        updated = True

    # Nếu có cập nhật, tự động lưu lại vào DB và tạo folder thực tế
    if updated or is_new_or_empty:
        try:
            os.makedirs(config["output_txt_dir"], exist_ok=True)
            os.makedirs(config["input_img_dir"], exist_ok=True)
            os.makedirs(config["output_img_dir"], exist_ok=True)
        except Exception as e:
            print(f"Lỗi tạo thư mục mặc định: {e}")
            
        save_profile_config(profile_name, config)

    return config

def get_profile_dashboard_stats(profile_name):
    """Lấy dữ liệu thống kê tổng quan và lịch sử cho dashboard của một profile."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Tổng số bài đã reup
    cursor.execute("SELECT COUNT(*) FROM processed_posts WHERE profile_name = ?", (profile_name,))
    total_posts = cursor.fetchone()[0]
    
    # 2. Phân loại theo media_type
    cursor.execute("SELECT media_type, COUNT(*) FROM content_fingerprints WHERE profile_name = ? GROUP BY media_type", (profile_name,))
    media_breakdown = dict(cursor.fetchall())
    
    # 3. Lịch sử reup gần nhất (15 bài)
    cursor.execute("""
        SELECT platform, post_id, created_at, media_type 
        FROM content_fingerprints 
        WHERE profile_name = ? 
        ORDER BY created_at DESC 
        LIMIT 15
    """, (profile_name,))
    history_rows = cursor.fetchall()
    history = []
    for r in history_rows:
        history.append({
            "platform": r[0],
            "post_id": r[1],
            "processed_at": r[2],
            "media_type": r[3]
        })
        
    if not history:
        # Fallback query từ processed_posts
        cursor.execute("""
            SELECT platform, post_id, processed_at 
            FROM processed_posts 
            WHERE profile_name = ? 
            ORDER BY processed_at DESC 
            LIMIT 15
        """, (profile_name,))
        processed_rows = cursor.fetchall()
        for r in processed_rows:
            history.append({
                "platform": r[0],
                "post_id": r[1],
                "processed_at": r[2],
                "media_type": "unknown"
            })
            
    # 4. Trạng thái và Logs để parse lỗi & trùng lặp
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
            
    conn.close()
    
    # Phân tích log tìm lỗi & số bài trùng lặp
    errors = []
    skipped_count = 0
    
    for log in logs:
        log_lower = log.lower()
        if any(keyword in log_lower for keyword in ["lỗi", "loi", "thất bại", "that bai", "error", "exception", "timeout"]):
            if "warning:" not in log_lower and "canh bao:" not in log_lower:
                errors.append(log)
        if any(keyword in log_lower for keyword in ["bỏ qua", "bo qua", "được xử lý/đăng trước đó"]):
            skipped_count += 1
            
    return {
        "profile_name": profile_name,
        "status": status,
        "total_posts": total_posts,
        "image_count": media_breakdown.get("image", 0),
        "video_count": media_breakdown.get("video", 0),
        "text_count": media_breakdown.get("text", 0),
        "history": history,
        "errors": errors[-5:], # Chỉ lấy 5 lỗi gần nhất để show
        "total_errors": len(errors),
        "skipped_count": skipped_count
    }

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
