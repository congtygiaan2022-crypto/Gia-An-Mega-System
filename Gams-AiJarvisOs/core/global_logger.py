import os
import json
import time
import uuid
import datetime
import traceback

# Root directory is E:\Gams-AiJarvisOs
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT_DIR, "logs")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

FIND_BUG_FILE = os.path.join(LOG_DIR, "find_bug.json")
HISTORY_FILE = os.path.join(LOG_DIR, "history.log")
ERROR_FILE = os.path.join(LOG_DIR, "error.log")
LOCK_FILE = os.path.join(LOG_DIR, "find_bug.lock")

class SimpleFileLock:
    def __init__(self, lock_file):
        self.lock_file = lock_file

    def acquire(self, timeout=10):
        start = time.time()
        while time.time() - start < timeout:
            try:
                fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.close(fd)
                return True
            except FileExistsError:
                time.sleep(0.1)
            except Exception:
                time.sleep(0.1)
        return False

    def release(self):
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
        except:
            pass

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

def log_history(project, action, status="INFO", details=""):
    """Ghi log lịch sử thao tác."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{project}] [{status}] {action} - {details}\n"
    
    lock = SimpleFileLock(os.path.join(LOG_DIR, "history.lock"))
    with lock:
        try:
            with open(HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            print(f"Lỗi khi ghi lịch sử: {e}")

def log_error(project, error_msg, exception=None):
    """Ghi log lỗi thông thường."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tb = ""
    if exception:
        tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        
    log_line = f"[{timestamp}] [{project}] ERROR: {error_msg}\n{tb}\n"
    
    lock = SimpleFileLock(os.path.join(LOG_DIR, "error.lock"))
    with lock:
        try:
            with open(ERROR_FILE, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            print(f"Lỗi khi ghi error log: {e}")

def report_bug(project, module, exception_details, context_data=None):
    """
    Ghi một cấu trúc bug vào find_bug.json.
    """
    bug_entry = {
        "bug_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.now().isoformat(),
        "project": project,
        "module": module,
        "exception_details": exception_details,
        "context_data": context_data or {},
        "status": "pending_fix"
    }
    
    lock = SimpleFileLock(LOCK_FILE)
    with lock:
        try:
            bugs = []
            if os.path.exists(FIND_BUG_FILE):
                try:
                    with open(FIND_BUG_FILE, "r", encoding="utf-8") as f:
                        bugs = json.load(f)
                except json.JSONDecodeError:
                    backup_name = FIND_BUG_FILE + f".bak.{int(time.time())}"
                    os.rename(FIND_BUG_FILE, backup_name)
                    bugs = []
            
            bugs.append(bug_entry)
            
            with open(FIND_BUG_FILE, "w", encoding="utf-8") as f:
                json.dump(bugs, f, indent=4, ensure_ascii=False)
                
            print(f"[{project}] Da report bug ID: {bug_entry['bug_id']} vao find_bug.json")
            
        except Exception as e:
            try:
                print(f"Loi khi ghi find_bug.json: {e}")
            except: pass
