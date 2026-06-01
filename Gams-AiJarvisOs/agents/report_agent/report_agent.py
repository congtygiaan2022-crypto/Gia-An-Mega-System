from agents.report_agent.data_collector import DataCollector
from agents.report_agent.data_processor import DataProcessor
from agents.report_agent.report_generator import ReportGenerator
from core.logger import get_module_logger

logger = get_module_logger("ReportAgent")

class ReportAgent:
    """
    AI Agent Report
    - Data Collector: collect_data, fetch_metrics
    - Data Processor: clean_data, calculate_metrics
    - Report Generator: generate_report, export_report
    """
    def __init__(self):
        self.collector = DataCollector()
        self.processor = DataProcessor()
        self.generator = ReportGenerator()

    def run(self, source=None):
        """Main execution flow for the Report Agent."""
        logger.info("Report Agent started...")
        data = self.collector.collect_data()
        processed = self.processor.calculate_metrics(data)
        report = self.generator.generate_report(processed)
        path = self.generator.export_report(report)
        return {"report": report, "path": path}

if __name__ == "__main__":
    agent = ReportAgent()
    print(agent.run())
