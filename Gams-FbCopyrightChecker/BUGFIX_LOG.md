# BUGFIX LOG — fb_copyright_checker

## [2026-05-22 13:55] Lần 19 — TOCTOU race /scan, dead queue, hash sai

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `api/server.py` dòng 129–132 | CRITICAL | `if _state.status == "scanning"` đọc không có lock → 2 request đồng thời đều thấy `"idle"`, cả 2 đều start scan thread song song → 2 Chrome tranh tài nguyên, crash hoặc kết quả sai (TOCTOU race) | Bọc check + set trong `with _state._lock:`; xóa `_state.set_status("scanning")` khỏi `_run_scan_task` (đã set từ endpoint) |
| `api/server.py` dòng 132 | MEDIUM | `_state.scan_queue.put(req)` — `req` được truyền trực tiếp vào thread argument, không ai đọc queue → mỗi POST `/scan` tích lũy 1 item vào queue không bao giờ được drain (memory leak) | Xóa dòng `scan_queue.put(req)` |
| `ai_runner.py` dòng 398 | HIGH | `hashlib.md5(stderr.encode(...))` — khi crash không có stderr (lỗi chỉ ở stdout), `stderr=""` → hash `md5("")` giống nhau cho tất cả crash loại này → lần crash thứ 2 (dù khác lỗi) bị nhận nhầm là "loop", `sys.exit(1)` bỏ qua 4 lần retry còn lại | Đổi thành `hashlib.md5(full_output.encode(...))` |

## [2026-05-22 13:25] Lần 18 — SQLite read lock trong AgentMemory

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `agent/memory.py` `get_accuracy_stats()` dòng 128–146 | HIGH | Ba lần `self.conn.execute()` không có `_db_lock` — khi scan thread đang INSERT và `commit()` bên trong lock, FastAPI handler gọi đồng thời → `OperationalError: database is locked`. Ngoài ra 3 query không trong cùng transaction → stats inconsistent | Bọc toàn bộ 3 execute + fetchall trong `with self._db_lock:` |
| `agent/memory.py` `get_top_patterns()` dòng 197–203 | HIGH | Cùng vấn đề — `self.conn.execute()` không có lock, gọi từ FastAPI thread đồng thời với scan worker | Bọc trong `with self._db_lock:` |

## [2026-05-22 12:55] Lần 17 — Data loss khi edit account, item_action sai, asyncio thread-safety

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `gui/dashboard.py` `_save()` dòng 233–236 | HIGH | Khi edit tài khoản, `Account(**data, fanpages=...)` chỉ preserve `fanpages` nhưng `profile_url`, `profile_name`, `active` bị reset về default → mỗi lần Save mất URL profile đã fetch + reset trạng thái active | Preserve đủ 4 field: `profile_url`, `profile_name`, `active`, `fanpages` từ `existing` |
| `modules/copyright_checker.py` dòng 309 | HIGH | `item_action = "auto_delete"` hardcoded → tất cả keyword-match items được ghi vào DB với `action='auto_delete'` → endpoint `/violations` chỉ query `WHERE action='queue_review'` → không bao giờ thấy bài vi phạm trong review queue khi `auto_delete=False` | Đổi thành `item_action = "queue_review"` — xóa hay không do caller (`run_full_copyright_check`) kiểm soát qua flag `auto_delete` |
| `api/server.py` `_broadcast_log` dòng 53–64 | HIGH | `asyncio.Queue.put_nowait()` gọi từ background thread (`_run_scan_task`) — asyncio không thread-safe → WebSocket consumer `await log_queue.get()` có thể không được đánh thức; đồng thời mutate `log_subscribers` list từ 2 thread → data race | Thêm `self._loop` field; dùng `loop.call_soon_threadsafe(q.put_nowait, msg)` khi loop đang chạy; snapshot list với `list(self.log_subscribers)`; set `_state._loop` trong `@app.on_event("startup")` |

## [2026-05-22 12:30] Lần 16 — TypeError SUM NULL, CONFIG leak, fanpages data loss

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `agent/memory.py` dòng 150 | HIGH | `correct / total_fb * 100` — `correct` từ `SUM(was_correct)` có thể `None` khi tất cả feedback là `was_correct=0` → SQLite trả `NULL` → TypeError khi chia | Đổi thành `(correct or 0) / total_fb * 100` |
| `api/server.py` dòng 180–202 | HIGH | CONFIG ("email", "password", "2fa_secret") được override trước `login()` nhưng `_orig` chỉ được restore ở 2 nhánh "login fail" và "login ok" — nếu `run_full_copyright_check()` raise exception thì `except` block ở ngoài bắt và `continue` mà không restore → CONFIG bị nhiễm credentials account cũ cho các account scan tiếp theo | Bọc toàn bộ `login + run_full_copyright_check` trong `try/finally`, restore `_orig` trong `finally` |
| `gui/dashboard.py` dòng 229–244 | MEDIUM | `Account(**{k: v.get().strip() for k, v in fields.items()})` — form chỉ có 5 trường (label, email, password, secret_2fa, uid), không có `fanpages` → khi edit account, `fanpages` bị overwrite bởi `[]` (default), xóa sạch danh sách fanpage đã lưu | Lấy `existing = mgr.get(edit_idx)` rồi `Account(**data, fanpages=existing.fanpages if existing else [])` khi edit |
| `scratch` / `scripts` files | LOW | Flake8 lint (F401, F541, E722): `time`/`By`/`sys` không dùng trong debug scripts; f-string thiếu placeholder trong download_chrome.py; bare except trong test_login_dom.py | Fix theo từng file |

## [2026-05-22 12:07] Lần 15 — Lint fix + race condition API

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `dump_support.py` dòng 1 | MEDIUM | `import os, sys, time, json` — E401 + F401 (`json` không dùng) | Tách thành `import os`, `import sys`, `import time`; xóa `json` |
| `dump_support.py` dòng 5 | MEDIUM | `from selenium.webdriver.common.by import By` — F401, `By` không dùng trong file này | Xóa dòng import |
| `modules/copyright_checker.py` dòng 202 | LOW | `except Exception as e: pass` — F841 biến `e` không dùng | Đổi thành `except Exception: pass` |
| `api/server.py` dòng 222, 253, 282 | HIGH | `mem.conn.execute()` trong `/violations`, `/approve`, `/reject` gọi trực tiếp mà không có `mem._db_lock` — trong khi `_run_scan_task` đang write/commit qua lock ở thread khác → dirty read hoặc `sqlite3.OperationalError: database is locked` | Bọc mỗi `mem.conn.execute(...).fetchone/all()` trong `with mem._db_lock:` |

## [2026-05-22] Lần 1

| File | Dòng (gốc) | Loại | Nội dung gốc | Sửa thành |
|------|-----------|------|--------------|-----------|
| ai_runner.py | 363 | F541 | `f"[SUCCESS] Error Report: Compiled and saved to last_error.json"` | `"[SUCCESS] Error Report: Compiled and saved to last_error.json"` (bỏ tiền tố `f`) |
| ai_runner.py | 383 | F541 | `log_info(f"\n" + "="*30 + f" ATTEMPT ...")` — phần `f"\n"` thiếu placeholder | `log_info("\n" + "="*30 + f" ATTEMPT {attempt}/{MAX_RETRIES} " + "="*30)` (bỏ `f` trước `"\n"`) |
| modules/two_factor.py | 66 | F541 | `f"\n[OK] Đã lưu secret key."` | `"\n[OK] Đã lưu secret key."` (bỏ tiền tố `f`) |
| run_e2e_test.py | 130 | F541 | `f'\nKết quả:'` | `'\nKết quả:'` (bỏ tiền tố `f`) |

## [2026-05-22] Lần 2 — Bug chức năng

| File | Bug ID | Mức độ | Mô tả | Sửa thành |
|------|--------|--------|-------|-----------|
| modules/fb_profile.py | BUG-001 | CRITICAL | `get_fanpages()` — chỉ cuộn 2 lần → chỉ thấy ~14/78 fanpage | Thay bằng vòng lặp thông minh tối đa 15 lần, dừng khi số card ổn định, sleep 1.5s |
| modules/fb_profile.py | BUG-001b | CRITICAL | `_get_pages_via_manage_url()` — cùng lỗi cuộn 2 lần | Thay bằng vòng lặp thông minh tối đa 15 lần, dừng khi số anchor ổn định |
| modules/copyright_checker.py | BUG-005 | MEDIUM | `switch_context_via_menu()` — except không có `return False` → trả về `None` thay vì `False` | Thêm `return False` cuối except block |
| api/server.py | 8 | F401 | `import os` | Xóa (không dùng) |
| api/server.py | 11 | F401 | `import time` | Xóa (không dùng) |
| api/server.py | 20 | F401/F811 | `from modules.config_loader import CONFIG` (top-level) | Xóa; CONFIG được re-import cục bộ bên trong hàm `_run_scan_task` |
| api/server.py | 143 | F811 | `from agent.act import build_driver_for_account` (lần 1) | Xóa; dòng 162 đã import lại cùng tên kèm `chrome_profile_dir` |
| gui/dashboard.py | 835 | E722 | `except: pass` | `except Exception: pass` |
| gui/dashboard.py | 877 | E722 | `except:` | `except Exception:` |
| gui/dashboard.py | 1001 | E722 | `except:` | `except Exception:` |
| gui/dashboard.py | 1029 | E722 | `except: pass` | `except Exception: pass` |
| modules/fb_profile.py | 122 | E722 | `except:` | `except Exception:` |

## [2026-05-22] Lần 2 (bổ sung)

| File | Loại | Sửa |
|------|------|-----|
| agent/act.py | F401 | Xóa `import sys` |
| agent/chrome_manager.py | F401 | Xóa `import signal` |
| agent/decide.py | F401 | Xóa `time`, `Optional`, `CONFIG` (top-level) + `import anthropic` (local, không dùng) |
| agent/memory.py | F401 | Xóa `import json` |
| agent/perceive.py | F401 | Xóa `io`, `time`, `asdict` |
| gui/dashboard.py | F401 | Xóa local `from dataclasses import asdict` không dùng |
| gui/dashboard.py | E722 | Sửa `except:` → `except Exception:` trong on_close |
| main.py | F401 | Xóa `import os` |
| modules/account_manager.py | F401 | Xóa `import re` |
| modules/delete_post.py | F401 | Xóa `CONFIG` import |
| modules/post_scanner.py | F401 | Xóa `WebDriverWait`, `EC` |

## [2026-05-22] Lần 3 — Bug logic (quét tự động)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| gui/dashboard.py `_checker_thread` | CRITICAL | `db.close()` không được gọi khi `run_full_copyright_check()` raise exception → SQLite connection leak | Chuyển `db = None` ra trước try; thêm `finally: if db: db.close()` |
| modules/copyright_checker.py | HIGH | Scroll loop cứng 3 lần, không kiểm tra số item tăng → bỏ sót vi phạm khi Facebook lazy-load | Thay bằng vòng lặp thông minh 10 lần, dừng khi count ổn định, sleep 1.5s |
| modules/copyright_checker.py item loop | MEDIUM | `except Exception: continue` im lặng → không biết item nào bị bỏ qua và tại sao | Thêm `log.debug(f"Bỏ qua item: {e}")` |
| gui/dashboard.py `_login_thread` | HIGH | CONFIG bị override không restore khi login thất bại (exception) → lần login sau có thể dùng sai credentials | Lưu giá trị gốc vào `_saved_fb`, restore trong `finally` khi `self.driver` vẫn None |

## [2026-05-22] Lần 4 — Bug logic (quét tự động lần 2)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `modules/copyright_checker.py` dòng 260 | HIGH | `score_risk(post_url)` dùng default `post_age_hours=999` → luôn trả về 0.0 → safety check cho bài mới không bao giờ trigger, tất cả đều auto-delete | Đổi thành `score_risk(post_url, post_age_hours=0)` — tuổi chưa biết → coi là mới → queue_review |
| `modules/copyright_checker.py` dòng 263 | HIGH | `re.search(pattern, post_url)` crash TypeError nếu `post_url` là None | Thêm guard `if post_url else None` trước `re.search()` |
| `modules/copyright_checker.py` dòng 348 | HIGH | Cùng lỗi dòng 263 trong `delete_appeal_post()` | Cùng fix guard |
| `api/server.py` db leak | HIGH | `db = Database()` trước for loop, `db.close()` có thể bị bỏ qua nếu exception thoát inner try | Thêm `try/finally` bọc for loop, `finally: db.close()` |
| `api/server.py` Chrome zombie | HIGH | `build_driver_for_account()` có thể spawn Chrome nhưng throw exception → `managed._driver` = None → Chrome không bị quit | Bọc `build_driver_for_account()` trong try-except với `continue` nếu thất bại |
| `agent/decide.py` dòng 140 | MEDIUM | `import json, re` trên một dòng (E401) và là local import không cần thiết | Chuyển `import json` và `import re` lên đầu file |
| `modules/two_factor.py` dòng 47 | MEDIUM | `import json, os` local trong hàm (E401) | Chuyển lên đầu file, xóa local import |

## [2026-05-22] Lần 5 — Bug logic (thread safety & resource leak)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `modules/fb_profile.py` dòng 192 | MEDIUM | `find_elements()` thứ hai sau scroll loop chạy ngay mà không có wait → Facebook lazy-load vẫn đang xử lý → bỏ sót fanpage cuối | Thêm `time.sleep(1)` trước `find_elements()` thứ hai |
| `modules/fb_profile.py` dòng 209 | MEDIUM | `seen[name] = href` không guard khi `name` rỗng sau fallback → key rỗng trong dict làm lộn xộn danh sách fanpage | Thêm `if not name or not name.strip(): continue` trước `seen[name] = href` |
| `agent/memory.py` | HIGH | `sqlite3.connect(check_same_thread=False)` mà không có `threading.Lock` → race condition khi nhiều account scan song song (ThreadPoolExecutor) | Thêm `self._db_lock = threading.Lock()` trong `__init__`; bọc `execute/commit` trong `record_decision`, `record_feedback`, `update_patterns` với `with self._db_lock:` |
| `agent/act.py` dòng 83 | MEDIUM | `ensure_profile_closed(profile_dir)` không có try-except → crash `build_driver_for_account()` nếu hàm fail (ví dụ: permission denied) | Bọc trong `try/except Exception as e: log.warning(...)` |
| `agent/perceive.py` dòng 125 | LOW | `log.debug(f"Webhook send failed: {e}")` → debug level quá thấp, admin không thấy khi webhook config sai | Đổi thành `log.warning(...)` |

## [2026-05-22] Lần 6 — Bug logic (tuple unpack, input validation, multi-import)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `agent/memory.py` dòng 160 | CRITICAL | `overall_fb, overall_correct = total_feedback` — `fetchone()` trả về None khi bảng user_feedback rỗng → crash TypeError khi unpack | Thêm `or (0, 0)`: `overall_fb, overall_correct = total_feedback or (0, 0)` |
| `modules/delete_post.py` dòng 20 | HIGH | `driver.get(post_url)` gọi trực tiếp mà không kiểm tra `post_url` rỗng/None → crash WebDriver nếu URL không hợp lệ | Thêm guard ở đầu hàm: `if not post_url: log.warning(...); return False` |
| `run_e2e_test.py` dòng 5 | MEDIUM | `import sys, io, os, traceback` — E401 multiple imports on one line | Tách thành 4 dòng import riêng biệt |

## [2026-05-22] Lần 7 — Bug logic (IndexError, raise None, resource leak)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `agent/decide.py` dòng 140 | CRITICAL | `response.content[0].text` — nếu Anthropic API trả về content rỗng, IndexError crash → fallback không được gọi | Thêm guard: `raw = response.content[0].text.strip() if response.content else ""`; nếu `raw` rỗng thì raise ValueError để catch rơi về keyword fallback |
| `agent/act.py` dòng 50 | HIGH | `raise last_exc` — nếu `max_attempts=0`, vòng lặp không chạy, `last_exc=None` → `raise None` crash TypeError | Đổi thành `raise last_exc or RuntimeError(f"{func.__name__} failed (max_attempts={max_attempts})")` |
| `api/server.py` dòng 264-268 | HIGH | `db = Database()` rồi `db.close()` sau `mem.update_patterns()` không có `finally` → nếu `update_patterns()` raise exception, `db.close()` bị bỏ qua → connection leak | Bọc trong `try: ... finally: db.close()` |

## [2026-05-22 11:07] Lần 14 — Lint fix + false positives đã xác nhận

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `test_switch.py` dòng 4 | F401 | `import json` không được dùng | Xóa |
| `modules/database.py` dòng 94 | Không lỗi | `get_flagged_posts()` thiếu filter bài đã xóa — thực ra `record_deletion()` (dòng 79) đã `UPDATE posts SET status='deleted'` khi xóa → `status='flagged'` tự loại trừ | Không sửa |
| `modules/fb_profile.py` API pagination | Không lỗi | `params={}` → `params if params else None` → None đúng cho pagination URL (Facebook đã nhúng access_token trong URL `next`) | Không sửa |

## [2026-05-22 10:07] Lần 13 — Bug logic (case-sensitive tên page, false positive đã xác nhận)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `modules/fb_profile.py` dòng 155 | MEDIUM | `name == personal_name` so sánh case-sensitive — nếu tên profile trong config có casing khác ("John Doe" vs "john doe") thì không được loại trừ đúng → profile cá nhân có thể bị thêm nhầm vào danh sách fanpage | Đổi thành `name.lower() == personal_name.lower()` |
| `agent/memory.py` SQL `excluded` | Không lỗi | `MAX(confirmed, excluded.confirmed)` là cú pháp SQLite upsert hợp lệ — `excluded` là alias chuẩn cho row bị conflict trong `ON CONFLICT DO UPDATE` | Không sửa |
| `api/server.py` dòng 222 | Không lỗi | `mem.conn.execute()` read-only query — SQLite cho phép đọc đồng thời không cần lock | Không sửa |
| `api/server.py` dòng 152 | Không lỗi | `db = Database()` ngay trước `try/finally: db.close()` — nếu Database() fail thì db chưa tồn tại và không có gì để đóng; nếu thành công thì finally đảm bảo đóng | Không sửa |

## [2026-05-22 09:07] Lần 12 — Bug logic (API params ngược, upsert thiếu url, flake8 F401)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `modules/account_manager.py` dòng 8 | F401 | `from dataclasses import dataclass, asdict, field` — `asdict` không được dùng ở đâu trong file | Xóa `asdict` khỏi import |
| `modules/fb_profile.py` dòng 334 | HIGH | `params if "limit" in url else None` — điều kiện ngược: lần gọi API đầu tiên URL chưa có "limit" → truyền `params=None` → không có `access_token` trong request → HTTP 401 → break ngay → hàm luôn trả về empty list | Đổi thành `params if params else None`: khi `params` là dict không rỗng truyền vào; sau pagination `params={}` thì truyền None (URL đã có params) |
| `modules/database.py` dòng 60 | MEDIUM | `upsert_post()` ON CONFLICT UPDATE không cập nhật trường `url` — nếu cùng `post_id` nhưng URL thay đổi (chia sẻ lại, redirect), DB giữ URL cũ | Thêm `url = excluded.url,` vào UPDATE clause |
| `gui/dashboard.py` stop_event | Không lỗi | Stop event đã được check tại personal_appeals loop (dòng 407) và fanpage outer loop (dòng 422) — hành vi đúng | Không sửa |

## [2026-05-22 08:08] Lần 11 — Bug logic (CONFIG không được restore sau login thất bại)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `gui/dashboard.py` dòng 886-889 | HIGH | `finally` block kiểm tra `not self.driver` để quyết định có restore CONFIG không — nhưng `self.driver` luôn được gán tại dòng 839 (`build_driver()`), kể cả khi login sau đó thất bại → `not self.driver = False` → CONFIG không bao giờ được khôi phục khi login fail, khiến email/password/headless cũ bị ghi đè vĩnh viễn | Thêm `_login_ok = False`; gán `_login_ok = ok` sau `fb_login()`; đổi condition thành `not _login_ok` |
| `modules/fb_login.py` dòng 105 | Không lỗi | `CONFIG["selenium"]` — `"selenium"` luôn có sẵn trong defaults của `config_loader.py` → không bao giờ KeyError | Không sửa |
| `delete_post.py` dòng 43-44 | Không lỗi | XPath `"..." " | ..."` — Python string literal concatenation hợp lệ; `|` là XPath union operator chuẩn | Không sửa |
| `agent/memory.py` SQL `MAX(confirmed, excluded.confirmed)` | Không lỗi | `excluded.confirmed` trong SQLite upsert trỏ tới giá trị vừa INSERT, `MAX(1, 0) = 1` giữ lại confirmed=True đúng ý định | Không sửa |

## [2026-05-22 08:06] Lần 10 — Bug logic (hardcoded zero in DB log)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `modules/copyright_checker.py` dòng 470 | MEDIUM | `db.log_scan(total=0, ...)` — `total` hardcode = 0, trong khi `flagged=len(all_appeals)`. DB `scan_log` luôn ghi 0 bài đã quét, làm mất ý nghĩa thống kê | Đổi thành `total=len(all_appeals)` để phản ánh đúng số appeals đã xử lý |
| `modules/account_manager.py` dòng 71 | Không lỗi | `not parts[0].isdigit() or len(parts[0]) < 5` — hành vi đúng theo thiết kế: số < 5 chữ số không phải UID Facebook (UID thường ≥ 15 ký tự) | Không sửa |

## [2026-05-22] Lần 9 — Bug logic (None url, false positives xác nhận)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `modules/post_scanner.py` dòng 52 | HIGH | `url = link.get_attribute("href")` trả về None nếu attribute không tồn tại → `_make_post_id(url)` gọi `url.encode()` → AttributeError: 'NoneType' object has no attribute 'encode' | Đổi thành `url = link.get_attribute("href") or profile_url` — fallback về profile_url thay vì None |
| `agent/memory.py` SQL `SUM(was_correct)` | Không lỗi | Đã có guard `(overall_correct or 0)` ở dòng 161 xử lý None; division-by-zero guard `if overall_fb` cũng có. Thực tế không crash khi table rỗng | Không sửa |

## [2026-05-22] Lần 8 — Bug logic (config KeyError, silent exception)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `modules/post_scanner.py` dòng 23-24 | HIGH | `CONFIG["facebook"]["profile_url"]` và `CONFIG["checker"]["keywords"]` truy cập trực tiếp → KeyError crash nếu key thiếu trong config.json (thường xảy ra khi chạy lần đầu hoặc config chưa đầy đủ) | Đổi thành `CONFIG.get("facebook", {}).get("profile_url", "")` và `CONFIG.get("checker", {}).get("keywords", [])`; thêm early return nếu `profile_url` rỗng |
| `modules/fb_profile.py` dòng 225 | MEDIUM | `except Exception: pass` trong manage_pages fallback loop nuốt lỗi im lặng → không biết khi nào key "name"/"url" bị thiếu hay Selenium lỗi | Đổi thành `except Exception as e: log.debug(f"Bỏ qua manage_pages fallback: {e}")` |

---

## Lần 20 — [2026-05-22 14:25] → 2026-05-22 17:27

### Lint fixes (flake8 F401, E401)
| File | Mô tả | Sửa |
|------|-------|-----|
| `dump_support_item.py` dòng 1 | E401 nhiều import 1 dòng + F401 `By` unused | Tách thành 3 import riêng, xóa `By` |
| `test_delete.py` dòng 1 | E401 nhiều import 1 dòng | Tách thành 3 import riêng |
| `dump_appeal.py` dòng 1 | E401 nhiều import 1 dòng + F401 `json`, `By` unused | Tách thành 3 import riêng, xóa `json` và `By` |
| `backup_code/modules/fb_login.py` dòng 48 | F401 `ChromeType` imported but unused | Xóa dòng `from webdriver_manager.core.os_manager import ChromeType` |

### Logic bugs
| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `modules/copyright_checker.py` dòng 205 | HIGH | `switch_to_profile` trả `True` sau khi TẤT CẢ fallback thất bại (quick_switch + profile_name + manual click đều fail) → caller hiểu nhầm là đã về profile gốc trong khi driver vẫn ở fanpage | Đổi `return True` cuối fallback block thành `return False` |
| `api/server.py` dòng 184-211 | HIGH | CONFIG backup chỉ lưu 3 key (email/password/2fa_secret); nếu `run_full_copyright_check` mutate thêm key khác (profile_url, profile_name...) thì không được restore → CONFIG "nhiễm" giá trị account vừa quét | Đổi `_orig = (...)` thành `_orig = dict(CONFIG["facebook"])` và `finally` restore bằng `.clear()` + `.update(_orig)` |
| `agent/decide.py` dòng 193 | MEDIUM | `should_auto_delete()` mutate `decision.action = "queue_review"` như side-effect ẩn → caller giữ reference đến decision object sẽ thấy action bị đổi bất ngờ sau khi gọi hàm | Xóa dòng `decision.action = "queue_review"`, chỉ return False |
| `modules/database.py` | HIGH | Class `Database` dùng `sqlite3.connect(check_same_thread=False)` nhưng hoàn toàn không có `threading.Lock` → concurrent access từ nhiều thread (GUI + checker) có thể gây SQLite ProgrammingError hoặc corruption | Thêm `self._lock = threading.Lock()` trong `__init__`; wrap tất cả `conn.execute`/`conn.commit` bằng `with self._lock:` |
| `gui/dashboard.py` dòng 1059 | MEDIUM | `_login_thread` finally chỉ restore CONFIG khi login thất bại (`not _login_ok`); nếu login thành công, CONFIG toàn cục bị lock vào thông tin account GUI vĩnh viễn | Bỏ điều kiện `not _login_ok` → luôn restore CONFIG trong finally |

---

## Lần 21 — [2026-05-22 17:27] → 2026-05-22 18:15

### Lint fixes (flake8 F401, F541, F841, E722, E401)
| File | Mô tả | Sửa |
|------|-------|-----|
| `dump_delete_flow.py` dòng 1 | E401 nhiều import 1 dòng + F401 `re` unused + F401 `WebDriverWait`, `EC` unused + E722 bare except (2 chỗ) | Tách import riêng, xóa unused imports, đổi bare except → except Exception |
| `modules/copyright_checker.py` dòng 449 | F541 f-string thiếu placeholder `f"[DEBUG] Found Radio..."` | Xóa prefix `f` |
| `modules/database.py` dòng 144 | F841 `now` được gán nhưng không dùng trong `mark_violation_deleted` (method chỉ cần UPDATE, không INSERT) | Xóa dòng `now = datetime.now().isoformat()` |
| `test_run.py` dòng 1 | E401 nhiều import 1 dòng + F401 `time` unused | Tách import riêng, xóa `time` |

### Logic bugs
| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `modules/copyright_checker.py` dòng 468-474 | HIGH | State machine Priority 4: `state = "MODAL_OPEN"` được gán trước khi kiểm tra `if state == "OPTION_SELECTED"` → điều kiện luôn False → `READY_TO_DELETE` không bao giờ đạt được → bài không bao giờ được xóa qua nhánh này | Lưu `prev_state = state` trước `safe_click`, rồi: `state = "READY_TO_DELETE" if prev_state == "OPTION_SELECTED" else "MODAL_OPEN"` |
| `modules/copyright_checker.py` dòng 486, 491 | MEDIUM | `appeal.get('title')[:60]` → nếu key 'title' không có, `get()` trả `None`, `None[:60]` ném `TypeError` | Đổi thành `(appeal.get('title') or '')[:60]` (cả 2 dòng) |
| `modules/bug_tracker.py` dòng 38-39 | MEDIUM | `log_bug()` ghi file `find_bug.jsonl` mà không có lock → khi nhiều scan thread gọi đồng thời, 2 JSON entries có thể bị ghi xen kẽ trên cùng 1 dòng → `get_pending_bugs()` mất entry đó | Thêm module-level `_file_lock = threading.Lock()`; wrap `open(..., "a")` bằng `with _file_lock:` |
