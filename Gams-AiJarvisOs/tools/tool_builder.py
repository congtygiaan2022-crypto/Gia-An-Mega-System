"""
tools/tool_builder.py — Auto-generates new tools via Antigravity when agent 
requests a tool that doesn't exist yet.
"""
import os
import importlib
from connectors.antigravity_connector import antigravity
from tools.tool_registry import registry as tool_registry


class ToolBuilder:
    """
    If agent tries a tool that doesn't exist:
      1. Ask Antigravity to generate a Python tool file
      2. Save to /tools/
      3. Reload the ToolRegistry
    """

    TOOLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))

    def create_tool(self, description: str, tool_name: str = None) -> str:
        """Request a new tool from Antigravity and save it."""
        prompt = f"Create a Python automation tool:\n{description}\n\nReturn only Python code."
        code = antigravity.run(prompt)

        if not code or code.startswith("# Generation failed"):
            return f"Tool generation failed: {code}"

        # Derive filename
        if not tool_name:
            tool_name = "_".join(description.lower().split()[:4]).replace("-", "_")
        filename = f"{tool_name}.py"
        path = os.path.join(self.TOOLS_DIR, filename)

        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

        print(f"[ToolBuilder] New tool saved: {path}")

        # Auto-reload tool registry
        tool_registry.reload()
        return f"Tool '{tool_name}' created and registered."

    def build_if_missing(self, tool_name: str, description: str) -> bool:
        """
        Check if tool exists in registry; if not, build it.
        Returns True if tool is now available.
        """
        if tool_registry.has(tool_name):
            return True

        print(f"[ToolBuilder] Tool '{tool_name}' not found. Building...")
        result = self.create_tool(description, tool_name)
        print(f"[ToolBuilder] {result}")
        return tool_registry.has(tool_name)


# Global singleton
tool_builder = ToolBuilder()
