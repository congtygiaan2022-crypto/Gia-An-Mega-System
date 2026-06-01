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
    conn = get_connection()
    cursor = conn.cursor()
    result = {}
    for p in profiles:
        cursor.execute("SELECT status, logs_json FROM profile_logs WHERE profile_name = ?", (p,))
        row = cursor.fetchone()
        if row:
            result[p] = {"status": row[0], "logs": json.loads(row[1])}
        else:
            result[p] = {"status": "Idle", "logs": []}
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
        return json.loads(row[0])
    return {
        "loop_type": "1", "loop_count": "1", 
        "delay_type": "fixed", "delay_fixed": "10", 
        "delay_rand_min": "10", "delay_rand_max": "60", "delay_times": []
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
