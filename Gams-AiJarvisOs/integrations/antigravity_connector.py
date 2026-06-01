import os
import json
from datetime import datetime
from core.logger import get_module_logger
from core.config import PROJECT_ROOT

logger = get_module_logger("AntigravityConnector")

class AntigravityConnector:
    def __init__(self):
        self.bridge_dir = os.path.join(PROJECT_ROOT, "bridge")
        self.requests_dir = os.path.join(self.bridge_dir, "requests")
        self.responses_dir = os.path.join(self.bridge_dir, "responses")
        
        os.makedirs(self.requests_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)

    def request_tool_generation(self, tool_name: str, requirement: str, task_id: str = None):
        """
        Signals Antigravity to generate a tool by writing to a shared artifact file.
        """
        request_id = task_id if task_id else datetime.now().strftime("%Y%m%d_%H%M%S")
        request = {
            "id": request_id,
            "task": "tool_generation",
            "name": tool_name,
            "requirement": requirement,
            "status": "pending",
            "workspace": os.getcwd(),
            "timestamp": datetime.now().isoformat()
        }
        
        req_file = os.path.join(self.requests_dir, f"req_{request_id}.json")
        with open(req_file, 'w', encoding='utf-8') as f:
            json.dump(request, f, indent=4, ensure_ascii=False)
        
        # Log for immediate visibility
        logger.info(f"Request logged to Artifact Bridge: {tool_name} at {req_file}")
        
        if task_id:
            from core.task_queue import global_task_queue
            global_task_queue.log(task_id, f"Bridge: Yêu cầu đã nhảy vào Event Queue ({req_file})")
            global_task_queue.log(task_id, f"Trạng thái: Đang chờ Antigravity (me) phát triển mã nguồn.")

        return "Yêu cầu đã được đẩy vào Event Queue thực tế. Antigravity sẽ bắt đầu xử lý ngay lập tức."

    def get_pending_requests(self):
        # Reads all files in requests_dir
        pending = []
        if os.path.exists(self.requests_dir):
            for file in os.listdir(self.requests_dir):
                if file.endswith(".json"):
                    try:
                        with open(os.path.join(self.requests_dir, file), 'r', encoding='utf-8') as f:
                            pending.append(json.load(f))
                    except: pass
        return pending

    def check_request_completion(self, name):
        """Checks if a specific tool generation request is completed by looking in responses_dir."""
        if os.path.exists(self.responses_dir):
            for file in os.listdir(self.responses_dir):
                if file.endswith(".json"):
                    try:
                        with open(os.path.join(self.responses_dir, file), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if data.get("name") == name and data.get("status") in ("completed", "done"):
                                return True
                    except: pass
        return False

# Global instance
antigravity_connector = AntigravityConnector()
