"""
Quản lý nhiều tài khoản Facebook bằng SQLite.
"""
import base64
import json
import os
import sqlite3
from dataclasses import dataclass, field
from typing import Optional

from modules.logger import get_logger

log = get_logger(__name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(_BASE_DIR, "db")
DB_FILE = os.path.join(DB_DIR, "accounts.db")
OLD_JSON_FILE = os.path.join(_BASE_DIR, "accounts.json")

# --- Mã hóa đơn giản ---
_KEY = b"fbcopyright2025"

def _obfuscate(text: str) -> str:
    if not text: return ""
    raw = text.encode("utf-8")
    out = bytes([b ^ _KEY[i % len(_KEY)] for i, b in enumerate(raw)])
    return base64.b64encode(out).decode()

def _deobfuscate(enc: str) -> str:
    if not enc: return ""
    try:
        raw = base64.b64decode(enc.encode())
        return bytes([b ^ _KEY[i % len(_KEY)] for i, b in enumerate(raw)]).decode("utf-8")
    except Exception:
        return enc

@dataclass
class Account:
    id: int = -1
    uid: str = ""
    email: str = ""
    password: str = ""
    secret_2fa: str = ""
    label: str = ""
    profile_url: str = ""
    profile_name: str = ""
    fanpages: list = field(default_factory=list)
    active: bool = True

    @property
    def display_name(self) -> str:
        return self.label or self.profile_name or self.email or self.uid or "Chưa đặt tên"

    @classmethod
    def from_pipe_string(cls, line: str) -> Optional["Account"]:
        parts = [p.strip() for p in line.strip().split("|")]
        if len(parts) < 2: return None
        acc = cls()
        if "@" in parts[0] or not parts[0].isdigit() or len(parts[0]) < 5:
            acc.email = parts[0]
            acc.password = parts[1] if len(parts) > 1 else ""
            acc.secret_2fa = parts[2] if len(parts) > 2 else ""
            uid_part = parts[3] if len(parts) > 3 else ""
            if uid_part.isdigit(): acc.uid = uid_part
        else:
            acc.uid = parts[0]
            acc.password = parts[1] if len(parts) > 1 else ""
            acc.secret_2fa = parts[2] if len(parts) > 2 else ""
            acc.email = parts[3] if len(parts) > 3 else ""
        return acc

class AccountManager:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        self._migrate_old_json()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uid TEXT,
                    email TEXT,
                    password TEXT,
                    secret_2fa TEXT,
                    label TEXT,
                    profile_url TEXT,
                    profile_name TEXT,
                    fanpages TEXT,
                    active INTEGER
                )
            """)
            conn.commit()

    def _migrate_old_json(self):
        if not os.path.exists(OLD_JSON_FILE): return
        # only migrate if table is empty
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM accounts")
            if cur.fetchone()[0] > 0:
                return
        
        try:
            with open(OLD_JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            migrated = 0
            for d in data:
                acc = Account(
                    uid=d.get("uid", ""),
                    email=d.get("email", ""),
                    password=_deobfuscate(d.get("password", "")),
                    secret_2fa=_deobfuscate(d.get("secret_2fa", "")),
                    label=d.get("label", ""),
                    profile_url=d.get("profile_url", ""),
                    profile_name=d.get("profile_name", ""),
                    fanpages=d.get("fanpages", []),
                    active=d.get("active", True)
                )
                self.add(acc)
                migrated += 1
            log.info(f"Migrated {migrated} accounts from JSON to SQLite")
            # Rename old json to avoid re-migration
            os.rename(OLD_JSON_FILE, OLD_JSON_FILE + ".bak")
        except Exception as e:
            log.error(f"Migration error: {e}")

    def _row_to_account(self, row) -> Account:
        return Account(
            id=row[0],
            uid=row[1],
            email=row[2],
            password=_deobfuscate(row[3]),
            secret_2fa=_deobfuscate(row[4]),
            label=row[5],
            profile_url=row[6],
            profile_name=row[7],
            fanpages=json.loads(row[8]) if row[8] else [],
            active=bool(row[9])
        )

    def add(self, acc: Account) -> bool:
        key = acc.uid or acc.email
        if key:
            all_accs = self.get_all()
            if any((a.uid == acc.uid and acc.uid) or (a.email == acc.email and acc.email) for a in all_accs):
                log.warning(f"Tài khoản đã tồn tại: {key}")
                return False
        
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO accounts (uid, email, password, secret_2fa, label, profile_url, profile_name, fanpages, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                acc.uid, acc.email, _obfuscate(acc.password), _obfuscate(acc.secret_2fa),
                acc.label, acc.profile_url, acc.profile_name,
                json.dumps(acc.fanpages, ensure_ascii=False),
                1 if acc.active else 0
            ))
            conn.commit()
            acc.id = cur.lastrowid
        return True

    def update(self, index: int, acc: Account):
        all_accs = self.get_all()
        if 0 <= index < len(all_accs):
            target_id = all_accs[index].id
            self.update_by_id(target_id, acc)

    def update_by_id(self, db_id: int, acc: Account):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE accounts SET
                    uid=?, email=?, password=?, secret_2fa=?, label=?,
                    profile_url=?, profile_name=?, fanpages=?, active=?
                WHERE id=?
            """, (
                acc.uid, acc.email, _obfuscate(acc.password), _obfuscate(acc.secret_2fa),
                acc.label, acc.profile_url, acc.profile_name,
                json.dumps(acc.fanpages, ensure_ascii=False),
                1 if acc.active else 0, db_id
            ))
            conn.commit()

    def remove(self, index: int):
        all_accs = self.get_all()
        if 0 <= index < len(all_accs):
            target_id = all_accs[index].id
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM accounts WHERE id=?", (target_id,))
                conn.commit()
            log.info(f"Đã xóa tài khoản: {all_accs[index].display_name}")

    def get_all(self) -> list[Account]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM accounts ORDER BY id ASC")
            rows = cur.fetchall()
            return [self._row_to_account(r) for r in rows]

    def get(self, index: int) -> Optional[Account]:
        all_accs = self.get_all()
        if 0 <= index < len(all_accs):
            return all_accs[index]
        return None

    def update_profile(self, index: int, profile: dict, fanpages: list):
        acc = self.get(index)
        if acc:
            acc.profile_url = profile.get("profile_url", acc.profile_url)
            acc.profile_name = profile.get("name", acc.profile_name)
            acc.uid = profile.get("uid", acc.uid) or acc.uid
            acc.fanpages = fanpages
            self.update(index, acc)

    def import_from_text(self, text: str) -> tuple[int, int]:
        added = skipped = 0
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            acc = Account.from_pipe_string(line)
            if acc and (acc.uid or acc.email):
                if self.add(acc):
                    added += 1
                else:
                    skipped += 1
        log.info(f"Import: +{added} mới, {skipped} trùng")
        return added, skipped

    def export_to_text(self) -> str:
        lines = []
        for a in self.get_all():
            lines.append(f"{a.uid}|{a.password}|{a.secret_2fa}|{a.email}")
        return "\n".join(lines)


_manager: Optional[AccountManager] = None

def get_manager() -> AccountManager:
    global _manager
    if _manager is None:
        _manager = AccountManager()
    return _manager
