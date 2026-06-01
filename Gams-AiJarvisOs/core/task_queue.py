import asyncio
import uuid
from typing import Dict, Any

class TaskQueue:
    def __init__(self):
        print("TaskQueue: Initializing new instance.")
        self.tasks: Dict[str, Dict[str, Any]] = {}

    def submit_task(self, task_description: str) -> str:
        # Singleton logic: Check if a task with the same description is already active
        for tid, t in self.tasks.items():
            if t["description"] == task_description and t["status"] in ["pending", "running"]:
                return tid

        task_id = str(uuid.uuid4())[:8] # Use shorter IDs for readability
        self.tasks[task_id] = {
            "id": task_id,
            "description": task_description,
            "status": "pending",
            "result": None,
            "logs": []
        }
        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        return self.tasks.get(task_id, {"error": "Task not found"})

    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        return self.tasks

    def log(self, task_id: str, message: str):
        if task_id in self.tasks:
            self.tasks[task_id]["logs"].append(message)

    def delete_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False

    def cleanup_tasks(self):
        """Xóa tất cả các task đã hoàn thành hoặc thất bại để dọn dẹp UI."""
        to_delete = [tid for tid, t in self.tasks.items() if t["status"] in ["completed", "failed"]]
        for tid in to_delete:
            del self.tasks[tid]
        return len(to_delete)

    async def _execute_workflow(self, task_id: str):
        from core.workflow_engine import run_workflow
        self.tasks[task_id]["status"] = "running"
        try:
            # We defer to the workflow engine to handle the actual agent routing
            result = await asyncio.to_thread(run_workflow, task_id, self.tasks[task_id]["description"], self)
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["result"] = result
        except Exception as e:
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["result"] = str(e)
            self.log(task_id, f"System error: {e}")

print("Queue: Global Task Queue instance created.")
global_task_queue = TaskQueue()
