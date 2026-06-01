"""
Tầng 5 — API-first
FastAPI REST server + WebSocket log streaming.
Chạy bằng: python main.py api  (hoặc uvicorn api.server:app --reload)
"""
import asyncio
import json
import queue
import threading
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from modules.account_manager import get_manager
from modules.database import Database
from modules.logger import get_logger
from agent.memory import get_memory

log = get_logger(__name__)

app = FastAPI(
    title="FB Copyright Checker — Agent API",
    description="REST API để điều khiển AI agent kiểm tra vi phạm bản quyền Facebook",
    version = "v1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Shared agent state ──────────────────────────────────────────────────────

class AgentState:
    def __init__(self):
        self.status: str = "idle"      # idle | scanning | error
        self.last_scan_at: Optional[str] = None
        self.last_result: Optional[dict] = None
        self.scan_queue: queue.Queue = queue.Queue()
        self.log_subscribers: list[asyncio.Queue] = []
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_status(self, status: str):
        with self._lock:
            self.status = status
        self._broadcast_log(f"[status] {status}")

    def _broadcast_log(self, line: str):
        msg = {"ts": datetime.now().isoformat(), "msg": line}
        dead = []
        for q in list(self.log_subscribers):  # snapshot để tránh concurrent modify
            try:
                if self._loop and self._loop.is_running():
                    self._loop.call_soon_threadsafe(q.put_nowait, msg)
                else:
                    q.put_nowait(msg)
            except Exception:
                dead.append(q)
        for q in dead:
            try:
                self.log_subscribers.remove(q)
            except ValueError:
                pass


_state = AgentState()


# ── Pydantic models ─────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    account_id: Optional[str] = None   # uid hoặc email; None = semua account
    auto_delete: bool = False

class FeedbackRequest(BaseModel):
    was_correct: bool
    note: str = ""


@app.on_event("startup")
async def _on_startup():
    _state._loop = asyncio.get_event_loop()


# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/status")
def get_status():
    """Trạng thái hiện tại của agent và thống kê accuracy."""
    mem = get_memory()
    return {
        "agent_status": _state.status,
        "last_scan_at": _state.last_scan_at,
        "last_result": _state.last_result,
        "accuracy": mem.get_accuracy_stats(),
    }


@app.get("/accounts")
def list_accounts():
    """Danh sách tất cả tài khoản đã thêm."""
    manager = get_manager()
    return [
        {
            "index": i,
            "uid": a.uid,
            "email": a.email,
            "display_name": a.display_name,
            "profile_url": a.profile_url,
            "fanpage_count": len(a.fanpages),
            "active": a.active,
        }
        for i, a in enumerate(manager.get_all())
    ]


@app.post("/scan")
def trigger_scan(req: ScanRequest):
    """
    Kích hoạt quét một hoặc tất cả accounts.
    Trả về ngay (async); kết quả xem tại /status hoặc WebSocket /ws/logs.
    """
    with _state._lock:
        if _state.status == "scanning":
            raise HTTPException(409, "Đang có scan đang chạy. Vui lòng đợi.")
        _state.status = "scanning"

    # Chạy trong thread nền
    thread = threading.Thread(
        target=_run_scan_task, args=(req,), daemon=True, name="scan-worker"
    )
    thread.start()

    return {"message": "Scan started", "account_id": req.account_id, "auto_delete": req.auto_delete}


def _run_scan_task(req: ScanRequest):
    """Chạy trong background thread — thực hiện scan và cập nhật state."""
    # status đã được set thành "scanning" từ trigger_scan (bên trong _lock)
    try:
        from modules.fb_login import login
        from modules.copyright_checker import run_full_copyright_check
        from modules.account_manager import get_manager

        manager = get_manager()
        accounts = manager.get_all()

        if req.account_id:
            accounts = [
                a for a in accounts
                if a.uid == req.account_id or a.email == req.account_id
            ]
            if not accounts:
                raise ValueError(f"Account không tìm thấy: {req.account_id}")

        db = Database()
        all_results = {"total_appeals": 0, "deleted": 0, "accounts": []}

        try:
            for acc in accounts:
                try:
                    from agent.chrome_manager import ManagedChromeProfile
                    from agent.act import build_driver_for_account, chrome_profile_dir as get_profile_dir

                    uid = acc.uid or acc.email
                    profile_dir = get_profile_dir(uid)

                    with ManagedChromeProfile(profile_dir) as managed:
                        try:
                            driver = build_driver_for_account(uid)
                        except Exception as drv_err:
                            log.error(f"Không tạo được driver cho {acc.display_name}: {drv_err}")
                            continue
                        managed._driver = driver  # context manager sẽ quit + đóng profile khi xong

                        # Override config tạm để login đúng account
                        from modules.config_loader import CONFIG
                        _orig = dict(CONFIG["facebook"])
                        CONFIG["facebook"]["email"]      = acc.email or acc.uid
                        CONFIG["facebook"]["password"]   = acc.password
                        CONFIG["facebook"]["2fa_secret"] = acc.secret_2fa

                        try:
                            if not login(driver):
                                log.error(f"Login failed for {acc.display_name}")
                                continue

                            fanpages = [{"name": p.get("name", ""), "url": p.get("url", "")}
                                        for p in (acc.fanpages or [])]

                            result = run_full_copyright_check(
                                driver, db, fanpages,
                                auto_delete=req.auto_delete,
                                account_name=acc.display_name,
                                log_callback=lambda msg: _state._broadcast_log(f"[{acc.display_name}] {msg}"),
                            )
                            all_results["total_appeals"] += result["total_appeals"]
                            all_results["deleted"]       += result["deleted"]
                            all_results["accounts"].append({
                                "account": acc.display_name,
                                **result,
                            })
                        finally:
                            CONFIG["facebook"].clear()
                            CONFIG["facebook"].update(_orig)
                    # ManagedChromeProfile.__exit__ tự quit driver + close_profile tại đây

                except Exception as e:
                    log.error(f"Scan error for {acc.display_name}: {e}")
        finally:
            db.close()
        _state.last_result = all_results
        _state.last_scan_at = datetime.now().isoformat()
        _state.set_status("idle")
    except Exception as e:
        log.error(f"Scan task fatal error: {e}", exc_info=True)
        _state.set_status("error")


@app.get("/violations")
def list_violations():
    """
    Danh sách bài viết vi phạm đang chờ xét duyệt (action=queue_review).
    """
    mem = get_memory()
    with mem._db_lock:
        rows = mem.conn.execute("""
            SELECT d.id, d.post_id, d.confidence, d.category, d.reason,
                   d.action, d.risk_score, d.decided_at, d.account_uid,
                   p.url, p.content
            FROM agent_decisions d
            LEFT JOIN posts p ON p.post_id = d.post_id
            WHERE d.action = 'queue_review'
              AND NOT EXISTS (
                  SELECT 1 FROM user_feedback f WHERE f.decision_id = d.id
              )
            ORDER BY d.decided_at DESC
            LIMIT 100
        """).fetchall()

    return [
        {
            "id": r[0], "post_id": r[1], "confidence": r[2],
            "category": r[3], "reason": r[4], "action": r[5],
            "risk_score": r[6], "decided_at": r[7], "account_uid": r[8],
            "post_url": r[9] or "", "content_preview": (r[10] or "")[:200],
        }
        for r in rows
    ]


@app.post("/violations/{decision_id}/approve")
def approve_violation(decision_id: int, req: FeedbackRequest):
    """
    Xác nhận đây là vi phạm thật → agent sẽ tiến hành xóa + ghi feedback correct.
    """
    mem = get_memory()
    with mem._db_lock:
        row = mem.conn.execute(
            "SELECT post_id, category, reason FROM agent_decisions WHERE id=?",
            (decision_id,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "Không tìm thấy decision")

    post_id, category, reason = row
    mem.record_feedback(post_id, was_correct=True, decision_id=decision_id, note=req.note)

    # Học pattern từ bài đã xác nhận
    db = Database()
    try:
        posts = db.conn.execute("SELECT content FROM posts WHERE post_id=?", (post_id,)).fetchone()
        if posts and posts[0]:
            mem.update_patterns(posts[0], category=category, confirmed=True)
    finally:
        db.close()

    log.info(f"Violation approved: decision_id={decision_id}, post_id={post_id}")
    return {"message": "Đã xác nhận vi phạm. Agent sẽ xóa bài.", "post_id": post_id}


@app.post("/violations/{decision_id}/reject")
def reject_violation(decision_id: int, req: FeedbackRequest):
    """
    Đánh dấu false positive → agent học không nên xóa loại bài này.
    """
    mem = get_memory()
    with mem._db_lock:
        row = mem.conn.execute(
            "SELECT post_id FROM agent_decisions WHERE id=?", (decision_id,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "Không tìm thấy decision")

    post_id = row[0]
    mem.record_feedback(post_id, was_correct=False, decision_id=decision_id, note=req.note)
    log.info(f"False positive recorded: decision_id={decision_id}, post_id={post_id}")
    return {"message": "Đã đánh dấu false positive. Agent sẽ học từ phản hồi này.", "post_id": post_id}


@app.get("/stats/patterns")
def get_patterns():
    """Top 50 text pattern vi phạm đã học được từ user feedback."""
    mem = get_memory()
    return mem.get_top_patterns(50)


# ── WebSocket: real-time log stream ─────────────────────────────────────────

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """
    Stream log lines real-time đến client.
    Mỗi message là JSON: {"ts": "...", "msg": "..."}
    """
    await websocket.accept()
    log_queue: asyncio.Queue = asyncio.Queue(maxsize=200)
    _state.log_subscribers.append(log_queue)
    log.info(f"WebSocket log subscriber connected ({len(_state.log_subscribers)} total)")
    try:
        while True:
            # Chờ message mới (timeout 30s để giữ connection alive)
            try:
                msg = await asyncio.wait_for(log_queue.get(), timeout=30)
                await websocket.send_text(json.dumps(msg, ensure_ascii=False))
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"ts": datetime.now().isoformat(), "msg": "__ping__"}))
    except WebSocketDisconnect:
        pass
    finally:
        try:
            _state.log_subscribers.remove(log_queue)
        except ValueError:
            pass
        log.info("WebSocket log subscriber disconnected")
