"""
Bug Tracker - Hệ thống tự động ghi lỗi và theo dõi việc sửa lỗi
=================================================================
- Khi có lỗi xảy ra trong bất kỳ tác vụ nào, ghi vào find_bug.md
- Claude Code đọc find_bug.md và tự sửa lỗi
- Sau khi sửa xong, xóa dòng đó trong find_bug.md và ghi vào fix_bug.md
"""

import os
import re
import sys
import traceback
import threading
from datetime import datetime
from typing import Optional, Callable

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except:
    pass

# ─────────────────────────────────────────────
# Đường dẫn file
# ─────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIND_BUG_FILE = os.path.join(_ROOT, "find_bug.md")
FIX_BUG_FILE  = os.path.join(_ROOT, "fix_bug.md")

_lock = threading.Lock()  # Thread-safe khi ghi file


# ═══════════════════════════════════════════════════════════════════
#  BugEntry - Đại diện cho một lỗi
# ═══════════════════════════════════════════════════════════════════
class BugEntry:
    def __init__(
        self,
        bug_id: str,
        timestamp: str,
        module: str,
        task: str,
        error_type: str,
        error_message: str,
        traceback_str: str,
        context: dict,
        severity: str = "ERROR",
    ):
        self.bug_id       = bug_id
        self.timestamp    = timestamp
        self.module       = module
        self.task         = task
        self.error_type   = error_type
        self.error_message = error_message
        self.traceback_str = traceback_str
        self.context      = context
        self.severity     = severity   # ERROR | WARNING | CRITICAL

    # ── Markdown block ──────────────────────────────────────────────
    def to_markdown(self) -> str:
        ctx_lines = "\n".join(
            f"  - **{k}**: `{v}`" for k, v in self.context.items()
        )
        tb_block  = (
            f"```\n{self.traceback_str.strip()}\n```"
            if self.traceback_str
            else "_Không có traceback_"
        )
        return (
            f"## 🐛 [{self.bug_id}] — {self.task}\n"
            f"- **Thời gian**: `{self.timestamp}`\n"
            f"- **Module**: `{self.module}`\n"
            f"- **Mức độ**: `{self.severity}`\n"
            f"- **Loại lỗi**: `{self.error_type}`\n"
            f"- **Thông báo lỗi**: `{self.error_message}`\n"
            f"- **Context**:\n{ctx_lines}\n"
            f"- **Traceback**:\n{tb_block}\n"
            f"<!-- END_BUG:{self.bug_id} -->\n"
        )

    # ── Fix log block ────────────────────────────────────────────────
    def to_fix_markdown(self, fix_note: str = "") -> str:
        return (
            f"## ✅ [{self.bug_id}] — {self.task}  `ĐÃ SỬA`\n"
            f"- **Thời gian phát hiện**: `{self.timestamp}`\n"
            f"- **Thời gian sửa**: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"- **Module**: `{self.module}`\n"
            f"- **Loại lỗi**: `{self.error_type}`\n"
            f"- **Thông báo lỗi**: `{self.error_message}`\n"
            f"- **Ghi chú sửa lỗi**: {fix_note or '_Claude Code đã tự động phát hiện và sửa._'}\n"
            f"---\n"
        )


# ═══════════════════════════════════════════════════════════════════
#  BugTracker — Singleton
# ═══════════════════════════════════════════════════════════════════
class BugTracker:
    """
    Hệ thống theo dõi và ghi lỗi tự động.

    Cách dùng nhanh (decorator):
        @BugTracker.watch(module="core.session", task="login")
        def login_with_password(self, ...):
            ...

    Cách dùng thủ công:
        try:
            risky_operation()
        except Exception as e:
            BugTracker.report(e, module="core.bettor", task="place_bet",
                              context={"match": match_name, "amount": amount})
    """

    _instance: Optional["BugTracker"] = None
    _counter  = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_files()
        return cls._instance

    # ── Khởi tạo file ────────────────────────────────────────────────
    def _init_files(self):
        for path, header in [
            (FIND_BUG_FILE, _find_bug_header()),
            (FIX_BUG_FILE,  _fix_bug_header()),
        ]:
            if not os.path.exists(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(header)

    # ── Tạo Bug ID duy nhất ─────────────────────────────────────────
    @classmethod
    def _next_id(cls) -> str:
        cls._counter += 1
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"BUG_{ts}_{cls._counter:03d}"

    # ─────────────────────────────────────────────────────────────────
    #  report() — Ghi lỗi vào find_bug.md
    # ─────────────────────────────────────────────────────────────────
    @classmethod
    def report(
        cls,
        exc: Exception,
        module: str      = "unknown",
        task: str        = "unknown",
        context: dict    = None,
        severity: str    = "ERROR",
        extra_msg: str   = "",
    ) -> str:
        """
        Ghi lỗi vào find_bug.md.

        Trả về bug_id để tiện theo dõi.
        """
        cls()  # ensure singleton init
        bug_id  = cls._next_id()

        tb_str  = traceback.format_exc() if exc else ""
        err_type = type(exc).__name__ if exc else "UnknownError"
        err_msg  = (extra_msg + " | " if extra_msg else "") + str(exc)

        entry = BugEntry(
            bug_id        = bug_id,
            timestamp     = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            module        = module,
            task          = task,
            error_type    = err_type,
            error_message = err_msg,
            traceback_str = tb_str,
            context       = context or {},
            severity      = severity,
        )

        with _lock:
            with open(FIND_BUG_FILE, "a", encoding="utf-8") as f:
                f.write("\n" + entry.to_markdown() + "\n")
                
        # Send to global logger for AiJarvisOs
        import sys
        JARVIS_CORE_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')), 'Gams-AiJarvisOs', 'core')
        if JARVIS_CORE_PATH not in sys.path:
            sys.path.insert(0, JARVIS_CORE_PATH)
        try:
            import global_logger
            global_logger.report_bug("ToolAutoBcgame", f"{module}.{task}", err_msg, {"traceback": tb_str, "context": context})
        except ImportError:
            pass

        print(f"[BugTracker] 🐛 Đã ghi lỗi → {bug_id} | {module} | {task}")
        return bug_id

    # ─────────────────────────────────────────────────────────────────
    #  mark_fixed() — Xóa lỗi khỏi find_bug.md, ghi vào fix_bug.md
    # ─────────────────────────────────────────────────────────────────
    @classmethod
    def mark_fixed(cls, bug_id: str, fix_note: str = "") -> bool:
        """
        Đánh dấu lỗi đã được sửa:
          1. Đọc find_bug.md, tách block của bug_id ra.
          2. Xóa block đó khỏi find_bug.md.
          3. Ghi thông tin đã sửa vào fix_bug.md.
        """
        with _lock:
            # ── Đọc nội dung find_bug ────────────────────────────────
            if not os.path.exists(FIND_BUG_FILE):
                return False

            with open(FIND_BUG_FILE, encoding="utf-8") as f:
                content = f.read()

            # ── Tìm block của bug này ────────────────────────────────
            # Block bắt đầu bằng "## 🐛 [BUG_ID]" và kết thúc bằng "<!-- END_BUG:BUG_ID -->"
            pattern = (
                r"(##\s+🐛\s+\[" + re.escape(bug_id) + r"\].*?"
                r"<!--\s*END_BUG:" + re.escape(bug_id) + r"\s*-->)"
            )
            match = re.search(pattern, content, re.DOTALL)
            if not match:
                print(f"[BugTracker] ⚠️ Không tìm thấy bug_id={bug_id} trong find_bug.md")
                return False

            bug_block = match.group(1)

            # ── Parse thông tin cơ bản để ghi fix_bug ───────────────
            entry = _parse_bug_block(bug_block, bug_id)

            # ── Xóa block khỏi find_bug.md ──────────────────────────
            new_content = re.sub(pattern, "", content, flags=re.DOTALL)

            with open(FIND_BUG_FILE, "w", encoding="utf-8") as f:
                f.write(new_content.strip() + "\n")

            # ── Ghi vào fix_bug.md ───────────────────────────────────
            if not os.path.exists(FIX_BUG_FILE):
                with open(FIX_BUG_FILE, "w", encoding="utf-8") as f:
                    f.write(_fix_bug_header())

            fix_line = entry.to_fix_markdown(fix_note)
            with open(FIX_BUG_FILE, "a", encoding="utf-8") as f:
                f.write("\n" + fix_line)

        print(f"[BugTracker] ✅ Đã đánh dấu sửa → {bug_id}")
        return True

    # ─────────────────────────────────────────────────────────────────
    #  list_bugs() — Liệt kê tất cả lỗi chưa sửa
    # ─────────────────────────────────────────────────────────────────
    @classmethod
    def list_bugs(cls) -> list[dict]:
        """Trả về danh sách dict {bug_id, task, severity, timestamp} chưa sửa."""
        if not os.path.exists(FIND_BUG_FILE):
            return []
        with open(FIND_BUG_FILE, encoding="utf-8") as f:
            content = f.read()
        ids = re.findall(r"##\s+🐛\s+\[(BUG_[^\]]+)\]", content)
        result = []
        for bid in ids:
            block_m = re.search(
                r"##\s+🐛\s+\[" + re.escape(bid) + r"\](.*?)(?=##\s+🐛|$)",
                content, re.DOTALL
            )
            info = {"bug_id": bid, "task": "", "severity": "", "timestamp": ""}
            if block_m:
                block_txt = block_m.group(1)
                for field, key in [
                    (r"\*\*Mức độ\*\*:\s*`([^`]+)`", "severity"),
                    (r"\*\*Thời gian\*\*:\s*`([^`]+)`", "timestamp"),
                ]:
                    m = re.search(field, block_txt)
                    if m:
                        info[key] = m.group(1)
                task_m = re.search(r"^\s*—\s*(.+)", block_txt)
                if task_m:
                    info["task"] = task_m.group(1).strip()
            result.append(info)
        return result

    # ─────────────────────────────────────────────────────────────────
    #  watch() — Decorator tự động bắt lỗi
    # ─────────────────────────────────────────────────────────────────
    @classmethod
    def watch(
        cls,
        module: str   = "unknown",
        task: str     = "unknown",
        severity: str = "ERROR",
        reraise: bool = True,
        context_fn: Optional[Callable] = None,
    ):
        """
        Decorator: tự động gọi BugTracker.report() khi hàm ném exception.

        @BugTracker.watch(module="core.session", task="login_with_password")
        def login_with_password(self, phone, password, ...):
            ...
        """
        def decorator(func):
            import functools

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    ctx = {}
                    if context_fn:
                        try:
                            ctx = context_fn(*args, **kwargs)
                        except Exception:
                            pass
                    cls.report(
                        exc      = exc,
                        module   = module,
                        task     = task or func.__name__,
                        context  = ctx,
                        severity = severity,
                    )
                    if reraise:
                        raise
            return wrapper
        return decorator


# ═══════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════
def _parse_bug_block(block: str, bug_id: str) -> BugEntry:
    """Parse markdown block thành BugEntry (để ghi fix log)."""
    def _extract(pattern, default=""):
        m = re.search(pattern, block)
        return m.group(1).strip() if m else default

    return BugEntry(
        bug_id        = bug_id,
        timestamp     = _extract(r"\*\*Thời gian\*\*:\s*`([^`]+)`"),
        module        = _extract(r"\*\*Module\*\*:\s*`([^`]+)`"),
        task          = _extract(r"##\s+🐛\s+\[[^\]]+\]\s+—\s+(.+)"),
        error_type    = _extract(r"\*\*Loại lỗi\*\*:\s*`([^`]+)`"),
        error_message = _extract(r"\*\*Thông báo lỗi\*\*:\s*`([^`]+)`"),
        traceback_str = _extract(r"```\n(.*?)\n```", ""),
        context       = {},
        severity      = _extract(r"\*\*Mức độ\*\*:\s*`([^`]+)`", "ERROR"),
    )


def _find_bug_header() -> str:
    return (
        "# 🐛 FIND BUG — Danh sách lỗi cần sửa\n\n"
        "> File này được tự động tạo bởi **BugTracker**.\n"
        "> Claude Code sẽ đọc file này, tìm và sửa lỗi, rồi gọi `BugTracker.mark_fixed(bug_id)`.\n\n"
        "---\n"
    )


def _fix_bug_header() -> str:
    return (
        "# ✅ FIX BUG — Lịch sử các lỗi đã sửa\n\n"
        "> File này ghi lại toàn bộ lỗi đã được phát hiện và sửa thành công.\n\n"
        "---\n"
    )


# ═══════════════════════════════════════════════════════════════════
#  Convenience functions (module-level shortcut)
# ═══════════════════════════════════════════════════════════════════
def report_bug(
    exc: Exception,
    module: str   = "unknown",
    task: str     = "unknown",
    context: dict = None,
    severity: str = "ERROR",
    extra_msg: str = "",
) -> str:
    """Shortcut: BugTracker.report(...)"""
    return BugTracker.report(
        exc=exc, module=module, task=task,
        context=context, severity=severity, extra_msg=extra_msg,
    )


def mark_bug_fixed(bug_id: str, fix_note: str = "") -> bool:
    """Shortcut: BugTracker.mark_fixed(...)"""
    return BugTracker.mark_fixed(bug_id, fix_note)
