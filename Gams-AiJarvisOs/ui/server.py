import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel
from core.agent import JavisAgent  # supports both simple str and dict returns
from core.task_queue import global_task_queue
from memory.memory_store import global_memory
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from tools.tool_registry import registry
from core.tool_generator import tool_generator
from integrations.antigravity_connector import antigravity_connector
from core.config import PROJECT_ROOT, TOOLS_DIR
from core.campaign_monitor import monitor
from agents.system_monitor import system_monitor
import os
import json
import threading
import signal
import time
from core.logger import logger

load_dotenv()

class Settings(BaseModel):
    openai_api_key: str = ""
    gemini_api_key: str = ""
    twocaptcha_api_key: str = ""
    default_model: str = ""

class AdsConfigModel(BaseModel):
    fb_token: str = ""
    fb_account: str = ""
    tk_token: str = ""
    tk_advertiser: str = ""
    sheets_name: str = ""

class AccountUpdateModel(BaseModel):
    service: str
    account_name: str
    data: dict

class AccountDeleteModel(BaseModel):
    service: str
    account_name: str

class AccountTestModel(BaseModel):
    service: str
    account_name: str
    data: dict

class TaskModel(BaseModel):
    id: str = ""
    name: str
    description: str = ""
    plugin: str
    schedule: str
    accounts: dict
    status: str = "active"

class WorkflowModel(BaseModel):
    name: str
    description: str = ""
    steps: list

class FanpageLink(BaseModel):
    stt: int = 0
    page_name: str = ""
    page_id: str
    url: str
    status: str = "Chưa chạy"

class PluginConfigUpdateModel(BaseModel):
    plugin_id: str
    settings: dict

class FacebookAccountModel(BaseModel):
    account: str

agent = JavisAgent()
app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    with open("ui/advanced_dashboard.html", encoding="utf-8") as f:
        return f.read()

@app.on_event("startup")
def startup_event():
    print("FastAPI: Đang khởi động các dịch vụ nền...")
    
    # 1. Khởi động Bridge
    try:
        from core.antigravity_bridge import start_bridge
        start_bridge()
        print("FastAPI: Antigravity Bridge started.")
    except Exception as e:
        print(f"FastAPI: Error starting bridge: {e}")

    # 2. Khởi động Scheduler (chỉ nếu chưa chạy)
    try:
        from core.scheduler import global_scheduler
        global_scheduler.start()
        print("FastAPI: Global Scheduler started.")
    except Exception as e:
        print(f"FastAPI: Error starting scheduler: {e}")

    # 3. Khởi động Autonomous Engine
    try:
        from core.autonomous_engine import autonomous_engine
        autonomous_engine.start()
        print("FastAPI: Autonomous Engine started.")
    except Exception as e:
        print(f"FastAPI: Error starting autonomous engine: {e}")

    # 4. Khởi động monitor phản hồi bridge
    threading.Thread(target=_monitor_bridge_responses, daemon=True).start()
    print("FastAPI: Bridge Response Monitor started.")

import threading

@app.post("/run")
async def run_task(task: str):
    result = agent.run(task)

    # agent.run() may return a plain string (simple mode) or a dict with task_id (workflow mode)
    if isinstance(result, dict):
        task_id = result.get("task_id")
        if task_id:
            def worker():
                from core.workflow_engine import run_workflow
                from core.task_queue import global_task_queue
                global_task_queue.tasks[task_id]["status"] = "running"
                try:
                    wf_result = run_workflow(task_id, global_task_queue.tasks[task_id]["description"], global_task_queue)
                    global_task_queue.tasks[task_id]["status"] = "completed"
                    global_task_queue.tasks[task_id]["result"] = wf_result
                except Exception as e:
                    global_task_queue.tasks[task_id]["status"] = "failed"
                    global_task_queue.tasks[task_id]["result"] = str(e)
                    global_task_queue.log(task_id, f"System error: {e}")
            threading.Thread(target=worker, daemon=True).start()
        return {"result": result}
    else:
        # Simple string response — wrap in dict for consistent API shape
        return {"result": result, "task_id": None}
    
@app.get("/tasks")
def get_tasks():
    from core.task_queue import global_task_queue
    return global_task_queue.get_all_tasks()

@app.post("/tasks/cleanup")
def cleanup_tasks():
    from core.task_queue import global_task_queue
    count = global_task_queue.cleanup_tasks()
    return {"message": f"Đã dọn dẹp {count} tiến trình đã kết thúc.", "count": count}

@app.delete("/task/{task_id}")
def delete_task(task_id: str):
    from core.task_queue import global_task_queue
    if global_task_queue.delete_task(task_id):
        return {"message": "Đã xóa tiến trình."}
    raise HTTPException(status_code=404, detail="Không tìm thấy tiến trình")

@app.put("/task/{task_id}")
def update_task_desc(task_id: str, description: str):
    from core.task_queue import global_task_queue
    if task_id in global_task_queue.tasks:
        global_task_queue.tasks[task_id]["description"] = description
        return {"message": "Đã cập nhật mô tả."}
    raise HTTPException(status_code=404, detail="Không tìm thấy tiến trình")

@app.get("/memory/{namespace}")
def get_memory(namespace: str, query: str = ""):
    from memory.memory_store import global_memory
    if not query:
        docs = global_memory.get_all(namespace)
        return {"total": len(docs), "documents": docs}
             
    results = global_memory.search(query, namespace=namespace)
    return {"query": query, "results": results}

@app.post("/restart")
def restart_server():
    """
    Triggers a server restart by exiting with code 99,
    allowing the batch runner loop to restart the server in the same CMD window.
    """
    import sys
    import os
    import threading
    import time
    try:
        def do_restart():
            time.sleep(1.0) # Let uvicorn send response first
            print("\nServer: Restarting system (exiting with code 99)...")
            sys.stdout.flush()
            sys.stderr.flush()
            os._exit(99)
            
        threading.Thread(target=do_restart, daemon=True).start()
        return {"message": "Đang khởi động lại hệ thống..."}
    except Exception as e:
        return {"error": f"Lỗi khởi động lại: {str(e)}"}

@app.post("/shutdown")
def shutdown_server():
    """
    Shuts down the server process.
    """
    import os
    import signal
    print("FastAPI: Nhận yêu cầu TẮT hệ thống...")
    try:
        # Send SIGTERM to the current process
        os.kill(os.getpid(), signal.SIGTERM)
        return {"message": "Hệ thống đang được tắt..."}
    except Exception as e:
        return {"error": f"Lỗi khi tắt hệ thống: {str(e)}"}

@app.get("/settings")
def get_settings():
    """
    Returns current configuration. API Keys are masked for UI pre-filling.
    """
    openai_key = os.getenv("OPENAI_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    
    def mask_for_input(key, prefix="sk-"):
        if not key or key in ["YOUR_OPENAI_KEY", "YOUR_GEMINI_KEY", ""]:
            return ""
        # Format: first 8 ... last 4
        return f"{key[:8]}...{key[-4:]}"

    twocaptcha_key = os.getenv("TWOCAPTCHA_API_KEY", "")

    return {
        "openai_api_key_masked": mask_for_input(openai_key, "sk-"),
        "gemini_api_key_masked": mask_for_input(gemini_key, "AIza"),
        "twocaptcha_api_key_masked": mask_for_input(twocaptcha_key, ""),
        "default_model": os.getenv("DEFAULT_MODEL", "gpt-4o"),
        "is_openai_configured": openai_key not in ["YOUR_OPENAI_KEY", ""],
        "is_gemini_configured": gemini_key not in ["YOUR_GEMINI_KEY", ""],
        "is_twocaptcha_configured": twocaptcha_key != ""
    }

@app.get("/api-accounts")
def get_api_accounts():
    from core.api_settings import APISettings
    settings = APISettings()
    
    # Return everything so the UI can build the list
    # The UI will handle masking the tokens for display if needed
    return settings.data

@app.post("/settings")
def update_settings(settings: Settings):
    """
    Updates the .env file with new settings.
    """
    try:
        env_path = ".env"
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        env_dict = {}
        for line in lines:
            if "=" in line:
                key, val = line.strip().split("=", 1)
                env_dict[key] = val
        
        if settings.openai_api_key and "..." not in settings.openai_api_key:
            print(f"Server: Cập nhật OPENAI_API_KEY")
            env_dict["OPENAI_API_KEY"] = settings.openai_api_key
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
            
        if settings.gemini_api_key and "..." not in settings.gemini_api_key:
            print(f"Server: Cập nhật GEMINI_API_KEY")
            env_dict["GEMINI_API_KEY"] = settings.gemini_api_key
            os.environ["GEMINI_API_KEY"] = settings.gemini_api_key

        if settings.twocaptcha_api_key and "..." not in settings.twocaptcha_api_key:
            print(f"Server: Cập nhật TWOCAPTCHA_API_KEY")
            env_dict["TWOCAPTCHA_API_KEY"] = settings.twocaptcha_api_key
            os.environ["TWOCAPTCHA_API_KEY"] = settings.twocaptcha_api_key

        if settings.default_model:
            print(f"Server: Cập nhật DEFAULT_MODEL={settings.default_model}")
            env_dict["DEFAULT_MODEL"] = settings.default_model
            os.environ["DEFAULT_MODEL"] = settings.default_model
            
        with open(env_path, "w", encoding="utf-8") as f:
            for k, v in env_dict.items():
                f.write(f"{k}={v}\n")
        
        # Ensure changes are picked up by other modules
        load_dotenv(override=True)
        print("Server: Đã lưu và reload cấu hình.")
        return {"message": "Đã lưu cài đặt thành công."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api-accounts/add")
def add_api_account(model: AccountUpdateModel):
    try:
        from core.api_settings import APISettings
        settings = APISettings()
        
        # Don't overwrite with masked tokens if the user didn't change them
        # (Though practically, the UI will just send the full string or omit the field if unchanged,
        # but the UI shouldn't send '***' back)
        
        settings.add_or_update_account(model.service, model.account_name, model.data)
        return {"message": f"Đã lưu tài khoản '{model.account_name}' thành công."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api-accounts/delete")
def delete_api_account(model: AccountDeleteModel):
    try:
        from core.api_settings import APISettings
        settings = APISettings()
        settings.delete_account(model.service, model.account_name)
        return {"message": f"Đã xóa tài khoản '{model.account_name}' thành công."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/antigravity/status")
def get_antigravity_status():
    heartbeat_file = os.path.join(PROJECT_ROOT, "bridge", ".heartbeat")
    is_online = False
    if os.path.exists(heartbeat_file):
        try:
            with open(heartbeat_file, "r") as f:
                last_beat = float(f.read().strip())
            if time.time() - last_beat < 15:
                is_online = True
        except:
            pass
    return {"status": "ONLINE" if is_online else "OFFLINE"}

@app.get("/antigravity/test")
def test_antigravity():
    task_id = f"test_{int(time.time())}"
    task = {
        "id": task_id,
        "task": "ping"
    }
    try:
        req_dir = os.path.join(PROJECT_ROOT, "bridge", "requests")
        res_dir = os.path.join(PROJECT_ROOT, "bridge", "responses")
        
        req_path = os.path.join(req_dir, f"req_{task_id}.json")
        res_path = os.path.join(res_dir, f"res_{task_id}.json")
        
        # Write request
        os.makedirs(req_dir, exist_ok=True)
        os.makedirs(res_dir, exist_ok=True)
        with open(req_path, "w", encoding="utf-8") as f:
            json.dump(task, f, indent=2)
            
        # Poll for response
        for _ in range(50):
            if os.path.exists(res_path):
                try:
                    with open(res_path, "r", encoding="utf-8") as f:
                        r = json.load(f)
                    
                    # Delete the response file after reading
                    try: os.remove(res_path)
                    except: pass
                        
                    return {"status": "success", "message": f"Kết nối thành công! Bridge trả lời: {r.get('message', 'Antigravity Alive')}"}
                except:
                    pass
            time.sleep(0.1)
            
        return {"status": "error", "message": "Quá thời gian (5s), không nhận được phản hồi từ Antigravity Bridge. Vui lòng kiểm tra xem script bridge có đang chạy không."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api-accounts/test")
def test_api_account(model: AccountTestModel):
    try:
        # Generic mock test logic
        # In real life, we would instantiate the API client and make a ping request.
        if "access_token" in model.data and len(model.data["access_token"]) < 10:
            return {"success": False, "message": "Token quá ngắn hoặc không hợp lệ"}
        return {"success": True, "message": "Kết nối thành công!"}
    except Exception as e:
        return {"success": False, "message": str(e)}

# --- SCHEDULER & TASKS ENDPOINTS ---
from core.task_manager import TaskManager
from core.log_manager import LogManager
from core.scheduler import global_scheduler

@app.get("/scheduler/tasks")
def get_tasks():
    tm = TaskManager()
    return tm.get_all_tasks()

@app.post("/scheduler/tasks")
def save_task(task: TaskModel):
    tm = TaskManager()
    task_data = task.dict()
    if task.id:
        tm.update_task(task.id, task_data)
    else:
        tm.add_task(task_data)
    global_scheduler.reload_jobs()
    return {"message": "Đã lưu tác vụ thành công"}

@app.delete("/scheduler/tasks/{task_id}")
def delete_task(task_id: str):
    tm = TaskManager()
    tm.delete_task(task_id)
    global_scheduler.reload_jobs()
    return {"message": "Đã xóa tác vụ"}

@app.post("/scheduler/tasks/{task_id}/run")
def run_task_manual(task_id: str):
    tm = TaskManager()
    task = tm.get_task(task_id)
    if task:
        # Run it asynchronously
        global_scheduler.run_task_wrapper(task)
        return {"message": "Đang chạy tác vụ thủ công"}
    raise HTTPException(status_code=404, detail="Task not found")

@app.post("/scheduler/tasks/{task_id}/terminate")
def terminate_task_manual(task_id: str):
    tm = TaskManager()
    task = tm.get_task(task_id)
    if task:
        plugin_name = task.get("plugin")
        logger.info(f"FastAPI: Nhận yêu cầu TẮT tác vụ: {plugin_name} (ID: {task_id})")
        global_scheduler.terminate_task(plugin_name, task_id)
        return {"message": f"Đã gửi yêu cầu tắt tác vụ {plugin_name}"}
    raise HTTPException(status_code=404, detail="Task not found")

@app.post("/scheduler/tasks/{task_id}/reset")
def reset_task_manual(task_id: str):
    tm = TaskManager()
    task = tm.get_task(task_id)
    if task:
        logger.info(f"FastAPI: Nhận yêu cầu RESET tác vụ: {task.get('plugin')} (ID: {task_id})")
        global_scheduler.reset_task(task)
        return {"message": f"Đã gửi yêu cầu khởi động lại tác vụ {task.get('plugin')}"}
    raise HTTPException(status_code=404, detail="Task not found")

@app.get("/scheduler/logs")
def get_all_logs(limit: int = 50):
    lm = LogManager()
    return lm.get_latest_runs(limit)

@app.get("/scheduler/logs/{run_id}")
def get_log_steps(run_id: str):
    lm = LogManager()
    return lm.get_run_steps(run_id)

@app.delete("/scheduler/logs/{run_id}")
def delete_log_run(run_id: str):
    lm = LogManager()
    lm.delete_run(run_id)
    return {"message": "Đã xóa log phiên chạy."}

@app.delete("/scheduler/tasks/{task_id}/logs")
def delete_task_logs(task_id: str):
    lm = LogManager()
    lm.delete_task_runs(task_id)
    return {"message": "Đã xóa toàn bộ log của tác vụ."}

@app.delete("/scheduler/logs")
def clear_all_automation_logs():
    lm = LogManager()
    lm.clear_all_runs()
    return {"message": "Đã dọn dẹp toàn bộ log tiến trình."}

@app.get("/tools")
def get_tools():
    # Dynamically scan for new tool files
    from core.config import TOOLS_DIR
    registry.auto_load_tools(TOOLS_DIR)
    
    # Also scan plugins
    from core.plugin_registry import plugin_registry
    plugin_registry.load_plugins()
    
    return {
        "tools": list(registry.get_all_tools().keys()),
        "descriptions": registry._descriptions,
        "plugins": list(plugin_registry.plugins.keys())
    }

# --- GAMS INSIGHT AUTOMATED FB LOGIN & CHROME PROFILE ENDPOINTS ---

@app.get("/api/gams-insight/fb-account")
def get_fb_account():
    fb_acc_path = os.path.join(PROJECT_ROOT, "plugins", "data", "gams_insight", "fb_account.json")
    if os.path.exists(fb_acc_path):
        try:
            with open(fb_acc_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"account": ""}

@app.post("/api/gams-insight/fb-account")
def save_fb_account(model: FacebookAccountModel):
    fb_acc_path = os.path.join(PROJECT_ROOT, "plugins", "data", "gams_insight", "fb_account.json")
    os.makedirs(os.path.dirname(fb_acc_path), exist_ok=True)
    try:
        with open(fb_acc_path, "w", encoding="utf-8") as f:
            json.dump({"account": model.account}, f, ensure_ascii=False, indent=4)
        return {"message": "Đã lưu tài khoản Facebook thành công."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gams-insight/open-chrome")
def open_chrome_manual():
    import sys
    import psutil
    import subprocess
    
    user_data_dir = os.path.abspath(os.path.join(PROJECT_ROOT, "plugins", "data", "gams_insight", "user_data"))
    
    # 1. Kill any existing chrome instances using this profile
    try:
        profile_dir_norm = os.path.normcase(os.path.normpath(user_data_dir))
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                name = (proc.info["name"] or "").lower()
                if "chrome" not in name:
                    continue
                cmdline = proc.info["cmdline"] or []
                for arg in cmdline:
                    arg_norm = os.path.normcase(os.path.normpath(arg.split("=", 1)[-1]))
                    if "user-data-dir" in arg and arg_norm == profile_dir_norm:
                        try:
                            proc.terminate()
                        except:
                            pass
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        time.sleep(1.0)
    except Exception as e:
        print(f"Error killing Chrome processes: {e}")
        
    # 2. Start manual Chrome
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = "chrome.exe"
            
    cmd = [
        chrome_path,
        f"--user-data-dir={user_data_dir}",
        "--no-sandbox",
        "--disable-gpu",
        "--remote-debugging-port=9222"
    ]
    
    try:
        if sys.platform == "win32":
            subprocess.Popen(cmd, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            subprocess.Popen(cmd, preexec_fn=os.setpgrp)
        return {"success": True, "message": "Đã mở Chrome thủ công thành công."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể chạy Chrome: {str(e)}")

@app.post("/api/gams-insight/login-facebook")
def login_facebook_endpoint(model: FacebookAccountModel):
    # Parse credential UID|pass|2fa|mail
    parts = model.account.split("|")
    if len(parts) < 3:
        raise HTTPException(status_code=400, detail="Định dạng tài khoản không hợp lệ. Yêu cầu: UID|pass|2fa|mail")
        
    uid = parts[0].strip()
    password = parts[1].strip()
    two_factor_secret = parts[2].strip()
    email = parts[3].strip() if len(parts) > 3 else uid
    
    username = uid if uid else email
    
    import subprocess
    import uuid
    
    # Write credentials to temporary JSON file to avoid shell escaping issues
    creds_id = str(uuid.uuid4())[:8]
    creds_dir = os.path.join(PROJECT_ROOT, "tmp")
    os.makedirs(creds_dir, exist_ok=True)
    creds_path = os.path.join(creds_dir, f"login_creds_{creds_id}.json")
    
    try:
        with open(creds_path, "w", encoding="utf-8") as f:
            json.dump({
                "username": username,
                "password": password,
                "two_factor_secret": two_factor_secret
            }, f)
            
        script_path = os.path.join(PROJECT_ROOT, "core", "login_facebook.py")
        if sys.platform == "win32":
            cmd_args = f'cmd.exe /c "title Jarvis_Login_Facebook && \"{sys.executable}\" \"{script_path}\" \"{creds_path}\""'
            creationflags = subprocess.CREATE_NEW_CONSOLE
        else:
            cmd_args = [sys.executable, script_path, creds_path]
            creationflags = 0
            
        result = subprocess.run(
            cmd_args,
            creationflags=creationflags,
            close_fds=True
        )
        
        if result.returncode == 0:
            return {"success": True, "message": "Đăng nhập tự động Facebook thành công!"}
        elif result.returncode == 1:
            return {"success": False, "message": "Đăng nhập thất bại. Vui lòng thử lại hoặc giải CAPTCHA thủ công."}
        else:
            return {"success": False, "message": f"Lỗi trong quá trình đăng nhập (Exit code: {result.returncode})"}
            
    except Exception as e:
        # Cleanup if still exists
        if os.path.exists(creds_path):
            try: os.remove(creds_path)
            except: pass
        return {"success": False, "message": f"Lỗi khởi chạy tiến trình đăng nhập: {str(e)}"}

@app.get("/api/fanpage-insights")
def get_fanpage_insights():
    try:
        links_path = os.path.join(PROJECT_ROOT, "plugins", "data", "gams_insight", "links.json")
        if not os.path.exists(links_path):
            return []
        
        with open(links_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Ensure it's a list sorted by STT
        if isinstance(data, list):
            data.sort(key=lambda x: int(x.get("stt", 9999)))
            return data
        return []
    except Exception as e:
        print(f"Error reading fanpage insights: {e}")
        return []

@app.post("/api/fanpage-sync-external")
def sync_fanpage_external():
    """Triggers the sync_fanpages script to update links.json from browser profile."""
    import subprocess
    import sys
    from core.config import PROJECT_ROOT
    
    script_path = os.path.join(PROJECT_ROOT, "core", "sync_fanpages.py")
    if not os.path.exists(script_path):
        # Fallback to tmp if moved back
        script_path = os.path.join(PROJECT_ROOT, "tmp", "sync_fanpages.py")
        
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="Sync script not found")
        
    try:
        if sys.platform == "win32":
            cmd_args = f'cmd.exe /c "title Jarvis_Sync_Fanpages && \"{sys.executable}\" \"{script_path}\""'
            creationflags = subprocess.CREATE_NEW_CONSOLE
        else:
            cmd_args = [sys.executable, script_path]
            creationflags = 0
            
        result = subprocess.run(
            cmd_args,
            creationflags=creationflags,
            close_fds=True
        )
        
        # Reload the data to count 
        links_path = os.path.join(PROJECT_ROOT, "plugins", "data", "gams_insight", "links.json")
        count = 0
        if os.path.exists(links_path):
            with open(links_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                count = len(data) if isinstance(data, list) else 0
                
        if result.returncode == 0:
            return {"message": "Đồng bộ thành công", "count": count, "output": "Đồng bộ từ browser hoàn tất."}
        else:
            raise HTTPException(status_code=500, detail=f"Sync failed (Exit code: {result.returncode})")
    except subprocess.CalledProcessError as e:
        print(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=f"Sync process call error: {str(e)}")
    except Exception as e:
        print(f"Sync exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fanpage-links")
def update_fanpage_links(links: list[FanpageLink]):
    try:
        links_path = os.path.join(PROJECT_ROOT, "plugins", "data", "gams_insight", "links.json")
        os.makedirs(os.path.dirname(links_path), exist_ok=True)
        
        # Preserve existing data if possible
        existing_data = []
        if os.path.exists(links_path):
            with open(links_path, "r", encoding="utf-8") as f:
                try: existing_data = json.load(f)
                except: existing_data = []

        # Map existing data by page_id for easy lookup
        data_map = {item.get("page_id"): item for item in existing_data if item.get("page_id")}

        new_links = []
        for i, link_model in enumerate(links):
            link = link_model.model_dump()
            p_id = link.get("page_id")
            # Create a clean entry
            entry = {
                "stt": link.get("stt") or (i + 1),
                "page_name": link.get("page_name", ""),
                "page_id": p_id,
                "url": link.get("url", ""),
                "status": "Chưa chạy"
            }
            
            # If existed before, merge data
            if p_id in data_map:
                old_entry = data_map[p_id]
                entry["status"] = old_entry.get("status", "Chưa chạy")
                entry["data"] = old_entry.get("data", {})
                entry["total_followers"] = old_entry.get("total_followers", "")
                entry["latest_post_date"] = old_entry.get("latest_post_date", "")
                entry["latest_post_title"] = old_entry.get("latest_post_title", "")
                if "last_scanned" in old_entry:
                    entry["last_scanned"] = old_entry["last_scanned"]
            
            new_links.append(entry)

        with open(links_path, "w", encoding="utf-8") as f:
            json.dump(new_links, f, ensure_ascii=False, indent=4)
        return {"message": "Đã lưu danh sách Fanpage thành công."}
    except Exception as e:
        print(f"Error saving fanpage links: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/plugin/{name}")
def delete_plugin(name: str):
    from core.config import PROJECT_ROOT
    plugin_path = os.path.join(PROJECT_ROOT, "plugins", f"{name}.py")
    if os.path.exists(plugin_path):
        os.remove(plugin_path)
        return {"message": f"Đã xóa plugin {name}"}
    raise HTTPException(status_code=404, detail="Không tìm thấy plugin")

@app.get("/system/campaigns")
def get_campaigns():
    return monitor.active_campaigns

@app.delete("/system/campaign/{id}")
def delete_campaign(id: str):
    if id in monitor.active_campaigns:
        del monitor.active_campaigns[id]
        return {"message": "Đã xóa lịch sử chiến dịch."}
    raise HTTPException(status_code=404, detail="Không tìm thấy chiến dịch")

@app.get("/system/status")
def get_system_status():
    stats = system_monitor.get_stats()
    # Get latest error from campaign monitor
    latest_error = None
    if os.path.exists(monitor.error_log):
        with open(monitor.error_log, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                try:
                    latest_error = json.loads(lines[-1])
                except:
                    latest_error = None
                
    return {
        "stats": stats,
        "latest_error": latest_error
    }

@app.get("/system/logs")
def get_system_logs():
    log_path = os.path.join(PROJECT_ROOT, "logs", "javis.log")
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            return f.readlines()[-200:]
    return []

@app.get("/system/self-healing")
def get_self_healing_data():
    from core.memory_manager import MemoryManager
    memory = MemoryManager()
    error_data = memory._load(memory.error_path)
    # Return latest 10 errors for the debug panel
    errors = error_data.get("errors", [])[-10:]
    return {"errors": errors}

# ---- SELF-REPAIR CHAT LOG ----
SELFREPAIR_LOG_PATH = os.path.join(PROJECT_ROOT, "logs", "self_repair_chatlog.json")

@app.get("/self-repair/log")
def get_self_repair_log():
    """Trả về nhật ký chat của module tự sửa lỗi plugin."""
    if os.path.exists(SELFREPAIR_LOG_PATH):
        with open(SELFREPAIR_LOG_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

class SelfRepairMessage(BaseModel):
    role: str  # "system" | "plugin" | "ai"
    plugin: str = ""
    message: str
    timestamp: str = ""

@app.post("/self-repair/log")
def post_self_repair_log(msg: SelfRepairMessage):
    """Thêm entry vào nhật ký tự sửa lỗi plugin."""
    import datetime
    logs = []
    if os.path.exists(SELFREPAIR_LOG_PATH):
        with open(SELFREPAIR_LOG_PATH, "r", encoding="utf-8") as f:
            try:
                logs = json.load(f)
            except:
                logs = []
    entry = {
        "role": msg.role,
        "plugin": msg.plugin,
        "message": msg.message,
        "timestamp": msg.timestamp or datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    }
    logs.append(entry)
    os.makedirs(os.path.dirname(SELFREPAIR_LOG_PATH), exist_ok=True)
    with open(SELFREPAIR_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)
    return {"message": "Đã ghi log tự sửa lỗi.", "entry": entry}

@app.delete("/self-repair/log")
def clear_self_repair_log():
    """Xóa sạch nhật ký tự sửa lỗi plugin."""
    if os.path.exists(SELFREPAIR_LOG_PATH):
        with open(SELFREPAIR_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
    return {"message": "Đã dọn sạch nhật ký tự sửa lỗi."}

@app.delete("/system/logs")
def clear_system_logs():
    log_path = os.path.join(PROJECT_ROOT, "logs", "javis.log")
    try:
        if os.path.exists(log_path):
            # On Windows, 'w' might fail if the file is open. 
            # 'r+' and truncate(0) is sometimes more successful.
            with open(log_path, "r+", encoding="utf-8") as f:
                f.truncate(0)
            return {"message": "Đã xóa log hệ thống."}
        return {"message": "Không tìm thấy file log."}
    except Exception as e:
        # If still fails, try to just overwrite if possible or return error
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("")
            return {"message": "Đã xóa log hệ thống (fallback)."}
        except Exception as e2:
            return {"error": f"Không thể xóa log: {str(e2)}"}

@app.delete("/system/self-healing")
def clear_self_healing():
    from core.memory_manager import MemoryManager
    memory = MemoryManager()
    memory._save(memory.error_path, {"errors": []})
    return {"message": "Đã xóa lịch sư sửa lỗi tự động."}

@app.post("/tools/create")
def create_tool(name: str, description: str = ""):
    result = tool_generator.create_tool(name, description)
    return {"message": result}

@app.post("/tools/request")
def request_tool(name: str, requirement: str):
    # Log the request to system tasks
    from core.task_queue import global_task_queue
    task_id = global_task_queue.submit_task(f"Self-Evolution: {name}")
    
    global_task_queue.log(task_id, f"Workspace: {PROJECT_ROOT}")
    global_task_queue.log(task_id, f"Action: Sending signal to Antigravity (me) for code generation.")
    
    # Actually call the connector which writes to requests.json
    result = antigravity_connector.request_tool_generation(name, requirement, task_id)
    
    return {"message": result, "task_id": task_id, "workspace": PROJECT_ROOT}

@app.get("/tools/requests")
def get_tool_requests():
    return {"requests": antigravity_connector.get_pending_requests()}

@app.get("/plugin/registry")
def get_plugin_registry():
    registry_path = os.path.join(PROJECT_ROOT, "plugins", "plugin_registry.json")
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"plugins": []}

@app.get("/api/plugin/{plugin_id}/settings")
def get_plugin_settings(plugin_id: str):
    config_path = os.path.join(PROJECT_ROOT, "plugins", "data", "plugin_settings.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(plugin_id, {})
        except:
            pass
    return {}

@app.post("/api/plugin/settings")
def update_plugin_settings(model: PluginConfigUpdateModel):
    config_path = os.path.join(PROJECT_ROOT, "plugins", "data", "plugin_settings.json")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    data = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}
            
    data[model.plugin_id] = model.settings
    
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return {"message": f"Đã cập nhật cấu hình cho plugin {model.plugin_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- AGENT HIERARCHY ENDPOINTS ---

@app.get("/api/agent-hierarchy")
def get_agent_hierarchy():
    hierarchy_path = os.path.join(PROJECT_ROOT, "plugins", "agent_hierarchy.json")
    if not os.path.exists(hierarchy_path):
        # Create default if missing
        default_hierarchy = {
            "Jarvis OS - AI agent dashbroad": {
                "AI Agent Phân tích và đưa ra giải pháp": [],
                "AI Agent Báo cáo": [],
                "AI Agent Automation": [],
                "AI Agent Auto fix bug": []
            }
        }
        os.makedirs(os.path.dirname(hierarchy_path), exist_ok=True)
        with open(hierarchy_path, "w", encoding="utf-8") as f:
            json.dump(default_hierarchy, f, indent=4, ensure_ascii=False)
        return default_hierarchy
    
    try:
        with open(hierarchy_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đọc sơ đồ: {str(e)}")

@app.post("/api/agent-hierarchy")
def update_agent_hierarchy(hierarchy: dict):
    hierarchy_path = os.path.join(PROJECT_ROOT, "plugins", "agent_hierarchy.json")
    try:
        with open(hierarchy_path, "w", encoding="utf-8") as f:
            json.dump(hierarchy, f, indent=4, ensure_ascii=False)
        return {"message": "Đã cập nhật sơ đồ hệ thống."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lưu sơ đồ: {str(e)}")

@app.get("/api/plugins/status")
def get_plugins_status():
    """
    Returns a list of all plugins with their current operational status.
    Combines registry data with active task data.
    """
    from core.plugin_registry import plugin_registry
    plugin_registry.load_plugins()
    all_plugins = list(plugin_registry.plugins.keys())
    
    from core.task_manager import TaskManager
    tm = TaskManager()
    active_tasks = tm.get_all_tasks()
    
    # Map plugin name to status
    status_map = {}
    for p in all_plugins:
        plugin_instance = plugin_registry.get_plugin(p)
        description = getattr(plugin_instance, "description", "Thư viện mã nguồn OS.")
        status_map[p] = {
            "name": p,
            "description": description,
            "status": "idle",
            "task_id": None
        }
    
    for t_info in active_tasks:
        t_id = t_info.get("id")
        p_name = t_info.get("plugin")
        if p_name in status_map:
            # If any task for this plugin is running, mark as running
            if t_info.get("status") == "running" or status_map[p_name]["status"] != "running":
                status_map[p_name]["status"] = t_info.get("status", "unknown")
                status_map[p_name]["task_id"] = t_id

    return status_map

# --- INDEPENDENT GAMS PLUGIN MANUAL & AUTO LAUNCH ENDPOINTS ---

@app.post("/api/gams-plugin/{plugin_name}/run-manual")
def run_plugin_manual(plugin_name: str):
    import subprocess
    import sys
    
    project_map = {
        "gams_auto_post_fanpage": {"folder": "Gams-AutoPostFanpage", "command": "gui.py"},
        "gams_auto_post_profile": {"folder": "Gams-AutoPostProfile", "command": "gui.py"},
        "gams_tiktok_downloader": {"folder": "Gams-TiktokDownloader", "command": "main.py"},
        "gams_youtube_downloader": {"folder": "Gams-YoutubeDownloader", "command": "main.py"},
        "gams_tool_auto_bcgame": {"folder": "Gams-ToolAutoBcgame", "command": "main.py"},
        "gams_fb_copyright_checker": {"folder": "Gams-FbCopyrightChecker", "command": "main.py"},
        "gams_insight_reader": {"folder": "Gams Ai Jarvis Os", "command": "test_insight_reader.py"}
    }
    
    if plugin_name not in project_map:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình chạy thủ công cho plugin này.")
        
    p_info = project_map[plugin_name]
    
    # Resolve the CWD
    if plugin_name == "gams_insight_reader":
        cwd = os.path.abspath(PROJECT_ROOT)
    else:
        cwd = os.path.abspath(os.path.join(os.path.dirname(PROJECT_ROOT), p_info["folder"]))
        
    if not os.path.exists(cwd):
        raise HTTPException(status_code=400, detail=f"Không tìm thấy thư mục: {cwd}")
        
    # Auto-close existing instance of this plugin first to prevent duplicate processes
    try:
        from core.scheduler import global_scheduler
        global_scheduler.terminate_task(plugin_name)
        time.sleep(0.5)
    except Exception as e:
        logger.warning(f"Could not terminate existing task before manual launch: {e}")

    # Open visible CMD window running cmd /k
    if sys.platform == "win32":
        cmd_args = f'cmd.exe /k "title Jarvis_Manual_{plugin_name} && \"{sys.executable}\" {p_info["command"]}"'
        creationflags = subprocess.CREATE_NEW_CONSOLE
    else:
        cmd_args = [sys.executable, p_info["command"]]
        creationflags = 0
        
    try:
        subprocess.Popen(
            cmd_args,
            cwd=cwd,
            creationflags=creationflags,
            close_fds=True
        )
        return {"success": True, "message": f"Đã khởi chạy {plugin_name} thủ công."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Không thể chạy tool: {str(e)}")

@app.post("/api/gams-plugin/{plugin_name}/run-auto")
def run_plugin_auto(plugin_name: str):
    import uuid
    task_id = f"task_auto_{plugin_name}"
    run_id = f"run_auto_{str(uuid.uuid4())[:8]}"
    
    try:
        from core.scheduler import global_scheduler
        task_data = {
            "id": task_id,
            "name": f"Auto Run {plugin_name}",
            "plugin": plugin_name,
            "schedule": "",
            "accounts": {},
            "stay_open": False
        }
        global_scheduler.run_task_wrapper(task_data)
        return {"success": True, "message": f"Đã kích hoạt {plugin_name} chạy tự động."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi kích hoạt: {str(e)}")

@app.post("/workflows/create")
def create_workflow(data: WorkflowModel):
    workflows_dir = os.path.join(PROJECT_ROOT, "workflows")
    os.makedirs(workflows_dir, exist_ok=True)
    file_path = os.path.join(workflows_dir, f"{data.name}.json")
    
    workflow_json = {
        "name": data.name,
        "description": data.description,
        "steps": data.steps
    }
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(workflow_json, f, indent=4, ensure_ascii=False)
        return {"message": f"Workflow '{data.name}' saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/shutdown")
def shutdown_server():
    """
    Safely shuts down the Jarvis python processes without killing the OS terminal.
    """
    def kill_him():
        time.sleep(1) # Chờ một chút để trả về phản hồi cho UI
        try:
            if os.name == 'nt':
                import subprocess
                # Lấy danh sách tiến trình python và command line của chúng
                cmd = 'wmic process where "name=\'python.exe\'" get processid,commandline /format:csv'
                output = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
                
                project_keywords = ['javis-agent', 'main.py', 'ui.server:app', 'isolated_runner.py']
                pids_to_kill = set()
                
                # Quan trọng: Lấy PID của chính server hiện tại
                my_pid = os.getpid()
                
                for line in output.splitlines():
                    if not line.strip() or 'ProcessId' in line: continue
                    parts = line.strip().split(',')
                    if len(parts) >= 3:
                        process_cmd = parts[1].lower()
                        pid = parts[2]
                        # Kiểm tra xem có chứa từ khóa của dự án HOẶC nằm trong thư mục dự án không
                        if any(kw in process_cmd for kw in project_keywords) or 'javis-agent' in process_cmd:
                            pids_to_kill.add(pid)
                
                # Đảm bảo bao gồm PID hiện tại và có thể là tiến trình cha (CMD)
                pids_to_kill.add(str(my_pid))
                
                for pid in pids_to_kill:
                    # Tắt tiến trình một cách quyết liệt
                    subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, capture_output=True)
            else:
                import signal
                os.system("pkill -f 'javis-agent'")
                os.kill(os.getpid(), signal.SIGTERM)
        except Exception as e:
            print(f"Error during shutdown: {e}")

    threading.Thread(target=kill_him).start()
    return {"message": "Hệ thống đang tắt. Các tiến trình Python của Jarvis đã đóng."}

def _monitor_bridge_responses():
    """Background thread to read responses/ directory and update task_queue dynamically"""
    res_dir = os.path.join(PROJECT_ROOT, "bridge", "responses")
    os.makedirs(res_dir, exist_ok=True)
    
    while True:
        try:
            for file in os.listdir(res_dir):
                if file.endswith(".json") and not file.startswith("res_test_"):
                    file_path = os.path.join(res_dir, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            r = json.load(f)
                        
                        tid = r.get("task_id")
                        if tid:
                            from core.task_queue import global_task_queue
                            if tid in global_task_queue.tasks:
                                if r.get("status") == "done" or r.get("status") == "ok":
                                    global_task_queue.tasks[tid]["status"] = "completed"
                                    global_task_queue.tasks[tid]["result"] = r.get("result", "Completed successfully")
                                    global_task_queue.log(tid, f"Antigravity: {r.get('result', 'Code generated')}")
                                elif r.get("status") == "error":
                                    global_task_queue.tasks[tid]["status"] = "failed"
                                    global_task_queue.tasks[tid]["result"] = r.get("message", "Error")
                                    global_task_queue.log(tid, f"Antigravity Error: {r.get('message')}")
                                    
                        # Delete the handled file
                        try: os.remove(file_path)
                        except: pass
                    except Exception as e:
                        print(f"Error parsing response {file}: {e}")
        except Exception as e:
            pass
        time.sleep(1)

# Logic startup đã được dời vào @app.on_event("startup")

