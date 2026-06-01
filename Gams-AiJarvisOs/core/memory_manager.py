import json
import os
from core.config import PROJECT_ROOT

class MemoryManager:
    def __init__(self):
        self.memory_dir = os.path.join(PROJECT_ROOT, "memory")
        os.makedirs(self.memory_dir, exist_ok=True)
        self.tasks_path = os.path.join(self.memory_dir, "tasks_memory.json")
        self.plugin_path = os.path.join(self.memory_dir, "plugin_memory.json")
        self.error_path = os.path.join(self.memory_dir, "error_memory.json")
        
        # Initialize if not exists
        for path, default in [
            (self.tasks_path, {"tasks": []}),
            (self.plugin_path, {"runs": []}),
            (self.error_path, {"errors": []})
        ]:
            if not os.path.exists(path):
                self._save(path, default)

    def _load(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def _save(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_task(self, task):
        data = self._load(self.tasks_path)
        data.setdefault("tasks", []).append(task)
        self._save(self.tasks_path, data)

    def add_plugin_run(self, run_data):
        data = self._load(self.plugin_path)
        data.setdefault("runs", []).append(run_data)
        self._save(self.plugin_path, data)

    def add_error(self, error_data):
        data = self._load(self.error_path)
        data.setdefault("errors", []).append(error_data)
        self._save(self.error_path, data)
