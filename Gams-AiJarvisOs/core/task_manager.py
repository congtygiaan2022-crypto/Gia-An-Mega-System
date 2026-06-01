import json
import os
import uuid

class TaskManager:
    def __init__(self):
        self.path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "scheduler_registry.json")
        if not os.path.exists(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([], f)
                
    def get_all_tasks(self):
        if not os.path.exists(self.path): return []
        with open(self.path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
            
    def get_task(self, task_id):
        tasks = self.get_all_tasks()
        for t in tasks:
            if t.get("id") == task_id:
                return t
        return None
        
    def add_task(self, task_data):
        tasks = self.get_all_tasks()
        if "id" not in task_data or not task_data["id"]:
            task_data["id"] = "task_" + str(uuid.uuid4())[:8]
        tasks.append(task_data)
        self._save(tasks)
        return task_data["id"]
        
    def update_task(self, task_id, task_data):
        tasks = self.get_all_tasks()
        for i, t in enumerate(tasks):
            if t.get("id") == task_id:
                task_data["id"] = task_id # preserve id
                tasks[i] = task_data
                self._save(tasks)
                return True
        return False
        
    def delete_task(self, task_id):
        tasks = self.get_all_tasks()
        tasks = [t for t in tasks if t.get("id") != task_id]
        self._save(tasks)

    def _save(self, tasks):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)
