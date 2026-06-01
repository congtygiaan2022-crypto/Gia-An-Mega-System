import sys
import os
import json

# Add current directory to path
sys.path.append(os.getcwd())

def test_imports():
    print("--- Testing Core Imports ---")
    try:
        from core.logger import logger
        print("[OK] core.logger")
        from core.campaign_monitor import monitor
        print("[OK] core.campaign_monitor")
        from core.plugin_registry import plugin_registry
        print("[OK] core.plugin_registry")
        from tools.tool_registry import registry
        print("[OK] tools.tool_registry")
    except Exception as e:
        print(f"[FAIL] Core import failed: {e}")

def test_agents():
    print("\n--- Testing Autonomous Agents ---")
    agents = [
        "agents.debug_agent.DebugAgent",
        "agents.code_fix_agent.CodeFixAgent",
        "agents.plugin_builder.PluginBuilder",
        "agents.system_monitor.SystemMonitor"
    ]
    for agent_path in agents:
        try:
            module_name, class_name = agent_path.rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            agent_instance = agent_class()
            print(f"[OK] {agent_path} initialized")
        except Exception as e:
            print(f"[FAIL] {agent_path}: {e}")

def test_tools():
    print("\n--- Testing Evolution Tools ---")
    from tools.tool_registry import registry
    from core.config import TOOLS_DIR
    registry.auto_load_tools(TOOLS_DIR)
    
    expected_tools = ["save_to_excel", "bao_cao_ads_tiktok", "analyze_tiktok_ads"]
    all_tools = registry.get_all_tools().keys()
    
    for t in expected_tools:
        if t in all_tools:
            print(f"[OK] Tool '{t}' is registered")
        else:
            print(f"[MISSING] Tool '{t}' not found")

if __name__ == "__main__":
    test_imports()
    test_agents()
    test_tools()
    print("\nVerification process complete.")
