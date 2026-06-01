import sys
import os

# Add the javis-agent path to sys.path
sys.path.append(os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')), 'Gams-AiJarvisOs', 'javis-agent'))

from plugins.jarvis_telegram_report_assistant import Plugin

p = Plugin()
print("Checking status...")
print(f"Is running: {p.is_running()}")

print("Triggering run (should start service)...")
result = p.run()
print(f"Result: {result}")

import time
time.sleep(2)
print(f"Is running now: {p.is_running()}")

# The bot will fail if TOKEN is missing, but the process should at least start for a moment
