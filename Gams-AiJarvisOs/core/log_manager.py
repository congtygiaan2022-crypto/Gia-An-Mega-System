import sqlite3
import os
import datetime

class LogManager:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "automation.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
        except Exception:
            pass
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS task_logs (
                        id TEXT PRIMARY KEY,
                        task_id TEXT,
                        task_name TEXT,
                        status TEXT,
                        start_time TEXT,
                        end_time TEXT
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS task_steps (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_log_id TEXT,
                        step_name TEXT,
                        status TEXT,
                        message TEXT,
                        timestamp TEXT,
                        FOREIGN KEY(task_log_id) REFERENCES task_logs(id)
                    )
                ''')
        finally:
            conn.close()

    def start_run(self, run_id, task_id, task_name):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO task_logs (id, task_id, task_name, status, start_time) VALUES (?, ?, ?, ?, ?)",
                    (run_id, task_id, task_name, "RUNNING", datetime.datetime.now().isoformat())
                )
        finally:
            conn.close()

    def log_step(self, run_id, step_name, status, message):
        """status: SUCCESS, ERROR, INFO"""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO task_steps (task_log_id, step_name, status, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (run_id, step_name, status, str(message), datetime.datetime.now().isoformat())
                )
        finally:
            conn.close()

    def finish_run(self, run_id, status):
        """status: SUCCESS, ERROR"""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    "UPDATE task_logs SET status = ?, end_time = ? WHERE id = ?",
                    (status, datetime.datetime.now().isoformat(), run_id)
                )
        finally:
            conn.close()

    def get_latest_runs(self, limit=50):
        conn = self._get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM task_logs ORDER BY start_time DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_run_steps(self, run_id):
        conn = self._get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM task_steps WHERE task_log_id = ? ORDER BY id ASC", (run_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def delete_run(self, run_id):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("DELETE FROM task_steps WHERE task_log_id = ?", (run_id,))
                conn.execute("DELETE FROM task_logs WHERE id = ?", (run_id,))
        finally:
            conn.close()

    def delete_task_runs(self, task_id):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("DELETE FROM task_steps WHERE task_log_id IN (SELECT id FROM task_logs WHERE task_id = ?)", (task_id,))
                conn.execute("DELETE FROM task_logs WHERE task_id = ?", (task_id,))
        finally:
            conn.close()

    def clear_all_runs(self):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("DELETE FROM task_steps")
                conn.execute("DELETE FROM task_logs")
        finally:
            conn.close()
