import time
from core.logger import get_module_logger
from core.plugin_execution_engine import plugin_execution_engine
from database.redis_connector import redis_connector

logger = get_module_logger("TaskRunner")

class TaskRunner:
    def __init__(self):
            except Exception as e:
                logger.error(f"Error running plugin {plugin_name}: {e}")
                
        threading.Thread(target=worker, daemon=True).start()
        return task_id

    def monitor_execution(self, task_id):
        """Returns the status and logs of a running task."""
        return self.queue.get_task(task_id)
