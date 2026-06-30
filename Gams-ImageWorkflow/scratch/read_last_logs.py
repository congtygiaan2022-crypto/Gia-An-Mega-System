import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db_manager

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

status_info = db_manager.get_all_status(["Test tool"])
logs = status_info.get("Test tool", {}).get("logs", [])
print("--- LAST 30 LOG LINES ---")
for log in logs[-30:]:
    print(log)
