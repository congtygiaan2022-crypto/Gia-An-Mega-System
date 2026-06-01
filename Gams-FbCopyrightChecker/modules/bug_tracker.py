import json
import threading
import time
import traceback
import uuid
from pathlib import Path

# Workspace root (project directory)
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

FIND_BUG_FILE = WORKSPACE_ROOT / "find_bug.jsonl"
FIX_BUG_FILE = WORKSPACE_ROOT / "fix_bug.jsonl"
_file_lock = threading.Lock()

def _ensure_files() -> None:
    """Ensure bug tracking files exist."""
    for p in (FIND_BUG_FILE, FIX_BUG_FILE):
        if not p.exists():
            p.touch()

def log_bug(feature: str, step: str, exc: Exception) -> str:
    """Append a bug entry to *find_bug* and return its unique ID.

    Args:
        feature: High‑level feature name (e.g., "copyright_checker").
        step: Specific step or function where the error occurred.
        exc: The exception instance.
    """
    _ensure_files()
    bug_id = uuid.uuid4().hex
    entry = {
        "id": bug_id,
        "timestamp": time.time(),
        "feature": feature,
        "step": step,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "traceback": traceback.format_exc()
    }
    with _file_lock:
        with open(FIND_BUG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return bug_id

def clear_bug(feature: str = None, step: str = None, bug_id: str = None) -> int:
    """Move matching bug entries from *find_bug* to *fix_bug*.

    Returns the number of moved entries.
    """
    _ensure_files()
    with open(FIND_BUG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    kept = []
    moved = []
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        match = False
        if bug_id and entry.get("id") == bug_id:
            match = True
        elif feature and step:
            if entry.get("feature") == feature and entry.get("step") == step:
                match = True
        if match:
            entry["fixed_timestamp"] = time.time()
            moved.append(entry)
        else:
            kept.append(line)
    with open(FIND_BUG_FILE, "w", encoding="utf-8") as f:
        f.writelines(kept)
    if moved:
        with open(FIX_BUG_FILE, "a", encoding="utf-8") as f:
            for e in moved:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return len(moved)

def get_pending_bugs() -> list[dict]:
    """Return a list of pending bug entries (as dicts)."""
    _ensure_files()
    bugs = []
    with open(FIND_BUG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                bugs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return bugs

def track_errors(feature: str, step: str):
    """Decorator that logs exceptions to *find_bug* and clears entries on success.

    Example::
        @track_errors("copyright_checker", "switch_context_via_menu")
        def switch_context_via_menu(...):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                clear_bug(feature=feature, step=step)
                return result
            except Exception as e:
                log_bug(feature, step, e)
                raise
        return wrapper
    return decorator
