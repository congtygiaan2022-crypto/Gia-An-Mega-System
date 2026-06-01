"""
System-wide import test for Jarvis v2.
Runs from javis-agent/ directory.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

modules = [
    # Core
    ("core.logger",                 "get_module_logger"),
    ("core.config",                 "PROJECT_ROOT"),
    ("core.local_llm",              "local_llm"),
    ("core.error_manager",          "error_manager"),
    ("core.error_registry",         "error_registry"),
    ("core.task_queue",             "global_task_queue"),
    ("core.agent",                  "JavisAgent"),
    ("core.planner",                "Planner"),
    ("core.plugin_registry",        "plugin_registry"),
    ("core.tool_generator",         "tool_generator"),
    ("core.campaign_monitor",       "monitor"),
    ("core.workflow_engine",        "run_workflow"),
    ("core.autonomous_engine",      "autonomous_engine"),
    ("core.self_repair",            "repair"),
    # Agents
    ("agents.base_agent",           "BaseAgent"),
    ("agents.debug_agent",          "DebugAgent"),
    ("agents.code_fix_agent",       "CodeFixAgent"),
    ("agents.system_monitor",       "system_monitor"),
    ("agents.coordinator_agent",    "CoordinatorAgent"),
    # Tools
    ("tools.tool_registry",         "registry"),
    ("tools.report_tool",           "create_report"),
    # Integrations
    ("integrations.antigravity_connector", "antigravity_connector"),
    ("integrations.local_llm_connector",   "local_llm"),
    # Connectors (v2)
    ("connectors.antigravity_connector",   "antigravity"),
    # Memory
    ("memory.memory_store",         "global_memory"),
]

passed, failed = [], []

for mod, attr in modules:
    try:
        m = __import__(mod, fromlist=[attr])
        getattr(m, attr)
        passed.append(mod)
        print(f"  OK  {mod}")
    except Exception as e:
        failed.append((mod, str(e)))
        print(f"  FAIL  {mod}: {e}")

print(f"\n--- RESULT: {len(passed)} OK / {len(failed)} FAILED ---")
for mod, err in failed:
    print(f"  FAIL  {mod}: {err}")
