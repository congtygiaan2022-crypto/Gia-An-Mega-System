import sqlite3
import os
import threading
from datetime import datetime

from modules.config_loader import CONFIG
from modules.logger import get_logger

log = get_logger(__name__)


class Database:
    def __init__(self):
        db_path = CONFIG["database"]["path"]
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()
        log.info(f"Database connected: {db_path}")

    def _init_tables(self):
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS posts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id     TEXT UNIQUE,
                url         TEXT,
                content     TEXT,
                status      TEXT DEFAULT 'active',
                flagged     INTEGER DEFAULT 0,
                created_at  TEXT,
                checked_at  TEXT
            );

            CREATE TABLE IF NOT EXISTS deleted_posts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id     TEXT,
                url         TEXT,
                reason      TEXT,
                deleted_at  TEXT
            );

            CREATE TABLE IF NOT EXISTS scan_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                scanned_at  TEXT,
                total        INTEGER,
                flagged      INTEGER,
                deleted      INTEGER
            );
            
            CREATE TABLE IF NOT EXISTS violations (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                account_uid  TEXT,
                context_name TEXT,
                title        TEXT,
                post_url     TEXT,
                status       TEXT,
                action       TEXT,
                detected_at  TEXT
            );
        """)
        self.conn.commit()

    def upsert_post(self, post_id: str, url: str, content: str):
        now = datetime.now().isoformat()
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO posts (post_id, url, content, created_at, checked_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(post_id) DO UPDATE SET
                    url = excluded.url,
                    content = excluded.content,
                    checked_at = excluded.checked_at
            """, (post_id, url, content, now, now))
            self.conn.commit()

    def flag_post(self, post_id: str):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("UPDATE posts SET flagged=1, status='flagged' WHERE post_id=?", (post_id,))
            self.conn.commit()
        log.warning(f"Post flagged: {post_id}")

    def record_deletion(self, post_id: str, url: str, reason: str):
        now = datetime.now().isoformat()
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO deleted_posts (post_id, url, reason, deleted_at)
                VALUES (?, ?, ?, ?)
            """, (post_id, url, reason, now))
            cur.execute("UPDATE posts SET status='deleted' WHERE post_id=?", (post_id,))
            self.conn.commit()
        log.info(f"Deletion recorded for post: {post_id}")

    def log_scan(self, total: int, flagged: int, deleted: int):
        now = datetime.now().isoformat()
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO scan_log (scanned_at, total, flagged, deleted)
                VALUES (?, ?, ?, ?)
            """, (now, total, flagged, deleted))
            self.conn.commit()

    def get_flagged_posts(self) -> list:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("SELECT post_id, url FROM posts WHERE flagged=1 AND status='flagged'")
            return cur.fetchall()

    def clear_violations(self, account_uid: str, context_name: str = None):
        with self._lock:
            cur = self.conn.cursor()
            if context_name:
                cur.execute("DELETE FROM violations WHERE account_uid = ? AND context_name = ?", (account_uid, context_name))
            else:
                cur.execute("DELETE FROM violations WHERE account_uid = ?", (account_uid,))
            self.conn.commit()

    def save_violations(self, account_uid: str, context_name: str, appeals: list[dict]):
        now = datetime.now().isoformat()
        with self._lock:
            cur = self.conn.cursor()
            for ap in appeals:
                cur.execute("""
                    INSERT INTO violations (account_uid, context_name, title, post_url, status, action, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    account_uid,
                    context_name,
                    ap.get("title", ""),
                    ap.get("post_url", ""),
                    ap.get("status", ""),
                    ap.get("action", ""),
                    now
                ))
            self.conn.commit()

    def mark_violation_deleted(self, post_url: str):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("UPDATE violations SET status='deleted' WHERE post_url=?", (post_url,))
            self.conn.commit()
        log.info(f"Đã cập nhật trạng thái xóa cho violation: {post_url}")

    def get_violations(self, account_uid: str) -> list[dict]:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("SELECT context_name, title, post_url, status, action FROM violations WHERE account_uid = ? ORDER BY id ASC", (account_uid,))
            rows = cur.fetchall()
        return [
            {
                "context": r[0],
                "title": r[1],
                "post_url": r[2],
                "status": r[3],
                "action": r[4]
            }
            for r in rows
        ]

    def remove_violation(self, post_url: str):
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM violations WHERE post_url = ?", (post_url,))
            self.conn.commit()

    def close(self):
        self.conn.close()
