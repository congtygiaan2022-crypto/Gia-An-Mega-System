from tools.tool_registry import registry
from core.plugin_registry import plugin_registry
import ast
import asyncio
import inspect
from core.logger import get_module_logger

logger = get_module_logger("Executor")

class ToolExecutor:
    def execute(self, step: str):
        # Extremely simple parser turning `tool_name(arg)` into python call
        try:
            logger.info(f"Executing step: {step}")
            # Find the first parenthesis
            if "(" not in step:
                return "Not a valid tool call format"
                
            idx = step.find("(")
            tool_name = step[:idx].strip()
            args_str = step[idx:]
            
            tool_func = registry.get_tool(tool_name)
            if not tool_func:
                # Try plugin registry
                plugin = plugin_registry.get_plugin(tool_name)
                if plugin:
                    tool_func = plugin.run
                else:
                    logger.warning(f"Tool/Plugin {tool_name} not found.")
                    return f"Tool/Plugin {tool_name} not found"
                
            # Parse arguments securely using ast.literal_eval
            args = ast.literal_eval(args_str)
            if not isinstance(args, tuple):
                 args = (args,)
                 
            # Execute synchronously or asynchronously as needed
            if inspect.iscoroutinefunction(tool_func):
                result = asyncio.run(tool_func(*args))
            else:
                result = tool_func(*args)
                
            logger.info(f"Step executed successfully. Result: {str(result)[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {step}: {e}")
            return f"Error executing tool: {e}"
