import os
import json
from core.config import PROJECT_ROOT
from core.logger import get_module_logger

logger = get_module_logger("WorkflowBuilder")

class WorkflowBuilder:
    def __init__(self):
        self.workflows_dir = os.path.join(PROJECT_ROOT, "workflows")
        os.makedirs(self.workflows_dir, exist_ok=True)

    def create_workflow(self, name, description, steps):
        """Creates a new workflow JSON file."""
        workflow_data = {
            "name": name,
            "description": description,
            "steps": steps,
            "created_at": os.path.getctime(self.workflows_dir) if os.path.exists(self.workflows_dir) else 0
        }
        file_path = os.path.join(self.workflows_dir, f"{name}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(workflow_data, f, indent=4, ensure_ascii=False)
            logger.info(f"Workflow '{name}' created at {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create workflow '{name}': {e}")
            return False

    def edit_workflow(self, name, updates):
        """Updates an existing workflow."""
        file_path = os.path.join(self.workflows_dir, f"{name}.json")
        if not os.path.exists(file_path):
            logger.warning(f"Workflow '{name}' not found for editing.")
            return False
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            data.update(updates)
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"Workflow '{name}' updated.")
            return True
        except Exception as e:
            logger.error(f"Failed to edit workflow '{name}': {e}")
            return False
