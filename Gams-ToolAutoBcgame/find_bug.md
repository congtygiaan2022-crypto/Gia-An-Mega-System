# 🐛 FIND BUG — Danh sách lỗi cần sửa

> File này được tự động tạo bởi **BugTracker**.
> Claude Code sẽ đọc file này, tìm và sửa lỗi, rồi gọi `BugTracker.mark_fixed(bug_id)`.
>
> **Cách sửa thủ công:**
> ```bash
> python fix_bugs_with_claude.py --list      # Xem danh sách lỗi
> python fix_bugs_with_claude.py             # Tự động sửa tất cả
> python fix_bugs_with_claude.py --id BUG_X  # Chỉ sửa một bug
> python fix_bugs_with_claude.py --mark BUG_X --note "Mô tả cách sửa"  # Đánh dấu thủ công
> ```

---
## 🐛 [BUG_20260604_013357_001] — start
- **Thời gian**: `2026-06-04 01:33:57`
- **Module**: `core.browser`
- **Mức độ**: `CRITICAL`
- **Loại lỗi**: `SessionNotCreatedException`
- **Thông báo lỗi**: `Message: session not created: cannot connect to chrome at 127.0.0.1:59989
from chrome not reachable
Stacktrace:
	undetected_chromedriver!GetHandleVerifier [0x81b593+105d3]
	undetected_chromedriver!GetHandleVerifier [0x81b6c4+10704]
	undetected_chromedriver!(No symbol) [0x621cde]
	undetected_chromedriver!(No symbol) [0x615478]
	undetected_chromedriver!(No symbol) [0x65cb32]
	undetected_chromedriver!(No symbol) [0x652e25]
	undetected_chromedriver!(No symbol) [0x652c46]
	undetected_chromedriver!(No symbol) [0x69947f]
	undetected_chromedriver!(No symbol) [0x698c97]
	undetected_chromedriver!(No symbol) [0x68d516]
	undetected_chromedriver!(No symbol) [0x6608e9]
	undetected_chromedriver!(No symbol) [0x6616a4]
	undetected_chromedriver!GetHandleVerifier [0xaa3014+298054]
	undetected_chromedriver!GetHandleVerifier [0xa9e603+293643]
	undetected_chromedriver!GetHandleVerifier [0xabea05+2b3a45]
	undetected_chromedriver!GetHandleVerifier [0x8354e8+2a528]
	undetected_chromedriver!GetHandleVerifier [0x83cd1d+31d5d]
	undetected_chromedriver!GetHandleVerifier [0x823e68+18ea8]
	undetected_chromedriver!GetHandleVerifier [0x824015+19055]
	undetected_chromedriver!GetHandleVerifier [0x80d65f+269f]
	KERNEL32!BaseThreadInitThunk [0x76bffcc9+19]
	ntdll!RtlGetAppContainerNamedObjectPath [0x7784843e+11e]
	ntdll!RtlGetAppContainerNamedObjectPath [0x7784840e+ee]
`
- **Context**:
  - **headless**: `False`
  - **proxy**: `none`
- **Traceback**:
```
Traceback (most recent call last):
  File "E:\Gams-ToolAutoBcgame\core\browser.py", line 112, in start
    self.driver = uc.Chrome(
                  ^^^^^^^^^^
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\undetected_chromedriver\__init__.py", line 466, in __init__
    super(Chrome, self).__init__(
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\selenium\webdriver\chrome\webdriver.py", line 45, in __init__
    super().__init__(
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\selenium\webdriver\chromium\webdriver.py", line 61, in __init__
    super().__init__(command_executor=executor, options=options)
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\selenium\webdriver\remote\webdriver.py", line 208, in __init__
    self.start_session(capabilities)
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\undetected_chromedriver\__init__.py", line 724, in start_session
    super(selenium.webdriver.chrome.webdriver.WebDriver, self).start_session(
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\selenium\webdriver\remote\webdriver.py", line 292, in start_session
    response = self.execute(Command.NEW_SESSION, caps)["value"]
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\selenium\webdriver\remote\webdriver.py", line 347, in execute
    self.error_handler.check_response(response)
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\selenium\webdriver\remote\errorhandler.py", line 229, in check_response
    raise exception_class(message, screen, stacktrace)
selenium.common.exceptions.SessionNotCreatedException: Message: session not created: cannot connect to chrome at 127.0.0.1:59989
from chrome not reachable
Stacktrace:
	undetected_chromedriver!GetHandleVerifier [0x81b593+105d3]
	undetected_chromedriver!GetHandleVerifier [0x81b6c4+10704]
	undetected_chromedriver!(No symbol) [0x621cde]
	undetected_chromedriver!(No symbol) [0x615478]
	undetected_chromedriver!(No symbol) [0x65cb32]
	undetected_chromedriver!(No symbol) [0x652e25]
	undetected_chromedriver!(No symbol) [0x652c46]
	undetected_chromedriver!(No symbol) [0x69947f]
	undetected_chromedriver!(No symbol) [0x698c97]
	undetected_chromedriver!(No symbol) [0x68d516]
	undetected_chromedriver!(No symbol) [0x6608e9]
	undetected_chromedriver!(No symbol) [0x6616a4]
	undetected_chromedriver!GetHandleVerifier [0xaa3014+298054]
	undetected_chromedriver!GetHandleVerifier [0xa9e603+293643]
	undetected_chromedriver!GetHandleVerifier [0xabea05+2b3a45]
	undetected_chromedriver!GetHandleVerifier [0x8354e8+2a528]
	undetected_chromedriver!GetHandleVerifier [0x83cd1d+31d5d]
	undetected_chromedriver!GetHandleVerifier [0x823e68+18ea8]
	undetected_chromedriver!GetHandleVerifier [0x824015+19055]
	undetected_chromedriver!GetHandleVerifier [0x80d65f+269f]
	KERNEL32!BaseThreadInitThunk [0x76bffcc9+19]
	ntdll!RtlGetAppContainerNamedObjectPath [0x7784843e+11e]
	ntdll!RtlGetAppContainerNamedObjectPath [0x7784840e+ee]
```
<!-- END_BUG:BUG_20260604_013357_001 -->


## 🐛 [BUG_20260604_013838_001] — start
- **Thời gian**: `2026-06-04 01:38:38`
- **Module**: `core.browser`
- **Mức độ**: `CRITICAL`
- **Loại lỗi**: `WebDriverException`
- **Thông báo lỗi**: `Message: unknown error: cannot connect to chrome at 127.0.0.1:60382
from chrome not reachable
Stacktrace:
	GetHandleVerifier [0x004EC113+48259]
	(No symbol) [0x0047CA41]
	(No symbol) [0x003708A3]
	(No symbol) [0x0035F924]
	(No symbol) [0x003A1E2C]
	(No symbol) [0x00399320]
	(No symbol) [0x00399167]
	(No symbol) [0x003DA8BA]
	(No symbol) [0x003DA0EA]
	(No symbol) [0x003D0B36]
	(No symbol) [0x003A570D]
	(No symbol) [0x003A62CD]
	GetHandleVerifier [0x007A65A3+2908435]
	GetHandleVerifier [0x007E3BBB+3159851]
	GetHandleVerifier [0x005850CB+674875]
	GetHandleVerifier [0x0058B28C+699900]
	(No symbol) [0x00486244]
	(No symbol) [0x00482298]
	(No symbol) [0x0048242C]
	(No symbol) [0x00474BB0]
	BaseThreadInitThunk [0x76BFFCC9+25]
	RtlGetAppContainerNamedObjectPath [0x7784843E+286]
	RtlGetAppContainerNamedObjectPath [0x7784840E+238]
`
- **Context**:
  - **headless**: `False`
  - **proxy**: `none`
- **Traceback**:
```
Traceback (most recent call last):
  File "E:\Gams-ToolAutoBcgame\core\browser.py", line 122, in start
    self.driver = uc.Chrome(
                  ^^^^^^^^^^
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\undetected_chromedriver\__init__.py", line 466, in __init__
    super(Chrome, self).__init__(
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\selenium\webdriver\chrome\webdriver.py", line 45, in __init__
    super().__init__(
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\selenium\webdriver\chromium\webdriver.py", line 61, in __init__
    super().__init__(command_executor=executor, options=options)
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\selenium\webdriver\remote\webdriver.py", line 208, in __init__
    self.start_session(capabilities)
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\undetected_chromedriver\__init__.py", line 724, in start_session
    super(selenium.webdriver.chrome.webdriver.WebDriver, self).start_session(
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\selenium\webdriver\remote\webdriver.py", line 292, in start_session
    response = self.execute(Command.NEW_SESSION, caps)["value"]
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\selenium\webdriver\remote\webdriver.py", line 347, in execute
    self.error_handler.check_response(response)
  File "C:\Users\admin\AppData\Local\Programs\Python\Python311\Lib\site-packages\selenium\webdriver\remote\errorhandler.py", line 229, in check_response
    raise exception_class(message, screen, stacktrace)
selenium.common.exceptions.WebDriverException: Message: unknown error: cannot connect to chrome at 127.0.0.1:60382
from chrome not reachable
Stacktrace:
	GetHandleVerifier [0x004EC113+48259]
	(No symbol) [0x0047CA41]
	(No symbol) [0x003708A3]
	(No symbol) [0x0035F924]
	(No symbol) [0x003A1E2C]
	(No symbol) [0x00399320]
	(No symbol) [0x00399167]
	(No symbol) [0x003DA8BA]
	(No symbol) [0x003DA0EA]
	(No symbol) [0x003D0B36]
	(No symbol) [0x003A570D]
	(No symbol) [0x003A62CD]
	GetHandleVerifier [0x007A65A3+2908435]
	GetHandleVerifier [0x007E3BBB+3159851]
	GetHandleVerifier [0x005850CB+674875]
	GetHandleVerifier [0x0058B28C+699900]
	(No symbol) [0x00486244]
	(No symbol) [0x00482298]
	(No symbol) [0x0048242C]
	(No symbol) [0x00474BB0]
	BaseThreadInitThunk [0x76BFFCC9+25]
	RtlGetAppContainerNamedObjectPath [0x7784843E+286]
	RtlGetAppContainerNamedObjectPath [0x7784840E+238]
```
<!-- END_BUG:BUG_20260604_013838_001 -->

