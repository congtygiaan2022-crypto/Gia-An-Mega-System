import json
import time
import os
import threading
from core.config import TOOLS_DIR, PROJECT_ROOT
from core.tool_generator import tool_generator

REQUEST_FILE = os.path.join(PROJECT_ROOT, "requests.json")

RESPONSE_FILE = os.path.join(PROJECT_ROOT, "responses.json")

def process_request(req):
    task_type = req.get('task')
    tool_name = req.get('tool_name')
    print(f"[Antigravity Worker] Processing: {task_type} for {tool_name}")
    
    if not tool_name:
        return {"status": "error", "message": "Missing tool_name"}
        
    try:
        if task_type == "fix_plugin":
            error_trace = req.get('error', '')
            print(f"[Antigravity Worker] Initiating self-healing protocol on {tool_name}")
            # Ask the generator to FIX the code rather than generate from scratch
            prompt = f"Fix the following python plugin '{tool_name}' which crashed with the stacktrace:\n{error_trace}\nYour output should overwrite the existing file entirely with the fixed version."
            tool_code = tool_generator.generate_tool(tool_name, prompt)
        else:
            # Generate the tool normally
            tool_code = tool_generator.generate_tool(tool_name, task_type)
        
        path = os.path.join(TOOLS_DIR, f"{tool_name}.py")
        print(f"[Antigravity Worker] Generating Tool: {path}")
        return {"status": "success", "plugin": tool_name}
        
    except Exception as e:
        print(f"[Antigravity Worker] Error generating tool {tool_name}: {e}")
        return {"status": "error", "plugin": tool_name, "message": str(e)}

def watch_requests():
    print("[Antigravity Worker] Started watching for Self-Developer requests...")
    while True:
        if os.path.exists(REQUEST_FILE):
            try:
                with open(REQUEST_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                results = []
                for req in data:
                    res = process_request(req)
                    if res:
                        results.append(res)
                        
                with open(RESPONSE_FILE, "w", encoding="utf-8") as f:
                    json.dump(results, f)
                    
                os.remove(REQUEST_FILE)
            except Exception as e:
                print(f"[Antigravity Worker] Failed to read requests.json: {e}")
                time.sleep(2)
                
        # Update heartbeat for health-checking
        with open(os.path.join(PROJECT_ROOT, ".antigravity_heartbeat"), "w") as f:
            f.write(str(time.time()))
            
        time.sleep(2)

def start_worker():
    thread = threading.Thread(target=watch_requests, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    watch_requests()
