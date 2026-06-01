import os
import json
import time
from core.logger import get_module_logger
from core.config import PROJECT_ROOT
from database.redis_connector import redis_connector

logger = get_module_logger("FixEngine")

class FixEngine:
    def __init__(self):
        self.redis = redis_connector
        self.request_dir = os.path.join(PROJECT_ROOT, "bridge", "requests")
        self.response_dir = os.path.join(PROJECT_ROOT, "bridge", "responses")
        os.makedirs(self.request_dir, exist_ok=True)
        os.makedirs(self.response_dir, exist_ok=True)

    def generate_fix(self, module_name, error_msg, logs=""):
        """Sends a fix request to Antigravity via Redis Queue or JSON Bridge."""
        task_id = f"fix_{module_name}_{int(time.time())}"
        request_data = {
            "id": task_id,
            "task": "fix_plugin",
            "name": module_name,
            "error": error_msg,
            "logs": logs,
            "timestamp": time.time()
        }
        
        # 1. Try Redis Queue
        if self.redis.ping():
            if self.redis.push_task("antigravity_queue", request_data):
                logger.info(f"Fix request queued in Redis for {module_name}")
                return task_id

        # 2. Fallback to JSON file bridge
        request_file = os.path.join(self.request_dir, f"req_{task_id}.json")
        try:
            with open(request_file, "w", encoding="utf-8") as f:
                json.dump(request_data, f, indent=4)
            logger.info(f"Fix request sent via JSON Bridge for {module_name}: {request_file}")
            return task_id
        except Exception as e:
            logger.error(f"Failed to send fix request: {e}")
            return None

    def patch_code(self, task_id, timeout=30):
        """Polls for the fix response."""
        # Monitoring both Redis and JSON for responses could be complex, 
        # for now we focus on the existing JSON polling or a Redis sub.
        response_file = os.path.join(self.response_dir, f"res_{task_id}.json")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if os.path.exists(response_file):
                try:
                    with open(response_file, "r", encoding="utf-8") as f:
                        result = json.load(f)
                    logger.info(f"Fix received for task {task_id}: {result.get('status')}")
                    return result
                except Exception as e:
                    logger.error(f"Error reading response file: {e}")
            time.sleep(1)
            
        logger.warning(f"Timeout waiting for fix response: {task_id}")
        return None
