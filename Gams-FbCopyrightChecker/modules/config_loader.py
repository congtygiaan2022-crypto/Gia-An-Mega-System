import json
import os

# Load .env file if present (python-dotenv optional)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_DEFAULTS = {
    "facebook": {
        "email": "", "password": "", "profile_url": "",
        "profile_name": "", "uid": "", "2fa_secret": "", "fanpages": [],
    },
    "selenium": {
        "headless": False, "browser": "chrome",
        "implicit_wait": 10, "page_load_timeout": 30,
        "chrome_binary": "",
    },
    "database": {"path": os.path.join(_BASE_DIR, "db", "fb_checker.db")},
    "logging": {
        "level": "INFO",
        "file": os.path.join(_BASE_DIR, "logs", "app.log"),
        "max_bytes": 5242880, "backup_count": 3,
    },
    "checker": {
        "scan_interval_seconds": 60,
        "keywords": ["copyright", "DMCA", "removed", "violated"],
        "auto_delete_flagged": False,
        "confidence_threshold": 0.90,
    },
    "agent": {
        "max_workers": 3,
        "screenshot_on_classify": False,
        "auto_learn_patterns": True,
    },
    "notifications": {
        "webhook_url": "",
        "telegram_chat_id": "",
    },
    "api": {
        "host": "0.0.0.0",
        "port": 8000,
    },
    "mobile_settings": {
        "enabled": False,
        "user_agents": [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/130.0.0.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 15; Pixel 9 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 15; SM-S938B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 15; SM-A566B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 15; V2415A) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36"
        ],
        "grid_layout": "2x2",
        "window_index": 0,
        "grid_rows": 1,
        "grid_cols": 1
    }
}


def load_config(path: str = None) -> dict:
    if path is None:
        path = os.path.join(_BASE_DIR, "config.json")
    cfg = json.loads(json.dumps(_DEFAULTS))  # deep copy defaults
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            for section, values in user_cfg.items():
                if isinstance(values, dict) and section in cfg:
                    cfg[section].update(values)
                else:
                    cfg[section] = values
        except Exception as e:
            print(f"[WARNING] config.json parse error: {e} — using defaults")
    else:
        print(f"[WARNING] config.json not found at {path} — using defaults")
    return cfg


CONFIG = load_config()
