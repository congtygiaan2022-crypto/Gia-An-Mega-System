from core.logger import get_module_logger
from core.memory_system import memory_system

logger = get_module_logger("InsightGenerator")

class InsightGenerator:
    def generate_insight(self, analysis_data):
        """Generates high-level insights from analysis."""
        logger.info("Generating insights...")
        insight = f"Insight based on {len(analysis_data) if isinstance(analysis_data, list) else 'data'}: Efficiency optimized."
        
        # Store in MySQL
        memory_system.store_long_term("AnalysisAgent", "insight", {"insight": insight, "source_data": analysis_data})
        
        return insight
