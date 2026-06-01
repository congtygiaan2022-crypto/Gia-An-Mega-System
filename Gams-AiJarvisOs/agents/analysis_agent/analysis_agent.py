from agents.analysis_agent.data_analyzer import DataAnalyzer
from agents.analysis_agent.strategy_engine import StrategyEngine
from agents.analysis_agent.insight_generator import InsightGenerator
from core.logger import get_module_logger

logger = get_module_logger("AnalysisAgent")

class AnalysisAgent:
    """
    AI Agent Analysis
    - Data Analyzer: analyze_data, detect_pattern
    - Strategy Engine: generate_solution, suggest_action
    - Insight Generator: generate_insight
    """
    def __init__(self):
        self.analyzer = DataAnalyzer()
        self.strategy = StrategyEngine()
        self.insight = InsightGenerator()

    def run(self, task_type, data):
        """Main execution flow for the Analysis Agent."""
        if task_type == "analyze":
            return self.analyzer.analyze_data(data)
        elif task_type == "solve":
            return self.strategy.generate_solution(data)
        elif task_type == "insight":
            return self.insight.generate_insight(data)
        else:
            logger.warning(f"Unknown analysis task type: {task_type}")
            return None

if __name__ == "__main__":
    agent = AnalysisAgent()
    # Example: print(agent.run("analyze", [1, 2, 3]))
