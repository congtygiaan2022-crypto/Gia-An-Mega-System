# BUGFIX LOG — Tool_auto_bcgame

## [2026-05-22 13:55] Lần 19 — _log thread-unsafe, btn_check_login missing, _run_loop UI calls

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `gui/main_window.py:187` + `gui/log_panel.py:51–54` | CRITICAL | `_log()` gọi `log_panel.add_log()` trực tiếp từ daemon thread → `add_log` làm 4 Tkinter widget operations (configure/insert/see/configure) → `RuntimeError: main thread is not in main loop`. `_log` được gọi hàng chục lần/giây trong mỗi vòng lặp | Đổi `_log` thành `self.after(0, lambda m=message, l=level: self.log_panel.add_log(m, l))` |
| `gui/main_window.py:234` | HIGH | `btn_check_login` được tham chiếu trong `_manual_login_thread` (enable sau khi browser mở) và `_on_login_success` (disable) nhưng **không được tạo ở đâu trong `_setup_ui()`** → `getattr(..., None)` trả None → button không bao giờ xuất hiện → người dùng không có cách xác nhận đã login thủ công | Thêm `self.btn_check_login = ctk.CTkButton(...)` vào `frm_btns` ở row=3 |
| `gui/main_window.py:632,689,702,705,709` (`_run_loop`) | MEDIUM | `_run_loop` (legacy/dead code) có 5 direct Tkinter widget calls từ thread: `lbl_match_info.configure`, `lbl_care_info.configure`, `tabview.set`, `report_list.insert`, `stats_panel.update_stats` — nếu được kích hoạt sẽ crash | Bọc tất cả trong `self.after(0, lambda: ...)` với default argument capture |

## [2026-05-22 13:25] Lần 18 — Fixed mode báo cáo sai, Tkinter thread-safety, import re

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `gui/main_window.py` dòng 476 + 571 + 575 | HIGH | `report_data['stake'] = balance` (toàn bộ số dư) thay vì `bet_amount` (tiền cược thực) → chế độ Fixed Bet ghi Google Sheet sai; `finalize_report` truyền `balance` thay `bet_amount` → tính lỗ/lãi sai; `new_balance = balance * odds if won else 0` sai (phải tính `balance - bet_amount + bet_amount * odds` khi thắng, `balance - bet_amount` khi thua) | Thêm `self.pending_bet_amount`; dùng `bet_amount` cho `stake` và `finalize_report`; sửa công thức `new_balance` |
| `gui/main_window.py` nhiều dòng | HIGH | `self.tabview.set()`, `self.report_list.insert()`, `self.care_list.insert()`, `self.lbl_care_info.configure()`, `self.stats_panel.update_stats()` gọi trực tiếp từ daemon thread → Tkinter không thread-safe → `RuntimeError: main thread is not in main loop` hoặc crash im lặng | Bọc tất cả widget call trong `self.after(0, lambda: ...)` với default argument capture |
| `core/session.py` dòng 361 | MEDIUM | `import re as _re` bên trong `get_balance()` (được gọi trong vòng lặp) — `re` không được import ở đầu file | Thêm `import re` lên đầu file; xóa local import; đổi `_re.sub` → `re.sub` |

## [2026-05-22 12:55] Lần 17 — Tab hijack, phone format, import shadow, reporter wrong value

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `core/scraper_wap.py` `check_match_status` | CRITICAL | Code cũ switch về `handles[1]` (tab đang mở sẵn) thay vì mở tab mới bằng `window.open('')` → BCGame tab bị navigate sang trang chi tiết wap.vn; agent đã fix: luôn dùng `window.open('')` + switch `window_handles[-1]` | Đổi `if len(handles) > 1: switch(handles[1])` thành `window.open(''); switch(window_handles[-1])` |
| `core/bettor.py` dòng 113–116 | HIGH | `_find_bet_elements()` có thể trả `None` → `elements.get('btn')` crash `AttributeError: 'NoneType' has no attribute 'get'` | Thêm guard `if elements:` trước `elements.get('btn')` |
| `gui/main_window.py` | MEDIUM | `import re as _re` trong vòng lặp while shadow module-level `re` → các regex call sau đó dùng `re` bị NameError hoặc dùng wrong binding | Xóa local import, dùng module-level `import re` |
| `core/session.py` dòng 80 | MEDIUM | `phone.lstrip("+").replace(country_code.lstrip("+"), "", 1).lstrip("0")` — nếu `country_code = "+84"` thì sau `lstrip("+")` là `"84"`, `phone.lstrip("+")` là `"84901234567"`, replace `"84"` → `"901234567"`, `lstrip("0")` → đúng. Nhưng khi phone = `"0901234567"` (không có +84 prefix) thì `lstrip("+")` = `"0901234567"`, `replace("84", "", 1)` = `"0901234567"` (không có "84" prefix) → `lstrip("0")` = `"901234567"` → OK. Edge case: phone = `"84901234567"` không có `+` → replace cắt `"84"` → `"901234567"` — đúng. Không phải bug thực. | Không sửa (false positive) |
| `core/reporter.py` dòng 89 | MEDIUM | `total = (stake * odds) if won else -stake` — ghi `total` âm khi thua là đúng theo thiết kế báo cáo | Không sửa (đúng) |

## [2026-05-22 12:30] Lần 16 — Manual mode broken, window recovery sai, lint fixes

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `gui/main_window.py` dòng 354–360 | CRITICAL | Chế độ thủ công tạo match dict không có key `detail_url` → `selected_match.get('detail_url')` trả `None` → `check_match_status(None, ...)` → `if not detail_url: return False` → `is_upcoming=False` → match bị excluded → vòng while cạn hết → không bao giờ đặt cược được | Thêm guard: `if detail_url:` trước khi gọi `check_match_status`, còn lại `is_upcoming = True` (manual mode bypass) |
| `core/auditor.py` dòng 65 | MEDIUM | `except` block của `GoogleAuditor.check_result` switch về `self.browser.driver.window_handles[0]` thay vì `original_window` → nếu có nhiều tab trước khi auditor chạy, `[0]` không chắc là tab BCGame gốc → mất context tab sau lỗi | Đổi thành `switch_to.window(original_window)` |
| `scratch/debug_balance.py` | LOW | F401: `time` và `By` không dùng | Xóa 2 import |
| `scratch/test_chrome.py` | LOW | F401: `sys` không dùng | Xóa import |
| `scripts/download_chrome.py` dòng 19 | LOW | F541: f-string không có placeholder | Xóa tiền tố `f` |
| `scripts/test_login_dom.py` dòng 53 | LOW | E722: bare `except:` | Đổi thành `except Exception:` |

## [2026-05-22 12:07] Lần 15 — Tab leak + martingale display + _run_loop guard

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `core/scraper_wap.py` `check_match_status` | HIGH | Tab chi tiết mở ra nhưng không bao giờ bị `close()` trước khi `switch_to.window(original_window)` → sau nhiều lần gọi Chrome tích lũy hàng chục tab mở → performance suy giảm, có thể `WebDriverException` | Thêm `try: self.browser.driver.close() except Exception: pass` trước cả hai `switch_to.window(original_window)` (cả return False và return True path) và trong except block |
| `strategies/martingale.py` dòng 46 | LOW | `get_info()` tính `self.multiplier**self.current_level` — khi `current_level > max_level`, `current_amount` đã bị cap nhưng `current_level` vẫn tăng → hiển thị multiplier cao hơn thực tế đang cược | Thêm `display_level = min(self.current_level, self.max_level)` rồi dùng `display_level` thay `current_level` trong format string |
| `gui/main_window.py` dòng 651 (`_run_loop`) | MEDIUM | `self.browser.click_element(best_odd['element'])` không check `_js_click_done` — khi `get_over_odds()` đã click bằng JS và trả về `element=None`, gọi `click_element(None)` bỏ qua click hoàn toàn mà không thông báo | Thêm guard `if not best_odd.get('_js_click_done') and best_odd.get('element'):` |

## [2026-05-22] Lần 1

| File | Dòng (gốc) | Loại | Nội dung gốc | Sửa thành |
|------|-----------|------|--------------|-----------|
| core/bettor.py | 5 | F401 | `import random` | Xóa (không dùng) |
| core/bettor.py | 6 | F401 | `import os` | Xóa (không dùng) |
| core/bettor.py | 8 | F401 | `from typing import Optional, Callable, Dict, List` | `from typing import Optional, Callable` (xóa Dict, List) |
| core/bettor.py | 16–17 | F401 | `from selenium.webdriver.common.by import By` và `from selenium.webdriver.common.keys import Keys` bên trong try/except | Xóa cả khối try/except import selenium; giữ `SELENIUM_AVAILABLE = True` |
| core/bettor.py | 129 | F541 | `f"✅ Đã bấm nút xác nhận. Đang chờ phản hồi..."` | `"✅ Đã bấm nút xác nhận. Đang chờ phản hồi..."` (bỏ tiền tố `f`) |
| core/bettor.py | 138 | F541 | `f"✅ Đặt cược hoàn tất thành công!"` | `"✅ Đặt cược hoàn tất thành công!"` (bỏ tiền tố `f`) |
| core/bettor.py | 295 | E722 | `except:` | `except Exception:` |
| core/browser.py | 14 | F401/F811 | `from selenium.webdriver.common.by import By` | Xóa (By được import cục bộ trong @property `By`) |
| core/browser.py | 17–18 | F401 | `NoSuchElementException` trong import | Xóa khỏi danh sách import |
| core/browser.py | 87 | F841 | `portable_chrome = os.path.join(...)` | Xóa dòng gán (biến không được dùng) |
| core/browser.py | 205 | E722 | `except: pass` | `except Exception: pass` |
| core/auditor.py | 4 | F401 | `import requests` | Xóa (không dùng) |
| core/auditor.py | 8 | F401 | `from typing import Optional, Tuple` | `from typing import Tuple` (xóa Optional) |
| core/auditor.py | 11 | F401 | `from datetime import datetime` | Xóa (không dùng) |
| core/auditor.py | 47 | E722 | `except: pass` | `except Exception: pass` |
| core/auditor.py | 68 | E722 | `except: pass` | `except Exception: pass` |
| core/auditor.py | 131 | E722 | `except: pass` | `except Exception: pass` |
| gui/main_window.py | 18 | F401 | `from core.auditor import GoogleAuditor` | `from core.auditor import CombinedAuditor` (dùng đúng class) |
| gui/main_window.py | 393 | E722 | `except: continue` | `except Exception: continue` |
| gui/main_window.py | 510 | F541 | `f"🏁 Kết thúc 0-0. THUA CƯỢC."` | `"🏁 Kết thúc 0-0. THUA CƯỢC."` (bỏ tiền tố `f`) |
| gui/main_window.py | 567 | F841 | `api_key = self.ent_api_key.get().strip() or ...` | Xóa dòng gán (biến không được dùng) |
| gui/main_window.py | 657 | F541 | `f"🏁 Kết thúc 0-0. THUA CƯỢC."` | `"🏁 Kết thúc 0-0. THUA CƯỢC."` (bỏ tiền tố `f`) |
| gui/bet_panel.py | 2 | F401 | `from typing import Callable, Optional` | Xóa (không dùng) |
| gui/bet_panel.py | 90 | E722 | `except:` | `except Exception:` |
| gui/log_panel.py | 3 | F401 | `from typing import Optional, Callable` | Xóa (không dùng) |

## [2026-05-22] Lần 2 (bổ sung)

| File | Loại | Sửa |
|------|------|-----|
| core/__init__.py | F401 | Xóa import BugTracker, report_bug, mark_bug_fixed không dùng |
| core/session.py | F401 | Xóa WebDriverWait, EC khỏi try block |
| core/session.py | F541 | `f"🔄 Đang chuyển hướng..."` → bỏ `f` |
| core/session.py | E722 | 3× `except:` → `except Exception:` |
| core/scraper_wap.py | F401 | Xóa `import requests` |
| core/scraper_wap.py | F841 | Xóa `original_window` không dùng trong get_tai_matches |
| core/scraper_wap.py | E722 | 4× `except:` → `except Exception:` |
| core/bug_tracker.py | F401 | Xóa `import json`, `from pathlib import Path` |
| core/bug_tracker.py | F841 | `tracker = cls()` → `cls()` |
| core/reporter.py | F401 | Xóa `List`, `Optional` khỏi typing import |
| core/selector.py | F401 | Xóa `Tuple`, `process` khỏi imports |
| gui/main_window.py | F401+F811 | Xóa top-level `CombinedAuditor` import (đã import cục bộ trong function) |
| fix_bugs_with_claude.py | F401 | Xóa `json`, `datetime`, `Path`, `FIX_BUG_FILE` không dùng |
| fix_bugs_with_claude.py | F541 | `f"📄 Xem kết quả..."` → bỏ `f` |
| full_test.py | F401 | Xóa `os`, `datetime` |
| strategies/base.py | F401 | Xóa `Optional` |

## [2026-05-22] Lần 2 — Bug chức năng

| File | Bug ID | Mức độ | Mô tả | Sửa thành |
|------|--------|--------|-------|-----------|
| core/scraper.py | BUG-002 | HIGH | Dead code 25 dòng sau `return []` (dùng `raw_candidates`, `js_click_05` chưa định nghĩa) | Xóa toàn bộ đoạn dead code |
| core/bettor.py | BUG-003 | MEDIUM | `_get_bet_elements()` có 2 khối try/except giống hệt nhau; khối thứ 2 không bao giờ chạy | Xóa khối try/except trùng lặp |
| full_test.py | BUG-004 | CRITICAL | `browser.click_element(target_odd['element'])` crash khi `element=None` (`_js_click_done=True`) | Thêm guard `if not target_odd.get('_js_click_done'):` trước khi click |

## [2026-05-22] Lần 3 — Bug logic (quét tự động)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| core/scraper.py `get_matches()` | HIGH | Chỉ query DOM 1 lần sau sleep(2), không scroll → BCGame lazy-load → bỏ sót kèo | Thêm scroll loop 8 lần dừng khi count ổn định trước khi query cuối |
| core/session.py cookie loop | MEDIUM | `except Exception: pass` im lặng khi add_cookie thất bại → không biết cookie nào bị bỏ qua | Thêm `self._log(f"Bỏ qua cookie lỗi '{name}': {e}", "DEBUG")` |
| core/auditor.py parse score | MEDIUM | `except Exception: pass` khi parse điểm số → tiếp tục với 0-0 mà không log lý do | Đổi thành `except Exception as e: logger.debug(f"Parse score Google: {e}")` |
| core/auditor.py window recovery | MEDIUM | 2× `except Exception: pass` trong cleanup tab → không biết tab cleanup thất bại | Thêm `logger.debug(f"Window recovery failed: {e}")` vào cả 2 chỗ |

## [2026-05-22] Lần 4 — Bug logic (quét tự động lần 2)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `core/scraper_wap.py` dòng 59 | MEDIUM | `cols[4].find('font')` gọi 2 lần trong ternary → gọi thừa, tiềm ẩn sai nếu DOM thay đổi giữa 2 lần | Dùng biến tạm `_font = cols[4].find('font')`, kiểm tra một lần |
| `core/scraper_wap.py` dòng 101 | MEDIUM | `except Exception: continue` không log → bỏ qua lỗi parse hàng trận im lặng | Thêm `self._log(f"Lỗi parse hàng trận: {e}", "DEBUG")` |
| `core/reporter.py` dòng 81 | HIGH | `row[1]` và `row[5]` không có guard len → IndexError nếu Google Sheet có hàng thiếu cột | Thêm `len(row) >= 6` check trước khi truy cập |
| `core/bettor.py` dòng 76 | MEDIUM | `int(amount)` truncate phần thập phân → 1500.9 USDT thành 1500 | Đổi thành `int(round(amount))` để làm tròn đúng |

## [2026-05-22] Lần 5 — Bug logic (GUI state & driver leak)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `gui/main_window.py` `__init__` | CRITICAL | `pending_match`, `pending_report`, `pending_odd`, `pending_balance`, `pending_won` không được khởi tạo trong `__init__` → AttributeError khi thread truy cập trước khi bet được thực hiện | Thêm 5 dòng khởi tạo `self.pending_* = None` vào `__init__` |
| `gui/main_window.py` `_run_auto_bet` | CRITICAL | `balance <= 0` chỉ log warning rồi đặt `bet_amount = 1000` và tiếp tục → mất cược khi không đọc được số dư | Thêm guard sớm: nếu `balance <= 0` thì append `excluded_matches` và `continue`; xóa fallback `bet_amount = 1000` |
| `core/session.py` dòng 366 | MEDIUM | `item['text']` và `item['weight']` không dùng `.get()` → KeyError nếu JS trả về dict thiếu key | Đổi thành `item.get('text', '')` và `item.get('weight', 1)` |
| `core/browser.py` dòng 99 | HIGH | `WebDriverWait(self.driver, 20)` throw exception sau khi Chrome đã khởi động → `self.driver` bị leak (không bao giờ `quit()`) | Bọc trong try-except: nếu lỗi thì `self.driver.quit(); self.driver = None; raise` |

## [2026-05-22] Lần 6 — Bug logic (file leak, dead code, sai variable)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `core/bug_tracker.py` dòng 195 | CRITICAL | `open(FIND_BUG_FILE).read()` không dùng context manager → file handle leak nếu `read()` throw exception | Đổi thành `with open(...) as f: content = f.read()` |
| `core/bug_tracker.py` dòng 241 | CRITICAL | Tương tự dòng 195 trong `list_bugs()` | Cùng fix context manager |
| `core/bug_tracker.py` dòng 214-216 | HIGH | Ba dòng đều gán `new_content` nhưng dùng `content` gốc, hai dòng đầu (214-215) là dead code bị overwrite ngay bởi dòng 216 | Xóa dòng 214-215, chỉ giữ `new_content = re.sub(pattern, "", content, ...)` |
| `core/bug_tracker.py` dòng 259 | HIGH | `re.search(..., content)` tìm trên toàn bộ file → lấy task của bug đầu tiên thay vì bug hiện tại | Đổi `content` thành `block_txt` để search trong block của bug hiện tại |
| `core/selector.py` dòng 120 | MEDIUM | `for cand in candidate_matches` không guard → TypeError nếu caller truyền None | Thêm `if not candidate_matches: return None` trước vòng lặp |

## [2026-05-22] Lần 7 — Bug logic (dict access, regex pattern, IndexError)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `core/scraper.py` dòng 258 | HIGH | `find_match_element()` gọi `el.text` nhưng `el` từ `_get_match_rows()` là dict `{element, text}` → AttributeError khi runtime | Đổi thành `text = el['text'] if isinstance(el, dict) else el.text` và `match.element = el['element'] if isinstance(el, dict) else el` |
| `core/bug_tracker.py` dòng 259 | HIGH | Sau fix Lần 6 (đổi `content` → `block_txt`), regex pattern vẫn có `##\s+🐛...` nhưng `block_txt` là group(1) không chứa header `##` → task_m luôn None, tên task không bao giờ được đọc | Đổi pattern thành `r"^\s*—\s*(.+)"` để khớp phần ` — task name` đầu `block_txt` |

## [2026-05-22 11:07] Lần 14 — Bug logic (race condition start button, false positives)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `gui/main_window.py` dòng 258-274 | HIGH | `_start_auto_bet`, `_start_auto_care`, `_start_auto_report` đều set `is_running=True` và tạo thread mới mà không check xem thread khác có đang chạy hay không → user có thể bấm cả 3 nút liên tiếp, tạo 3 thread đồng thời cùng đọc/ghi `pending_match/odd/balance/won` → race condition, dữ liệu sai | Thêm `if self.is_running: self._log("⚠️ ..."); return` ở đầu cả 3 hàm |
| `gui/main_window.py` sleep for-loop | Không lỗi | Infinite loop khi `stop` được gọi trong sleep — thực ra `while self.is_running:` (dòng 516) tự thoát sau khi for-loop break do `is_running=False` | Không sửa |

## [2026-05-22 10:07] Lần 13 — Bug logic (empty detail_url append, false positive đã xác nhận)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `core/scraper_wap.py` dòng 87 | HIGH | Match có `detail_url=""` (không tìm thấy link XEM và không có tỷ số live) vẫn được append vào danh sách → khi bot sau đó gọi `browser.navigate("")` hoặc mở URL rỗng sẽ lỗi; điều kiện `if detail_url and not detail_url.startswith('http')` bị short-circuit khi empty string nên không bắt được | Thêm `if not detail_url: continue` riêng sau SKIP check để loại bỏ match không có URL hợp lệ |
| `core/auditor.py` dòng 26, 84 | Không lỗi | `self.browser.execute_script(...)` — `BrowserController` có method `execute_script()` riêng (xác nhận từ Lần 9) | Không sửa |
| `core/bettor.py` dòng 115 | Không lỗi | `confirm_btn = elements.get('btn')` có thể None nhưng dòng 119 đã có guard `if confirm_btn:` | Không sửa |

## [2026-05-22 09:07] Lần 12 — Bug logic (Ctrl+V sai key combo, None deref pending_*)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `core/browser.py` dòng 225 | HIGH | `element.send_keys(Keys.CONTROL, 'v')` — truyền 2 argument riêng lẻ nên gửi phím CONTROL rồi phím V tách biệt, không phải tổ hợp Ctrl+V → paste không hoạt động | Đổi thành `element.send_keys(Keys.CONTROL + 'v')` (string concat tạo ra key combo) |
| `gui/main_window.py` dòng 547 | HIGH | `_run_auto_report` chỉ check `pending_report` và `pending_won` trước khi dùng, nhưng `pending_odd` và `pending_balance` không được check → dòng 553-554 `best_odd['odds']` crash TypeError: 'NoneType' is not subscriptable nếu `_run_auto_care` chưa chạy | Mở rộng guard để check cả `pending_odd is None` và `pending_balance is None` |
| `gui/main_window.py` dòng 501 | HIGH | `_run_auto_care` chỉ check `pending_match`, nhưng dòng 509-511 dùng `report_data['match']` với `report_data = self.pending_report` — nếu `pending_report` là None → crash TypeError | Thêm guard `if not getattr(self, 'pending_report', None): return` |
| `gui/main_window.py` dòng 563-565 | MEDIUM | Reset block cuối `_run_auto_report` bỏ sót `pending_odd = None` và `pending_balance = None` → vòng cược tiếp theo kế thừa odds/balance cũ | Thêm 2 dòng reset `pending_odd` và `pending_balance` |
| `core/bug_tracker.py` dòng 305 | Không lỗi | `return wrapper` đã có (đã xác nhận lần 9) — agent tiếp tục báo false positive | Không sửa |

## [2026-05-22 08:08] Lần 11 — Bug logic (ValueError int(''), false positive đã xác nhận)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `core/auditor.py` dòng 106-107 | CRITICAL | `int(re.sub(r'\D', '', score_home_el.text))` crash ValueError khi text chỉ chứa ký tự không phải số (ví dụ "--", "?", rỗng) sau khi loại `\D` → `int('')` → ValueError | Tách ra 2 biến tạm `h_str`/`a_str`, thêm guard `if h_str and a_str:` trước khi `int()` |
| `core/scraper_wap.py` dòng 79 | Không lỗi | `if not is_clock and h1 <= 20 and h2 <= 20: SKIP` — đây là logic có chủ đích: skip hàng trận đang live/kết thúc (có tỷ số thực) để tránh đặt cược nhầm | Không sửa |
| `core/session.py` sort bằng nhau | Không lỗi | Unstable sort khi weight bằng nhau không gây crash, chỉ ảnh hưởng thứ tự chọn — chấp nhận được | Không sửa |

## [2026-05-22 08:06] Lần 10 — Bug logic (missing dict guard)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `gui/main_window.py` dòng 165 | HIGH | `_save_config()` truy cập `self.config["login"]["phone"]` trực tiếp — nếu `config.json` chưa tồn tại hoặc thiếu key "login", gọi `_save_config()` sẽ crash KeyError. Key "ui" và "api" đã có guard `if "ui" not in self.config` nhưng "login" thì không | Thêm `if "login" not in self.config: self.config["login"] = {}` trước dòng gán |

## [2026-05-22] Lần 9 — Bug logic (KeyError dict, None url)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `core/selector.py` dòng 125-130 | HIGH | `cand['home_team']` và `cand['away_team']` truy cập trực tiếp bằng `[]` → KeyError crash nếu dict `candidate_matches` thiếu key này (thường xảy ra khi `Match` object được truyền vào thay vì dict) | Đổi toàn bộ 4 chỗ sang `cand.get('home_team', '')` và `cand.get('away_team', '')` |
| `core/bug_tracker.py` ~307 | Không lỗi | Kiểm tra lại: `return wrapper` đã có ở dòng 307, `return decorator` ở dòng 308 — cấu trúc decorator hoàn toàn đúng. Bug report từ agent là false positive | Không sửa |
| `core/scraper_wap.py` dòng 157 | Không lỗi | `self.browser.execute_script(...)` hợp lệ vì `BrowserController` có method `execute_script()` riêng (dòng 236 của browser.py) | Không sửa |

## [2026-05-22] Lần 8 — Bug logic (None sheet, double DOM query)

| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `core/reporter.py` `add_bet_report` | HIGH | `_authenticate()` có thể trả True nhưng `self.sheet` vẫn None (nếu `get_worksheet(0)` trả None) → condition `not self.sheet and not _auth()` = `True and False = False` → không return sớm → `self.sheet.insert_row()` crash AttributeError | Thêm `if not self.sheet: logger.error(...); return False` sau guard đầu |
| `core/reporter.py` `finalize_report` | HIGH | Cùng lỗi như trên trong `finalize_report()` → `self.sheet.get_all_values()` crash AttributeError | Thêm cùng guard `if not self.sheet: return False` |
| `core/scraper.py` dòng 219 | MEDIUM | `find_elements(xpath)` gọi 2 lần trong ternary — lần 1 kiểm tra, lần 2 lấy `[0]` — 2 DOM query thừa; nếu DOM thay đổi giữa 2 lần → IndexError silently bị nuốt; exception không log | Lưu vào biến tạm `name_els`; đổi `except Exception: pass` → `except Exception as e: logger.debug(...)` |

---

## Lần 20 — [2026-05-22 14:25] → 2026-05-22 17:27

### Logic bugs
| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `core/auditor.py` dòng 25, 83 | HIGH | `original_window` chỉ được gán TRONG try block; nếu `current_window_handle` ném exception (session chết), except block tham chiếu `original_window` → `NameError` | Khởi tạo `original_window = None` TRƯỚC try; kiểm tra `if original_window:` trước khi dùng trong except; áp dụng cho cả `GoogleAuditor` và `FlashScoreAuditor` |
| `core/reporter.py` dòng 89 | HIGH | `total = stake * odds` khi thắng = tổng tiền nhận về (gồm vốn), không phải lợi nhuận → cột "Tổng Kết" bị thổi phồng; khi thua `-stake` là đúng (lỗ thuần) nhưng khi thắng phải là lãi thuần | Đổi thành `total = stake * (odds - 1) if won else -stake` |
| `core/scraper_wap.py` dòng 215 | MEDIUM | `_parse_time` không xử lý trường hợp trận đêm khuya hôm qua: giờ hiện tại là 00:05, trận 23:30 thuộc ngày hôm qua → `h > 18 and base_time.hour < 6` không có nhánh → trận được coi là trong tương lai ~23h sau | Thêm `elif h > 18 and base_time.hour < 6: dt -= timedelta(days=1)` |
| `core/selector.py` dòng 34 | MEDIUM | Default `dictionary_path = "data/name_dictionary.json"` là relative path; khi cwd khác project root, `os.makedirs("data")` tạo sai chỗ, `open(path)` fails FileNotFoundError | Trong `__init__`: nếu path không phải absolute thì resolve thành absolute từ `os.path.abspath(__file__)` của selector.py |

---

## Lần 21 — [2026-05-22 17:27] → 2026-05-22 18:15

### Logic bugs
| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `core/session.py` dòng 81 | HIGH | `clean_phone = phone.lstrip("+").replace(country_code.lstrip("+"), "", 1)` dùng `str.replace()` → xóa lần xuất hiện đầu tiên của mã quốc gia bất kể vị trí; ví dụ phone="0984123456", cc="+84" → `replace("84","",1)` → "0123456" sai hoàn toàn | Dùng `startswith`: kiểm tra `_stripped.startswith(_cc)` rồi mới cắt `_stripped[len(_cc):]` |
| `core/scraper_wap.py` dòng 156-158 | MEDIUM | Trong `check_match_status`: nếu `window.open('')` thành công nhưng `switch_to.window()` ngay sau ném exception, tab mới đã tạo nhưng không bao giờ được đóng → resource leak tab | Thêm cờ `_new_tab_opened = False` trước outer try; set `True` sau `window.open`; trong except: `if _new_tab_opened and len(window_handles) > 1: driver.close()` trước `switch_to(original_window)` |

---

## Lần 22 — [2026-05-26 14:04]

### Logic bugs
| File | Mức độ | Mô tả | Sửa thành |
|------|--------|-------|-----------|
| `core/selector.py` | HIGH | Nhận diện trận đấu và so khớp tên giữa Wap.vn (tiếng Việt) và BCGame (tiếng Anh) dễ bị lỗi hoặc bỏ sót do khác biệt ngôn ngữ, viết tắt và dấu tiếng Việt (ví dụ: "Thụy Điển" vs "Sweden", "M.U" vs "Manchester United"). | Thêm `strip_diacritics` để loại bỏ dấu tiếng Việt; tích hợp bộ từ điển `TRANSLATIONS` dịch từ tiếng Việt/viết tắt sang tiếng Anh/tên đầy đủ; sắp xếp từ khóa dịch theo độ dài giảm dần để tránh dịch đè từ ngắn trong từ dài (ví dụ: "viet nam" -> "vietnam" trước khi dịch "nam"); cập nhật `find_best_match_in_list` và `normalize_name` để sử dụng bộ chuẩn hóa này. |
| `core/scraper.py` | HIGH | `search_match` trên BCGame chỉ dùng tên đội gốc từ Wap.vn nên không tìm thấy các đội được dịch sang tiếng Việt (như "Thụy Điển", "Ý"). | Tích hợp `normalize_name` vào `search_match`; thêm cả tên gốc tiếng Việt và tên tiếng Anh đã dịch/chuẩn hóa vào danh sách từ khóa tìm kiếm (`search_queries`) để tăng tối đa khả năng tìm thấy trận đấu trên BCGame. |

