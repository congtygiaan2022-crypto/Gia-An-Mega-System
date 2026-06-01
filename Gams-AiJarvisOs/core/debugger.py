import traceback
import json
import os
from core.config import PROJECT_ROOT

REQUEST_FILE = os.path.join(PROJECT_ROOT, "requests.json")

def capture_error(e):
    """Returns the full stacktrace of the exception."""
    return traceback.format_exc()

def send_to_antigravity(plugin_name, error_trace):
    """
    Sends a self-healing request to Antigravity's worker queue.
    Antigravity will write a new version of the plugin based on the error.
    """
    req = {
        "task": "fix_plugin",
        "tool_name": plugin_name,
        "error": error_trace
    }
    
    # Read existing requests
    data = []
    if os.path.exists(REQUEST_FILE):
        try:
            with open(REQUEST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
            
    data.append(req)
    
    with open(REQUEST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"[Debugger] Sent fix request to Antigravity for plugin '{plugin_name}'.")
