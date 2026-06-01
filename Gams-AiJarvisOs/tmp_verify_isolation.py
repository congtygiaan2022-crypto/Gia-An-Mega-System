import os
import sys
import subprocess
import time

PROJECT_ROOT = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')), 'Gams Ai Jarvis Os', 'javis-agent')
os.chdir(PROJECT_ROOT)

print("Starting verification test for Isolated Runner...")

# Mock data
plugin_name = "test_plugin"
task_id = "test_manual"
run_id = "run_test_verify"
args_json = '{"verify": true}'

# Create a simple test plugin if it doesn't exist
test_plugin_path = os.path.join(PROJECT_ROOT, "plugins", "test_plugin.py")
if not os.path.exists(test_plugin_path):
    with open(test_plugin_path, "w", encoding="utf-8") as f:
        f.write('def run(**kwargs):\n    print(f"Test plugin running with args: {kwargs}")\n    return "Verify Success"')

# Construct command
cmd = f'start cmd /c "python core/isolated_runner.py --plugin {plugin_name} --task_id {task_id} --run_id {run_id} --args \'{args_json}\'"'

print(f"Launching command: {cmd}")
subprocess.Popen(cmd, shell=True)

print("Isolated CMD should have opened and will close in 3 seconds.")
time.sleep(5)
print("Verification script finished.")
