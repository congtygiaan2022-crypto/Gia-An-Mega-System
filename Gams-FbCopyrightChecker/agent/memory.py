"""
Tầng 4 — Memory & Learning
Ghi lại quyết định của agent, nhận phản hồi từ người dùng,
theo dõi độ chính xác, và học pattern từ các vi phạm đã xác nhận.
"""
import os
import sqlite3
import threading
from datetime import datetime
from typing import Optional

from modules.config_loader import CONFIG
from modules.logger import get_logger

log = get_logger(__name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AgentMemory:
    """
    Quản lý bộ nhớ dài hạn của agent: decisions, feedback, learned patterns.
    Dùng SQLite — cùng file DB với modules/database.py nhưng bảng riêng.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = CONFIG["database"]["path"]
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
        self.db_path = db_path
        self._db_lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()

    def _init_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS agent_decisions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id      TEXT NOT NULL,
                account_uid  TEXT DEFAULT '',
                method       TEXT DEFAULT 'keyword',
                confidence   REAL DEFAULT 0.0,
                category     TEXT DEFAULT 'none',
                action       TEXT DEFAULT 'skip',
                reason       TEXT DEFAULT '',
                risk_score   REAL DEFAULT 0.0,
                decided_at   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_feedback (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id      TEXT NOT NULL,
                decision_id  INTEGER REFERENCES agent_decisions(id),
                was_correct  INTEGER NOT NULL,   -- 1=correct, 0=wrong (false positive)
                note         TEXT DEFAULT '',
                feedback_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS learned_patterns (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_text TEXT UNIQUE NOT NULL,
                category     TEXT DEFAULT 'copyright',
                hit_count    INTEGER DEFAULT 1,
                confirmed    INTEGER DEFAULT 0,   -- 1 = user confirmed
                last_seen    TEXT NOT NULL
            );
        """)
        self.conn.commit()

    # ── Record agent decision ──────────────────────────────────────────────

    def record_decision(
        self,
        post_id: str,
        method: str,
        confidence: float,
        category: str,
        action: str,
        reason: str,
        account_uid: str = "",
        risk_score: float = 0.0,
    ) -> int:
        """Lưu quyết định của agent. Trả về decision id."""
        now = datetime.now().isoformat()
        with self._db_lock:
            cur = self.conn.execute(
                """INSERT INTO agent_decisions
                   (post_id, account_uid, method, confidence, category, action, reason, risk_score, decided_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (post_id, account_uid, method, confidence, category, action, reason, risk_score, now),
            )
            self.conn.commit()
            return cur.lastrowid

    # ── User feedback ──────────────────────────────────────────────────────

    def record_feedback(
        self,
        post_id: str,
        was_correct: bool,
        decision_id: Optional[int] = None,
        note: str = "",
    ):
        """
        Ghi nhận phản hồi người dùng.
        was_correct=False → false positive (bài bị xóa nhầm).
        """
        now = datetime.now().isoformat()
        with self._db_lock:
            self.conn.execute(
                """INSERT INTO user_feedback (post_id, decision_id, was_correct, note, feedback_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (post_id, decision_id, int(was_correct), note, now),
            )
            self.conn.commit()
        status = "CORRECT" if was_correct else "FALSE POSITIVE"
        log.info(f"Feedback recorded: post={post_id} [{status}]")

    # ── Accuracy stats ──────────────────────────────────────────────────────

    def get_accuracy_stats(self) -> dict:
        """
        Thống kê tỷ lệ chính xác theo method và category.
        Trả về dict với breakdown chi tiết.
        """
        with self._db_lock:
            cur = self.conn.execute("""
                SELECT
                    d.method,
                    d.category,
                    COUNT(f.id) AS total_feedback,
                    SUM(f.was_correct) AS correct,
                    COUNT(f.id) - SUM(f.was_correct) AS false_positives
                FROM agent_decisions d
                JOIN user_feedback f ON f.decision_id = d.id
                GROUP BY d.method, d.category
            """)
            rows = cur.fetchall()

            total_decisions = self.conn.execute(
                "SELECT COUNT(*) FROM agent_decisions"
            ).fetchone()[0]
            total_feedback = self.conn.execute(
                "SELECT COUNT(*), SUM(was_correct) FROM user_feedback"
            ).fetchone()

        breakdown = []
        for method, category, total_fb, correct, fp in rows:
            acc = ((correct or 0) / total_fb * 100) if total_fb else 0
            breakdown.append({
                "method": method,
                "category": category,
                "total_feedback": total_fb,
                "correct": correct,
                "false_positives": fp,
                "accuracy_pct": round(acc, 1),
            })

        overall_fb, overall_correct = total_feedback or (0, 0)
        overall_acc = ((overall_correct or 0) / overall_fb * 100) if overall_fb else None

        return {
            "total_decisions": total_decisions,
            "total_feedback": overall_fb or 0,
            "overall_accuracy_pct": round(overall_acc, 1) if overall_acc is not None else None,
            "breakdown": breakdown,
        }

    # ── Pattern learning ────────────────────────────────────────────────────

    def update_patterns(self, text: str, category: str, confirmed: bool = False):
        """
        Trích xuất và lưu text patterns từ bài vi phạm đã xác nhận.
        Mỗi câu/cụm từ ≥ 10 chars được lưu như 1 pattern.
        """
        now = datetime.now().isoformat()
        # Tách thành các đoạn ngắn (câu hoặc dòng)
        fragments = [
            s.strip() for s in text.replace("\n", ". ").split(". ")
            if 10 <= len(s.strip()) <= 200
        ]
        with self._db_lock:
            for frag in fragments[:20]:  # giới hạn 20 pattern / lần
                self.conn.execute("""
                    INSERT INTO learned_patterns (pattern_text, category, hit_count, confirmed, last_seen)
                    VALUES (?, ?, 1, ?, ?)
                    ON CONFLICT(pattern_text) DO UPDATE SET
                        hit_count = hit_count + 1,
                        confirmed = MAX(confirmed, excluded.confirmed),
                        last_seen = excluded.last_seen
                """, (frag, category, int(confirmed), now))
            self.conn.commit()

    def get_top_patterns(self, limit: int = 50) -> list[dict]:
        """Trả về các pattern phổ biến nhất đã được xác nhận."""
        with self._db_lock:
            rows = self.conn.execute("""
                SELECT pattern_text, category, hit_count, confirmed
                FROM learned_patterns
                WHERE confirmed = 1
                ORDER BY hit_count DESC
                LIMIT ?
            """, (limit,)).fetchall()
        return [
            {"pattern": r[0], "category": r[1], "hits": r[2], "confirmed": bool(r[3])}
            for r in rows
        ]

    def close(self):
        self.conn.close()


# Singleton
_memory: Optional[AgentMemory] = None
_mem_lock = __import__("threading").Lock()

def get_memory() -> AgentMemory:
    global _memory
    with _mem_lock:
        if _memory is None:
            _memory = AgentMemory()
    return _memory
