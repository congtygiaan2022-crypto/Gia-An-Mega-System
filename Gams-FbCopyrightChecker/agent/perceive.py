"""
Tầng 1 — Perception
Quan sát trạng thái trang, chụp screenshot, phát JSON events, gửi webhook.
"""
import base64
import json
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import requests
from selenium import webdriver

from modules.config_loader import CONFIG
from modules.logger import get_logger

log = get_logger(__name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EVENTS_FILE = os.path.join(_BASE_DIR, "logs", "events.jsonl")
_WRITE_LOCK = threading.Lock()


@dataclass
class PageObservation:
    url: str = ""
    title: str = ""
    visible_text: str = ""          # first 3000 chars
    screenshot_b64: str = ""        # base64 PNG, empty if not captured
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    page_type: str = "unknown"      # "profile", "fanpage", "appeals", "post", "other"


def capture_screenshot(driver: webdriver.Chrome) -> bytes:
    """Trả về PNG bytes của page hiện tại."""
    try:
        return driver.get_screenshot_as_png()
    except Exception as e:
        log.debug(f"Screenshot failed: {e}")
        return b""


def observe_page(driver: webdriver.Chrome, take_screenshot: bool = False) -> PageObservation:
    """
    Quan sát page hiện tại và trả về PageObservation structured.
    take_screenshot=True khi cần gửi cho Claude Vision.
    """
    obs = PageObservation()
    try:
        obs.url   = driver.current_url
        obs.title = driver.title or ""

        # Lấy text hiển thị (giới hạn để không tốn token)
        body_text = driver.find_element("tag name", "body").text
        obs.visible_text = body_text[:3000]

        # Phân loại page
        url = obs.url.lower()
        if "support" in url and "appeal" in url:
            obs.page_type = "appeals"
        elif "/posts/" in url or "story_fbid" in url:
            obs.page_type = "post"
        elif "/pages/" in url or "pageType=PROFESSIONAL" in url:
            obs.page_type = "fanpage"
        elif "/me" in url or driver.current_url.count("/") == 3:
            obs.page_type = "profile"

        if take_screenshot:
            png = capture_screenshot(driver)
            if png:
                obs.screenshot_b64 = base64.b64encode(png).decode()

    except Exception as e:
        log.debug(f"observe_page partial error: {e}")

    return obs


def emit_event(event_type: str, data: dict):
    """Ghi 1 dòng JSON vào logs/events.jsonl (thread-safe)."""
    log_dir = os.path.dirname(_EVENTS_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    record = {
        "ts": datetime.now().isoformat(),
        "event": event_type,
        **data,
    }
    with _WRITE_LOCK:
        with open(_EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def send_webhook(message: str, level: str = "info", extra: Optional[dict] = None):
    """
    Gửi notification đến webhook URL nếu được cấu hình.
    Hỗ trợ format Telegram bot (nếu URL có 'telegram') hoặc generic webhook.
    """
    cfg = CONFIG.get("notifications", {})
    url = cfg.get("webhook_url", "").strip()
    if not url:
        return

    payload: dict
    if "telegram" in url:
        chat_id = cfg.get("telegram_chat_id", "")
        payload = {
            "chat_id": chat_id,
            "text": f"[{level.upper()}] {message}",
            "parse_mode": "HTML",
        }
    else:
        payload = {
            "text": message,
            "level": level,
            **(extra or {}),
        }

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        log.warning(f"Webhook send failed: {e}")


def notify_violation_found(context: str, count: int, account: str = ""):
    """Tiện ích: phát event + gửi webhook khi tìm thấy vi phạm."""
    msg = f"🚨 [{account or context}] Phát hiện {count} vi phạm bản quyền"
    emit_event("violation_found", {"context": context, "count": count, "account": account})
    send_webhook(msg, level="warning")
    log.warning(msg)


def notify_deletion_done(count: int, total: int, account: str = ""):
    """Phát event + webhook khi hoàn thành xóa."""
    msg = f"✅ [{account}] Đã xóa {count}/{total} bài vi phạm"
    emit_event("deletion_done", {"deleted": count, "total": total, "account": account})
    send_webhook(msg, level="info")
    log.info(msg)
