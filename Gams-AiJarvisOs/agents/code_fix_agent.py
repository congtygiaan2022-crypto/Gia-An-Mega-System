import os
from core.logger import get_module_logger
from integrations.antigravity_connector import antigravity_connector

logger = get_module_logger("CodeFixAgent")

class CodeFixAgent:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def propose_fix(self, file_path, error_traceback):
        """Analyzes a file and proposes a fix for a specific error."""
        logger.info(f"Proposing fix for {file_path}")
        
        # In a real scenario, this would send the code + traceback to Antigravity
        # For now, we signal the need for a fix via the connector
        requirement = f"Sửa lỗi trong file {file_path}.\nTraceback: {error_traceback}"
        antigravity_connector.request_tool_generation(f"fix_{os.path.basename(file_path)}", requirement)
        
        return f"Yêu cầu sửa lỗi cho {file_path} đã được gửi tới Antigravity Core."

    def apply_fix(self, file_path, new_content):
        """Safely applies a fix and logs the change."""
        abs_path = os.path.join(self.project_root, file_path)
        if not os.path.exists(abs_path):
            logger.error(f"Cannot apply fix: File {file_path} not found.")
            return False

        # Rollback backup
        backup_path = abs_path + ".bak"
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                old_content = f.read()
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(old_content)
            
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            logger.info(f"CODE FIX SUCCESS: {file_path}. Backup created at {backup_path}")
            return True
        except Exception as e:
            logger.error(f"CODE FIX FAILED: {file_path}. Error: {e}")
            return False

# Global instance
code_fix_agent = CodeFixAgent()
