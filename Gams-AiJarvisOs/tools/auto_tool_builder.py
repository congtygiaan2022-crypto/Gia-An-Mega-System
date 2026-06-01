import os
from core.logger import get_module_logger

logger = get_module_logger("AutoToolBuilder")

class AutoToolBuilder:
    def __init__(self, tools_dir="tools"):
        self.tools_dir = tools_dir
        os.makedirs(self.tools_dir, exist_ok=True)

    def create_tool(self, name, code_content=None, description=""):
        filename = f"{name}.py"
        path = os.path.join(self.tools_dir, filename)

        if not code_content:
            code_content = f'''
"""
Auto-generated tool: {name}
Description: {description}
"""
from tools.tool_registry import tool

@tool(description="{description}")
def {name}(task):
    print(f"Running auto-generated tool: {name}")
    return f"Tool {name} executed with task: {{task}}"
'''

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(code_content)
            
            logger.info(f"Tool {name} created successfully at {path}")
            
            # Trigger registry reload
            from tools.tool_registry import reload_tools
            reload_tools()
            
            return f"Tool {name} created and registered successfully."
        except Exception as e:
            logger.error(f"Failed to create tool {name}: {e}")
            return f"Error creating tool: {e}"

# Global instance
tool_builder = AutoToolBuilder()
