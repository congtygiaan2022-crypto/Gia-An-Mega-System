import time
import uuid
import logging
from database.mysql_connector import mysql_connector, Workflow
from database.redis_connector import redis_connector

logger = logging.getLogger("WorkflowEngine")

class WorkflowEngine:
    """
    Manages multi-step automation workflows.
    - Workflow Registry (MySQL)
    - Step Execution (Redis Queue)
    - State Tracking (Redis/MySQL)
    """
    def __init__(self):
        self.mysql = mysql_connector
        self.redis = redis_connector
        self.mysql.init_db()

    def create_workflow(self, name, description, steps):
        """Registers a new workflow in MySQL."""
        session = self.mysql.get_session()
        try:
            workflow = Workflow(name=name, description=description, steps=steps)
            session.add(workflow)
            session.commit()
            logger.info(f"Workflow '{name}' created successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def run_workflow(self, name, context=None):
        """Starts a workflow by fetching steps and queuing the first one."""
        session = self.mysql.get_session()
        try:
            workflow = session.query(Workflow).filter(Workflow.name == name).first()
            if not workflow:
                logger.error(f"Workflow '{name}' not found.")
                return None
            
            run_id = str(uuid.uuid4())
            logger.info(f"Starting workflow run: {run_id} ({name})")
            
            # Queue the first step
            if workflow.steps:
                first_step = workflow.steps[0]
                task_data = {
                    "workflow_name": name,
                    "run_id": run_id,
                    "step_index": 0,
                    "step_data": first_step,
                    "context": context or {}
                }
                self.redis.push_task("workflow_step_queue", task_data)
                return run_id
            return None
        finally:
            session.close()

    def handle_step_completion(self, run_id, step_index, result):
        """Triggered when a step completes to queue the next one."""
        # This would be called by a worker listening to results
        pass

# Global instance
workflow_engine = WorkflowEngine()
