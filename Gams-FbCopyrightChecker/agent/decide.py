"""
Tầng 2 — Decision
Claude AI classifier phân loại vi phạm bản quyền với confidence + risk scoring.
Fallback về keyword matching nếu API key chưa cấu hình.
"""
import os
import json
import re
from dataclasses import dataclass
from functools import lru_cache

from modules.logger import get_logger
from agent.perceive import PageObservation

log = get_logger(__name__)

# Confidence thresholds
THRESHOLD_AUTO_DELETE  = 0.90   # tự động xóa
THRESHOLD_QUEUE_REVIEW = 0.60   # xếp hàng chờ người duyệt
# dưới 0.60 → bỏ qua

# Risk: bài dưới N giờ hoặc có nhiều engagement → bắt buộc manual confirm
HIGH_RISK_AGE_HOURS   = 24
HIGH_RISK_ENGAGEMENT  = 100

_KEYWORDS = [
    "copyright", "bản quyền", "intellectual property", "quyền sở hữu trí tuệ",
    "dmca", "rights manager", "content removed", "nội dung bị xóa",
    "violated", "vi phạm", "removed", "đã xóa", "disabled", "bị vô hiệu",
]

_SYSTEM_PROMPT = """\
Bạn là hệ thống phân loại vi phạm bản quyền Facebook cho người dùng Việt Nam.
Nhiệm vụ: phân tích nội dung trang Appeals/Support của Facebook và xác định \
xem bài viết có thực sự vi phạm bản quyền không.

Trả lời CHÍNH XÁC theo JSON schema sau (không thêm text nào khác):
{
  "is_violation": true/false,
  "confidence": 0.0-1.0,
  "category": "copyright" | "dmca" | "rights_manager" | "ip_claim" | "none",
  "reason": "giải thích ngắn gọn tại sao",
  "action": "auto_delete" | "queue_review" | "skip"
}

Quy tắc action:
- confidence >= 0.90 AND is_violation=true  → "auto_delete"
- confidence >= 0.60 AND is_violation=true  → "queue_review"
- else → "skip"
"""


@dataclass
class Decision:
    is_violation: bool = False
    confidence: float = 0.0
    category: str = "none"
    reason: str = ""
    action: str = "skip"           # "auto_delete" | "queue_review" | "skip"
    method: str = "keyword"        # "claude" | "keyword"


def _keyword_classify(text: str) -> Decision:
    """Fallback classifier dựa trên keyword matching."""
    text_lower = text.lower()
    hits = [kw for kw in _KEYWORDS if kw in text_lower]
    if not hits:
        return Decision()
    confidence = min(0.50 + len(hits) * 0.08, 0.85)
    action = "queue_review" if confidence >= THRESHOLD_QUEUE_REVIEW else "skip"
    return Decision(
        is_violation=True,
        confidence=confidence,
        category="copyright",
        reason=f"Keyword matches: {', '.join(hits[:3])}",
        action=action,
        method="keyword",
    )


@lru_cache(maxsize=1)
def _get_anthropic_client():
    """Lazy-init Anthropic client (cached singleton)."""
    try:
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return None
        return anthropic.Anthropic(
            api_key=api_key,
            default_headers={
                "User-Agent": "claude-code/0.2.29",
                "Accept": "application/json"
            }
        )
    except ImportError:
        log.warning("anthropic package not installed. Using keyword fallback.")
        return None


def classify_violation(observation: PageObservation) -> Decision:
    """
    Phân loại vi phạm bản quyền từ PageObservation.
    Dùng Claude claude-haiku-4-5 nếu API key có sẵn, fallback về keyword.
    """
    client = _get_anthropic_client()
    if client is None:
        return _keyword_classify(observation.visible_text)

    try:
        # Build message content
        content: list = []

        # Nếu có screenshot → gửi kèm để Claude Vision phân tích UI
        if observation.screenshot_b64:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": observation.screenshot_b64,
                },
            })

        user_text = (
            f"URL: {observation.url}\n"
            f"Title: {observation.title}\n"
            f"Page type: {observation.page_type}\n\n"
            f"Nội dung trang (3000 ký tự đầu):\n{observation.visible_text}"
        )
        content.append({"type": "text", "text": user_text})

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=256,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},  # prompt cache
                }
            ],
            messages=[{"role": "user", "content": content}],
        )

        raw = response.content[0].text.strip() if response.content else ""
        if not raw:
            raise ValueError("Empty response from Claude API")
        # Parse JSON từ response
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            raise ValueError(f"No JSON in response: {raw[:200]}")

        data = json.loads(json_match.group())
        d = Decision(
            is_violation=bool(data.get("is_violation", False)),
            confidence=float(data.get("confidence", 0.0)),
            category=data.get("category", "none"),
            reason=data.get("reason", ""),
            action=data.get("action", "skip"),
            method="claude",
        )
        log.info(f"Claude decision: {d.action} (conf={d.confidence:.2f}) — {d.reason[:80]}")
        return d

    except Exception as e:
        log.warning(f"Claude classifier error: {e} — falling back to keyword")
        return _keyword_classify(observation.visible_text)


def score_risk(post_url: str, post_age_hours: float = 999, engagement: int = 0) -> float:
    """
    Tính risk score 0.0–1.0.
    Bài quá mới hoặc có nhiều reaction → risk cao → cần manual confirm trước khi xóa.
    """
    score = 0.0
    if post_age_hours < HIGH_RISK_AGE_HOURS:
        score += 0.5 * (1 - post_age_hours / HIGH_RISK_AGE_HOURS)
    if engagement > HIGH_RISK_ENGAGEMENT:
        score += min(0.5, engagement / (HIGH_RISK_ENGAGEMENT * 10))
    return min(score, 1.0)


def should_auto_delete(decision: Decision, risk_score: float = 0.0) -> bool:
    """
    Trả về True nếu nên tự động xóa ngay.
    High-risk posts (risk >= 0.5) bắt buộc queue review dù confidence cao.
    """
    if decision.action != "auto_delete":
        return False
    if risk_score >= 0.5:
        log.info(f"High-risk post (risk={risk_score:.2f}) — downgrading to queue_review")
        return False
    return True
