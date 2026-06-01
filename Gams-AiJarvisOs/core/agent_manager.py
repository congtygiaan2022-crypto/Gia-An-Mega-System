from agents.analysis_agent.analysis_agent import AnalysisAgent
from agents.report_agent.report_agent import ReportAgent
from agents.automation_agent.automation_agent import AutomationAgent
from agents.debug_agent.debug_agent import DebugAgent
from core.logger import get_module_logger

logger = get_module_logger("AgentManager")

class AgentManager:
    """
    Jarvis OS Agent Manager
    Manages and coordinates all AI agents.
    """
    def __init__(self):
        self.analysis_agent = AnalysisAgent()
        self.report_agent = ReportAgent()
        self.automation_agent = AutomationAgent()
        self.debug_agent = DebugAgent()

    def get_agent(self, agent_type):
        """Returns the requested agent instance."""
        if agent_type == "analysis":
            return self.analysis_agent
        elif agent_type == "report":
            return self.report_agent
        elif agent_type == "automation":
            return self.automation_agent
        elif agent_type == "debug":
            return self.debug_agent
        else:
            logger.warning(f"Unknown agent type requested: {agent_type}")
            return None

    def run_all_monitors(self):
        """Runs background monitors for all agents (e.g., debug, system)."""
        logger.info("Running background agent tasks...")
        # Example: Debug agent scanning for errors
        debug_results = self.debug_agent.run()
        return {"debug": debug_results}

# Global instance
agent_manager = AgentManager()
