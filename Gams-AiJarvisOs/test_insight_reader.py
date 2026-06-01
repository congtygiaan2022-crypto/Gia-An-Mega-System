import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'javis-agent'))

from core.plugin_engine import run_plugin

if __name__ == "__main__":
    print("Test Insight Reader Plugin...")
    # Khởi động thủ công plugin để verify
    res = run_plugin("gams_insight_reader", "test_task_id", "test_run_1")
    print(f"Result: {res}")
