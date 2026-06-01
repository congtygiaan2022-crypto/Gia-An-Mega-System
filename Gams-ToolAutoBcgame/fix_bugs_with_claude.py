#!/usr/bin/env python3
"""
fix_bugs_with_claude.py
=======================
Script tự động:
  1. Đọc find_bug.md để lấy danh sách lỗi chưa sửa
  2. Gửi từng lỗi cho Claude Code (claude CLI) để phân tích và sửa
  3. Sau khi Claude sửa xong → gọi BugTracker.mark_fixed(bug_id)
     → Xóa khỏi find_bug.md và ghi vào fix_bug.md

Cách chạy:
    python fix_bugs_with_claude.py              # Xử lý tất cả lỗi trong find_bug.md
    python fix_bugs_with_claude.py --id BUG_X  # Chỉ xử lý một bug cụ thể
    python fix_bugs_with_claude.py --list       # Liệt kê lỗi chưa sửa
    python fix_bugs_with_claude.py --dry-run    # Xem prompt sẽ gửi Claude, không thực sự gửi
"""

import os
import re
import sys
import argparse
import subprocess
import textwrap

# ── Thêm root vào sys.path ─────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from core.bug_tracker import (
    BugTracker, FIND_BUG_FILE,
    _parse_bug_block,
)

# ═══════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════

def _load_open_bugs() -> list[dict]:
    """Đọc find_bug.md, trả về list {bug_id, block_text}."""
    if not os.path.exists(FIND_BUG_FILE):
        print("⚠️  find_bug.md chưa tồn tại.")
        return []

    content = open(FIND_BUG_FILE, encoding="utf-8").read()

    # Tách từng block bằng END_BUG marker
    blocks = re.findall(
        r"(##\s+🐛\s+\[(BUG_[^\]]+)\].*?<!--\s*END_BUG:\2\s*-->)",
        content, re.DOTALL
    )
    return [{"bug_id": b[1], "block": b[0]} for b in blocks]


def _build_claude_prompt(bug_id: str, block: str) -> str:
    """Xây dựng prompt để gửi Claude Code sửa bug."""
    entry = _parse_bug_block(block, bug_id)

    prompt = textwrap.dedent(f"""
    Bạn là một kỹ sư Python cao cấp đang bảo trì dự án Tool_auto_bcgame.
    Dự án sử dụng Selenium để tự động đặt cược trên BCGame.

    === LỖI CẦN SỬA ===
    - Bug ID    : {entry.bug_id}
    - Module    : {entry.module}
    - Tác vụ    : {entry.task}
    - Loại lỗi  : {entry.error_type}
    - Thông báo : {entry.error_message}
    - Mức độ    : {entry.severity}

    === TRACEBACK ===
    {entry.traceback_str or "Không có traceback"}

    === YÊU CẦU ===
    1. Đọc file nguồn liên quan trong thư mục dự án.
    2. Tìm nguyên nhân gốc rễ (root cause) của lỗi trên.
    3. Sửa lỗi trong file nguồn với giải thích ngắn gọn.
    4. Sau khi sửa xong, chạy lệnh Python sau để đánh dấu bug đã được sửa:

       python -c "from core.bug_tracker import mark_bug_fixed; mark_bug_fixed('{bug_id}', 'Mô tả ngắn về cách sửa')"

    ⚠️  QUAN TRỌNG: Bắt buộc phải chạy lệnh mark_bug_fixed ở trên sau khi sửa xong.
    """).strip()
    return prompt


def _call_claude_cli(prompt: str, bug_id: str, dry_run: bool = False) -> bool:
    """
    Gọi `claude` CLI với prompt, trả về True nếu thành công.
    Yêu cầu: Claude Code CLI đã được cài đặt (npm install -g @anthropic-ai/claude-code).
    """
    if dry_run:
        print("\n" + "="*60)
        print(f"[DRY-RUN] Prompt sẽ gửi cho Claude ({bug_id}):")
        print("="*60)
        print(prompt)
        print("="*60 + "\n")
        return True

    # Lưu prompt ra file tạm để truyền vào claude
    prompt_file = os.path.join(ROOT, f".claude_prompt_{bug_id}.txt")
    try:
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)

        print(f"\n🤖 Đang gọi Claude Code để sửa {bug_id}...")
        print("-" * 50)

        # Gọi claude CLI — stdin là prompt
        result = subprocess.run(
            ["claude", "--print", "--allowedTools", "Read,Write,Bash"],
            input=prompt,
            capture_output=False,       # hiện output lên màn hình
            text=True,
            encoding="utf-8",
            cwd=ROOT,
            timeout=300,                # 5 phút tối đa
        )

        if result.returncode == 0:
            print(f"✅ Claude xử lý {bug_id} thành công.")
            return True
        else:
            print(f"❌ Claude trả về lỗi (code {result.returncode}) cho {bug_id}.")
            return False

    except FileNotFoundError:
        print("❌ Không tìm thấy lệnh `claude`. Hãy cài đặt Claude Code CLI:")
        print("   npm install -g @anthropic-ai/claude-code")
        return False
    except subprocess.TimeoutExpired:
        print(f"⏰ Claude vượt quá thời gian xử lý cho {bug_id}.")
        return False
    except Exception as e:
        print(f"❌ Lỗi gọi Claude: {e}")
        return False
    finally:
        if os.path.exists(prompt_file):
            os.remove(prompt_file)


def _print_bug_list(bugs: list[dict]):
    """In danh sách lỗi ra terminal."""
    if not bugs:
        print("✨ Không có lỗi nào trong find_bug.md!")
        return

    print(f"\n{'='*60}")
    print(f"  🐛 Có {len(bugs)} lỗi chưa sửa trong find_bug.md")
    print(f"{'='*60}")
    for b in bugs:
        entry = _parse_bug_block(b["block"], b["bug_id"])
        print(f"  [{entry.severity:8s}] {b['bug_id']:28s} | {entry.module} → {entry.task}")
    print(f"{'='*60}\n")


# ═══════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Tự động sửa bug bằng Claude Code"
    )
    parser.add_argument("--id",      metavar="BUG_ID", help="Chỉ sửa một bug cụ thể")
    parser.add_argument("--list",    action="store_true", help="Liệt kê lỗi chưa sửa")
    parser.add_argument("--dry-run", action="store_true", help="Xem prompt, không gửi Claude")
    parser.add_argument("--mark",    metavar="BUG_ID", help="Đánh dấu thủ công một bug đã sửa")
    parser.add_argument("--note",    metavar="NOTE",   help="Ghi chú khi dùng --mark")
    args = parser.parse_args()

    # ── --mark: Đánh dấu thủ công ───────────────────────────────────
    if args.mark:
        ok = BugTracker.mark_fixed(args.mark, args.note or "Đánh dấu thủ công bởi developer.")
        if ok:
            print(f"✅ Đã đánh dấu {args.mark} là đã sửa.")
        else:
            print(f"❌ Không tìm thấy {args.mark} trong find_bug.md.")
        return

    # ── Đọc danh sách bug ───────────────────────────────────────────
    all_bugs = _load_open_bugs()

    # ── --list ───────────────────────────────────────────────────────
    if args.list:
        _print_bug_list(all_bugs)
        return

    if not all_bugs:
        print("✨ Không có lỗi nào cần sửa. find_bug.md trống!")
        return

    # ── Lọc theo --id ────────────────────────────────────────────────
    if args.id:
        all_bugs = [b for b in all_bugs if b["bug_id"] == args.id]
        if not all_bugs:
            print(f"❌ Không tìm thấy bug_id={args.id} trong find_bug.md.")
            return

    _print_bug_list(all_bugs)

    # ── Xử lý từng bug ──────────────────────────────────────────────
    success_count = 0
    fail_count    = 0

    for bug in all_bugs:
        bug_id = bug["bug_id"]
        block  = bug["block"]

        print(f"\n{'─'*50}")
        print(f"🔧 Đang xử lý: {bug_id}")
        print(f"{'─'*50}")

        prompt = _build_claude_prompt(bug_id, block)
        ok     = _call_claude_cli(prompt, bug_id, dry_run=args.dry_run)

        if ok and not args.dry_run:
            # Kiểm tra xem Claude đã tự gọi mark_fixed chưa
            # Nếu bug_id vẫn còn trong file → Claude chưa gọi, ta tự gọi
            remaining = _load_open_bugs()
            still_open = any(b["bug_id"] == bug_id for b in remaining)
            if still_open:
                print(f"ℹ️  Claude chưa tự mark_fixed → Đang tự đánh dấu {bug_id}...")
                BugTracker.mark_fixed(bug_id, "Claude Code đã sửa (auto-mark).")
            success_count += 1
        elif not ok:
            fail_count += 1

    # ── Tổng kết ─────────────────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"📊 Kết quả: ✅ {success_count} sửa thành công | ❌ {fail_count} thất bại")
    print("📄 Xem kết quả trong: fix_bug.md")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
