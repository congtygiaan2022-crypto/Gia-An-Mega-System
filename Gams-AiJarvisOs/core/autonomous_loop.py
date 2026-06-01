import time
from core.logger import get_module_logger

logger = get_module_logger("AutonomousLoop")

class AutonomousLoop:
    def __init__(self, planner, executor):
        self.planner = planner
        self.executor = executor
        self.running = False

    def start(self, task):
        self.running = True
        logger.info(f"Starting autonomous task: {task}")
        
        # Create initial plan
        steps = self.planner.create_plan(task)
        # Filter out empty or non-tool steps
        steps = [s.strip() for s in steps if s.strip() and "(" in s]
        
        results = []
        while self.running and steps:
            step = steps.pop(0)
            logger.info(f"Executing step: {step}")
            
            try:
                result = self.executor.execute(step)
                results.append({"step": step, "result": result})
                logger.info(f"Step result: {str(result)[:50]}...")
            except Exception as e:
                logger.error(f"Error in autonomous loop at step '{step}': {e}")
                results.append({"step": step, "error": str(e)})
            
            # Pause between steps to simulate human behavior and avoid rate limits
            time.sleep(2)

        self.running = False
        logger.info(f"Autonomous task completed: {task}")
        return results

    def stop(self):
        self.running = False
        logger.info("Autonomous loop stopped manually.")
        return "Autonomous loop stopped"
