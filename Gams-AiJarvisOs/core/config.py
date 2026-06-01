import os

# Base project directory (h:/Tool_tucode/AI_Javis_Manus2/javis-agent)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Important Directories
CORE_DIR = os.path.join(PROJECT_ROOT, "core")
TOOLS_DIR = os.path.join(PROJECT_ROOT, "tools")
PLUGINS_DIR = os.path.join(PROJECT_ROOT, "plugins")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
DATABASE_DIR = os.path.join(PROJECT_ROOT, "database")
SCHEDULER_DIR = os.path.join(PROJECT_ROOT, "scheduler")
MEMORY_DIR = os.path.join(PROJECT_ROOT, "memory")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
WORKFLOWS_DIR = os.path.join(PROJECT_ROOT, "workflows")
INTEGRATIONS_DIR = os.path.join(PROJECT_ROOT, "integrations")

ARTIFACT_DIR = os.path.join(os.path.expanduser("~"), ".gemini", "antigravity", "brain")

# Registry Config
AUTO_LOAD_PLUGINS = True
