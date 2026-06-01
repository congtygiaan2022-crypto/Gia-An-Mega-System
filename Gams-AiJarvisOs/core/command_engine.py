import re
from typing import Tuple, Any, Optional

class CommandEngine:
    def __init__(self):
        # Define common patterns for local routing
        self.patterns = [
            (r"^(?:mở|open)\s+(https?://\S+|google|youtube|facebook|shopee)", self._handle_open),
            (r"^(?:tìm|search)\s+(.+)", self._handle_search),
            (r"^(?:tạo công cụ|create tool)\s+(\w+)", self._handle_create_tool),
            (r"^(?:chụp ảnh|screenshot|capture)", self._handle_screenshot),
            (r"^(?:cuộn|scroll)\s*(u|d|up|down)?", self._handle_scroll),
        ]

    def parse(self, text: str) -> Optional[Tuple[str, Any]]:
        """
        Parses text and returns (intent, args) if found locally.
        """
        text = text.lower().strip()
        
        # 1. Match regex patterns
        for pattern, handler in self.patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                return handler(match)
        
        # 2. Dynamic check: See if the text starts with a registered tool name
        from tools.tool_registry import registry
        all_tools = registry.get_all_tools()
        for tool_name in all_tools:
            if text.startswith(tool_name.lower()):
                # Extract args if in paren, else take the rest
                args_text = text[len(tool_name):].strip()
                if args_text.startswith("(") and args_text.endswith(")"):
                    args_text = args_text[1:-1]
                return tool_name, args_text
        
        return None

    def _handle_open(self, match) -> Tuple[str, str]:
        target = match.group(1)
        if not target.startswith("http"):
            if "google" in target: target = "https://www.google.com"
            elif "youtube" in target: target = "https://www.youtube.com"
            elif "facebook" in target: target = "https://www.facebook.com"
            elif "shopee" in target: target = "https://shopee.vn"
        return "browser_open", target

    def _handle_search(self, match) -> Tuple[str, str]:
        return "browser_search", match.group(1)

    def _handle_create_tool(self, match) -> Tuple[str, str]:
        return "create_tool", match.group(1)

    def _handle_screenshot(self, match) -> Tuple[str, None]:
        return "browser_screenshot", None

    def _handle_scroll(self, match) -> Tuple[str, str]:
        direction = match.group(1) or "down"
        if direction in ["u", "up"]: direction = "up"
        else: direction = "down"
        return "browser_scroll", direction

# Global instance
engine = CommandEngine()
