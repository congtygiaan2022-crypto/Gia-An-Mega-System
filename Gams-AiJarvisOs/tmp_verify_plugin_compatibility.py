import subprocess
import os
import json
import time

def verify_plugin_compatibility():
    print("Verifying Plugin Compatibility (Plugin Class Support)...")
    
    # Plugins to test
    plugins = ["gams_insight_reader", "jarvis_telegram_report_assistant"]
    
    for plugin_name in plugins:
        print(f"\n--- Testing {plugin_name} ---")
        
        # 1. Create a mock argument file
        run_id = f"test_run_{plugin_name[:5]}"
        arg_file = os.path.join("tmp", f"args_{run_id}.json")
        os.makedirs("tmp", exist_ok=True)
        test_data = {"accounts": {}, "action": "check"} # 'check' is safe for the telegram plugin
        with open(arg_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)
            
        # 2. Construct the command
        task_id = "test_task_123"
        # Using /c for the test so it finishes, but our runner code handles the logic
        cmd = f'python core/isolated_runner.py --plugin {plugin_name} --task_id {task_id} --run_id {run_id} --args {arg_file}'
        
        print(f"Executing: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            print("Output:")
            print(result.stdout)
            if "[SUCCESS]" in result.stdout:
                print(f"[PASSED] {plugin_name} matched and executed via Plugin class.")
            else:
                print(f"[FAILED] {plugin_name} did not execute as expected.")
                print("Error Output:")
                print(result.stderr)
        except Exception as e:
            print(f"[CRASH] Failed to run trial for {plugin_name}: {e}")

if __name__ == "__main__":
    verify_plugin_compatibility()
