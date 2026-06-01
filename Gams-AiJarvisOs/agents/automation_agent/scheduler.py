from core.scheduler import global_scheduler
from core.logger import get_module_logger

logger = get_module_logger("AutomationScheduler")

class AutomationScheduler:
    def __init__(self):
        self.scheduler = global_scheduler

    def schedule_task(self, task_name, cron_expression, plugin_name, args=None):
        """Schedules a task via the global scheduler."""
        logger.info(f"Scheduling task: {task_name} with cron: {cron_expression}")
        # Logic to add to scheduler (assuming global_scheduler has a method to add jobs dynamically)
        # For now, we interact with the existing core scheduler's mechanisms
        try:
            # Placeholder for actual scheduling logic which might involve updating task_manager.json
            from core.task_manager import TaskManager
            tm = TaskManager()
            tm.add_task({
                "name": task_name,
                "plugin": plugin_name,
                "schedule": cron_expression,
                "accounts": args or {},
                "status": "active"
            })
            self.scheduler.reload_jobs()
            return True
        except Exception as e:
            logger.error(f"Failed to schedule task {task_name}: {e}")
            return False

    def cron_runner(self):
        """Monitors and runs cron jobs (logic already in core/scheduler.py)."""
        # This module can provide additional monitoring if needed
        pass
