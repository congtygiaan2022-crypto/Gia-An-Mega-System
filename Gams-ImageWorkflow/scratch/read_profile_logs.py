import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db_manager

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

status_info = db_manager.get_all_status(["Test tool"])
logs = status_info.get("Test tool", {}).get("logs", [])
print("--- PROFILE LOGS FOR Test tool ---")
for log in logs:
    print(log)
