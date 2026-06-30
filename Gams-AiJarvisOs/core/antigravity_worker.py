import json
import time
import os
import threading
from dotenv import load_dotenv
load_dotenv()
from core.config import PLUGINS_DIR, PROJECT_ROOT
from core.tool_generator import tool_generator
from core.antigravity_bridge import generate_code_via_llm, extract_python_code

REQUEST_FILE = os.path.join(PROJECT_ROOT, "requests.json")

RESPONSE_FILE = os.path.join(PROJECT_ROOT, "responses.json")

def process_request(req):
    task_type = req.get('task')
    tool_name = req.get('tool_name') or req.get('name')
    print(f"[Antigravity Worker] Processing: {task_type} for {tool_name}")
    
    if not tool_name:
        return {"status": "error", "message": "Missing tool_name"}
        
    try:
        plugin_path = os.path.join(PLUGINS_DIR, f"{tool_name}.py")
        
        if task_type == "fix_plugin":
            error_trace = req.get('error', '')
            print(f"[Antigravity Worker] Initiating self-healing protocol on {tool_name}")
            
            # Read original code
            original_code = ""
            if os.path.exists(plugin_path):
                try:
                    with open(plugin_path, "r", encoding="utf-8") as f:
                        original_code = f.read()
                except Exception as read_err:
                    print(f"[Antigravity Worker] Warning: Could not read original code: {read_err}")
            
            prompt = f"""
You are Antigravity, an expert AI developer agent.
You are tasked with fixing a bug in the Python plugin '{tool_name}.py'.

Here is the original source code of the plugin:
```python
{original_code}
```

Here is the error traceback and log details:
{error_trace}

Please analyze the error and output the entire corrected python code.
Your output must contain only the valid python code inside a single ```python ``` code block. Do not write any other explanation or text outside the code block.
"""
            llm_response = generate_code_via_llm(prompt)
            if not llm_response:
                raise Exception("LLM returned empty response or API call failed.")
                
            code = extract_python_code(llm_response)
            if not code:
                raise Exception("Failed to extract python code from LLM response.")
                
        else: # tool_generation or other
            print(f"[Antigravity Worker] Generating new plugin: {tool_name}")
            requirement = req.get('requirement', task_type)
            prompt = f"""
You are Antigravity, an expert AI developer agent.
You are tasked with generating a Python plugin '{tool_name}.py' based on the following requirement:
{requirement}

Requirements for the plugin:
- It must have a `Plugin` class or a top-level `run` function.
- If it uses a `Plugin` class, it must have an `__init__(self)` initializing `self.name` and `self.description` and a `run(self, **kwargs)` method returning a dict with "status": "success"/"error".
- Ensure clean code, appropriate logging (using core.logger.get_module_logger), and error handling.
- Output the entire python code inside a single ```python ``` code block. Do not write any other explanation or text outside the code block.
"""
            llm_response = generate_code_via_llm(prompt)
            if not llm_response:
                raise Exception("LLM returned empty response or API call failed.")
                
            code = extract_python_code(llm_response)
            if not code:
                raise Exception("Failed to extract python code from LLM response.")
        
        # Backup the original file
        if os.path.exists(plugin_path):
            backup_path = plugin_path + ".bak"
            try:
                import shutil
                shutil.copy2(plugin_path, backup_path)
                print(f"[Antigravity Worker] Created backup of {tool_name}.py at {backup_path}")
            except Exception as backup_err:
                print(f"[Antigravity Worker] Failed to create backup: {backup_err}")
                
        os.makedirs(PLUGINS_DIR, exist_ok=True)
        with open(plugin_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        print(f"[Antigravity Worker] Successfully wrote plugin: {plugin_path}")
        tool_generator._update_registry(tool_name)
        return {"status": "success", "plugin": tool_name}
        
    except Exception as e:
        print(f"[Antigravity Worker] Error processing request for {tool_name}: {e}")
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
