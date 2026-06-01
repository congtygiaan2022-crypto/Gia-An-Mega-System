import os
import json
from datetime import datetime
from core.logger import get_module_logger

logger = get_module_logger("CampaignMonitor")

class CampaignMonitor:
    def __init__(self):
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        self.error_log = os.path.join(self.log_dir, "campaign_errors.log")
        os.makedirs(self.log_dir, exist_ok=True)
        self.active_campaigns = {}

    def start_campaign(self, campaign_id, name):
        self.active_campaigns[campaign_id] = {
            "name": name,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "errors": []
        }
        logger.info(f"Campaign Started: {name} (ID: {campaign_id})")

    def end_campaign(self, campaign_id, success=True, result=None):
        if campaign_id in self.active_campaigns:
            status = "success" if success else "failed"
            self.active_campaigns[campaign_id]["status"] = status
            self.active_campaigns[campaign_id]["end_time"] = datetime.now().isoformat()
            self.active_campaigns[campaign_id]["result"] = result
            
            log_msg = f"Campaign {status.capitalize()}: {self.active_campaigns[campaign_id]['name']}"
            if success:
                logger.info(log_msg)
            else:
                logger.error(log_msg)
            
            return self.active_campaigns[campaign_id]
        return None

    def add_step(self, campaign_id, step_msg):
        if campaign_id in self.active_campaigns:
            if "steps" not in self.active_campaigns[campaign_id]:
                self.active_campaigns[campaign_id]["steps"] = []
            self.active_campaigns[campaign_id]["steps"].append({
                "timestamp": datetime.now().isoformat(),
                "message": step_msg
            })
            logger.info(f"Campaign {campaign_id} Step: {step_msg}")

    def report_error(self, campaign_id, module, error_msg, traceback=None):
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "campaign_id": campaign_id,
            "module": module,
            "message": error_msg,
            "traceback": traceback
        }
        
        if campaign_id in self.active_campaigns:
            self.active_campaigns[campaign_id]["errors"].append(error_entry)
            self.active_campaigns[campaign_id]["status"] = "failed"
        
        logger.error(f"Error in {module} (Campaign: {campaign_id}): {error_msg}")
        
        # Write to dedicated error log
        with open(self.error_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(error_entry, ensure_ascii=False) + "\n")
            
        return error_entry

# Global monitor instance
monitor = CampaignMonitor()
