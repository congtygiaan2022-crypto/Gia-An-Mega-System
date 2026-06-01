from agents.debug_agent.error_monitor import ErrorMonitor
from agents.debug_agent.debug_analyzer import DebugAnalyzer
from agents.debug_agent.fix_engine import FixEngine
from core.logger import get_module_logger

logger = get_module_logger("DebugAgent")

class DebugAgent:
    """
    AI Agent Auto Fix Bug
    - Error Monitor: capture errors, collect logs
    - Debug Analyzer: analyze stacktrace, detect bug
    - Fix Engine: generate fix, patch code
    """
    def __init__(self):
        self.monitor = ErrorMonitor()
        self.analyzer = DebugAnalyzer()
        self.fix_engine = FixEngine()

    def run(self):
        """Main execution flow for the Debug Agent."""
        logger.info("Debug Agent started scanning for issues...")
        errors = self.monitor.capture_error()
        
        if not errors:
            return "No errors detected."

        results = []
        for error in errors:
            bug_info = self.analyzer.detect_bug(error)
            module = bug_info["module"]
            
            if module != "Unknown" and module != "CoreComponent":
                logger.info(f"Detected bug in module: {module}. Requesting fix...")
                logs = self.monitor.collect_logs(module)
                task_id = self.fix_engine.generate_fix(module, error, logs)
                results.append({"module": module, "task_id": task_id})
            else:
                logger.warning(f"Skipping fix for module: {module} (Type: {bug_info['type']})")
        
        return results

if __name__ == "__main__":
    agent = DebugAgent()
    print(agent.run())
