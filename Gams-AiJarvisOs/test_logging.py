import sys
import os
import time

# Ensure core is accessible
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "core"))
import global_logger

def main():
    print("Test global logger...")
    global_logger.log_history("TestProject", "Testing history log")
    
    print("Test reporting a bug...")
    try:
        1 / 0
    except ZeroDivisionError as e:
        import traceback
        global_logger.report_bug("TestProject", "test_division", str(e), {"traceback": traceback.format_exc(), "value": 1})
    
    print("Done. Check logs/history.jsonl and logs/find_bug.json")

if __name__ == "__main__":
    main()
