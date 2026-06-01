from agents.automation_agent.workflow_builder import WorkflowBuilder
from agents.automation_agent.scheduler import AutomationScheduler
from agents.automation_agent.task_runner import TaskRunner
from core.logger import get_module_logger

logger = get_module_logger("AutomationAgent")

class AutomationAgent:
    """
    AI Agent Automation
    - Workflow Builder: create/edit workflows
    - Scheduler: schedule tasks, cron runner
    - Task Runner: run plugins, monitor execution
    """
    def __init__(self):
        self.builder = WorkflowBuilder()
        self.scheduler = AutomationScheduler()
        self.task_runner = TaskRunner()

    def run(self, task_type, **kwargs):
        """Generic run method for automation tasks."""
        if task_type == "create_workflow":
            return self.builder.create_workflow(kwargs.get("name"), kwargs.get("description"), kwargs.get("steps"))
        elif task_type == "schedule":
            return self.scheduler.schedule_task(kwargs.get("name"), kwargs.get("cron"), kwargs.get("plugin"), kwargs.get("args"))
        elif task_type == "run":
            return self.task_runner.run_plugin(kwargs.get("plugin"), kwargs.get("args"))
        else:
            logger.warning(f"Unknown automation task type: {task_type}")
            return None

if __name__ == "__main__":
    agent = AutomationAgent()
    # Example: agent.run("run", plugin="test_plugin")
