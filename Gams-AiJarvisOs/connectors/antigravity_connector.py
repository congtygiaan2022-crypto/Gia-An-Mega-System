"""
connectors/antigravity_connector.py
Thin v2 wrapper around the full implementation in integrations/antigravity_connector.py.
Also adds a simple subprocess fallback for direct CLI usage.
"""
import subprocess
import sys
import os

# Re-export the full connector from integrations/ so nothing breaks
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from integrations.antigravity_connector import AntigravityConnector, antigravity_connector


class AntigravityConnectorV2(AntigravityConnector):
    """
    Extends the base connector with direct subprocess CLI support.
    If `antigravity` binary is in PATH, use it; otherwise fall back to artifact bridge.
    """

    def run(self, instruction: str) -> str:
        """
        Try to call the `antigravity` CLI directly first.
        Falls back to the artifact bridge if the binary is not found.
        """
        try:
            result = subprocess.run(
                ["antigravity", instruction],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
        except FileNotFoundError:
            pass  # CLI not in PATH — use artifact bridge
        except Exception as e:
            pass

        # Artifact bridge fallback
        return self.request_tool_generation(
            tool_name=instruction[:50],
            requirement=instruction,
        )


# Global v2 singleton
antigravity = AntigravityConnectorV2()
