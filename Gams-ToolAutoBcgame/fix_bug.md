# ✅ FIX BUG — Lịch sử các lỗi đã sửa

> File này ghi lại toàn bộ lỗi đã được phát hiện và sửa thành công.
> Đây là tài liệu để **user review** các thay đổi đã được thực hiện.

---

## ✅ [BUG_20260523_110124_001] — start  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-05-23 11:01:24`
- **Thời gian sửa**: `2026-05-26 04:03:57`
- **Module**: `core.browser`
- **Loại lỗi**: `SessionNotCreatedException`
- **Thông báo lỗi**: `Message: session not created: cannot connect to chrome at 127.0.0.1:50857
from session not created: This version of ChromeDriver only supports Chrome version v1.0.0
Current browser version is 148.0.7778.179
Stacktrace:
	undetected_chromedriver!GetHandleVerifier [0xa93283+10543]
	undetected_chromedriver!GetHandleVerifier [0xa932c4+10584]
	undetected_chromedriver!(No symbol) [0x88a6f0]
	undetected_chromedriver!(No symbol) [0x8c64e2]
	undetected_chromedriver!(No symbol) [0x8c551c]
	undetected_chromedriver!(No symbol) [0x8bb615]
	undetected_chromedriver!(No symbol) [0x8bb436]
	undetected_chromedriver!(No symbol) [0x901d4f]
	undetected_chromedriver!(No symbol) [0x901567]
	undetected_chromedriver!(No symbol) [0x8f5de6]
	undetected_chromedriver!(No symbol) [0x8c90d9]
	undetected_chromedriver!(No symbol) [0x8c9ea4]
	undetected_chromedriver!GetHandleVerifier [0xd161ea+2934aa]
	undetected_chromedriver!GetHandleVerifier [0xd1176d+28ea2d]
	undetected_chromedriver!GetHandleVerifier [0xd324ab+2af76b]
	undetected_chromedriver!GetHandleVerifier [0xaac796+29a56]
	undetected_chromedriver!GetHandleVerifier [0xab3a1d+30cdd]
	undetected_chromedriver!GetHandleVerifier [0xa9bba8+18e68]
	undetected_chromedriver!GetHandleVerifier [0xa9bd55+19015]
	undetected_chromedriver!GetHandleVerifier [0xa84c3f+1eff]
	KERNEL32!BaseThreadInitThunk [0x7647fcc9+19]
	ntdll!RtlGetAppContainerNamedObjectPath [0x7734843e+11e]
	ntdll!RtlGetAppContainerNamedObjectPath [0x7734840e+ee]`
- **Ghi chú sửa lỗi**: Đã thêm phát hiện phiên bản Chrome từ Registry và truyền version_main cho undetected_chromedriver để tránh tải sai bản driver
---

## ✅ [BUG_20260526_022322_001] — simulated_task  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-05-26 02:23:22`
- **Thời gian sửa**: `2026-05-26 04:05:16`
- **Module**: `core.session`
- **Loại lỗi**: `ValueError`
- **Thông báo lỗi**: `Simulated crash in Bcgame SessionManager`
- **Ghi chú sửa lỗi**: Lỗi mô phỏng - đánh dấu đã sửa để làm sạch danh sách
---

## ✅ [BUG_20260526_022350_001] — simulated_task  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-05-26 02:23:50`
- **Thời gian sửa**: `2026-05-26 04:05:18`
- **Module**: `core.session`
- **Loại lỗi**: `ValueError`
- **Thông báo lỗi**: `Simulated logic crash in Bcgame SessionManager`
- **Ghi chú sửa lỗi**: Lỗi mô phỏng - đánh dấu đã sửa để làm sạch danh sách
---

## ✅ [BUG_20260526_060258_001] — simulated_task  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-05-26 06:02:58`
- **Thời gian sửa**: `2026-05-26 06:03:05`
- **Module**: `core.session`
- **Loại lỗi**: `ValueError`
- **Thông báo lỗi**: `Simulated logic crash in Bcgame SessionManager`
- **Ghi chú sửa lỗi**: Simulated task marked fixed.
---

## ✅ [BUG_20260526_060451_001] — simulated_task  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-05-26 06:04:51`
- **Thời gian sửa**: `2026-05-26 07:03:53`
- **Module**: `core.session`
- **Loại lỗi**: `ValueError`
- **Thông báo lỗi**: `Simulated logic crash in Bcgame SessionManager`
- **Ghi chú sửa lỗi**: Simulated bug marked as resolved.
---

## ✅ [BUG_20260526_080331_001] — simulated_task  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-05-26 08:03:31`
- **Thời gian sửa**: `2026-05-26 08:03:37`
- **Module**: `core.session`
- **Loại lỗi**: `ValueError`
- **Thông báo lỗi**: `Simulated logic crash in Bcgame SessionManager`
- **Ghi chú sửa lỗi**: Simulated logic crash in Bcgame SessionManager resolved (mock task)
---

## ✅ [BUG_20260526_140435_001] — simulated_task  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-05-26 14:04:35`
- **Thời gian sửa**: `2026-05-26 14:06:14`
- **Module**: `core.session`
- **Loại lỗi**: `ValueError`
- **Thông báo lỗi**: `Simulated logic crash in Bcgame SessionManager`
- **Ghi chú sửa lỗi**: Simulated logic crash resolved.
---

## ✅ [BUG_20260527_020733_001] — start  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-05-27 02:07:33`
- **Thời gian sửa**: `2026-05-28 15:06:40`
- **Module**: `core.browser`
- **Loại lỗi**: `SessionNotCreatedException`
- **Thông báo lỗi**: `Message: session not created: cannot connect to chrome at 127.0.0.1:54958
from chrome not reachable
Stacktrace:
	undetected_chromedriver!GetHandleVerifier [0xbbb593+105d3]
	undetected_chromedriver!GetHandleVerifier [0xbbb6c4+10704]
	undetected_chromedriver!(No symbol) [0x9c1cde]
	undetected_chromedriver!(No symbol) [0x9b5478]
	undetected_chromedriver!(No symbol) [0x9fcb32]
	undetected_chromedriver!(No symbol) [0x9f2e25]
	undetected_chromedriver!(No symbol) [0x9f2c46]
	undetected_chromedriver!(No symbol) [0xa3947f]
	undetected_chromedriver!(No symbol) [0xa38c97]
	undetected_chromedriver!(No symbol) [0xa2d516]
	undetected_chromedriver!(No symbol) [0xa008e9]
	undetected_chromedriver!(No symbol) [0xa016a4]
	undetected_chromedriver!GetHandleVerifier [0xe43014+298054]
	undetected_chromedriver!GetHandleVerifier [0xe3e603+293643]
	undetected_chromedriver!GetHandleVerifier [0xe5ea05+2b3a45]
	undetected_chromedriver!GetHandleVerifier [0xbd54e8+2a528]
	undetected_chromedriver!GetHandleVerifier [0xbdcd1d+31d5d]
	undetected_chromedriver!GetHandleVerifier [0xbc3e68+18ea8]
	undetected_chromedriver!GetHandleVerifier [0xbc4015+19055]
	undetected_chromedriver!GetHandleVerifier [0xbad65f+269f]
	KERNEL32!BaseThreadInitThunk [0x7624fcc9+19]
	ntdll!RtlGetAppContainerNamedObjectPath [0x774c843e+11e]
	ntdll!RtlGetAppContainerNamedObjectPath [0x774c840e+ee]`
- **Ghi chú sửa lỗi**: Thay doi use_subprocess=True va loc trung lap chrome process bang psutil
---

## ✅ [BUG_20260527_020930_001] — start  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-05-27 02:09:30`
- **Thời gian sửa**: `2026-05-28 15:06:44`
- **Module**: `core.browser`
- **Loại lỗi**: `SessionNotCreatedException`
- **Thông báo lỗi**: `Message: session not created: cannot connect to chrome at 127.0.0.1:55145
from chrome not reachable
Stacktrace:
	undetected_chromedriver!GetHandleVerifier [0x8fb593+105d3]
	undetected_chromedriver!GetHandleVerifier [0x8fb6c4+10704]
	undetected_chromedriver!(No symbol) [0x701cde]
	undetected_chromedriver!(No symbol) [0x6f5478]
	undetected_chromedriver!(No symbol) [0x73cb32]
	undetected_chromedriver!(No symbol) [0x732e25]
	undetected_chromedriver!(No symbol) [0x732c46]
	undetected_chromedriver!(No symbol) [0x77947f]
	undetected_chromedriver!(No symbol) [0x778c97]
	undetected_chromedriver!(No symbol) [0x76d516]
	undetected_chromedriver!(No symbol) [0x7408e9]
	undetected_chromedriver!(No symbol) [0x7416a4]
	undetected_chromedriver!GetHandleVerifier [0xb83014+298054]
	undetected_chromedriver!GetHandleVerifier [0xb7e603+293643]
	undetected_chromedriver!GetHandleVerifier [0xb9ea05+2b3a45]
	undetected_chromedriver!GetHandleVerifier [0x9154e8+2a528]
	undetected_chromedriver!GetHandleVerifier [0x91cd1d+31d5d]
	undetected_chromedriver!GetHandleVerifier [0x903e68+18ea8]
	undetected_chromedriver!GetHandleVerifier [0x904015+19055]
	undetected_chromedriver!GetHandleVerifier [0x8ed65f+269f]
	KERNEL32!BaseThreadInitThunk [0x7624fcc9+19]
	ntdll!RtlGetAppContainerNamedObjectPath [0x774c843e+11e]
	ntdll!RtlGetAppContainerNamedObjectPath [0x774c840e+ee]`
- **Ghi chú sửa lỗi**: Thay doi use_subprocess=True va loc trung lap chrome process bang psutil
---

## ✅ [BUG_20260527_021644_001] — start  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-05-27 02:16:44`
- **Thời gian sửa**: `2026-05-28 15:06:48`
- **Module**: `core.browser`
- **Loại lỗi**: `SessionNotCreatedException`
- **Thông báo lỗi**: `Message: session not created: cannot connect to chrome at 127.0.0.1:56386
from chrome not reachable
Stacktrace:
	undetected_chromedriver!GetHandleVerifier [0x5db593+105d3]
	undetected_chromedriver!GetHandleVerifier [0x5db6c4+10704]
	undetected_chromedriver!(No symbol) [0x3e1cde]
	undetected_chromedriver!(No symbol) [0x3d5478]
	undetected_chromedriver!(No symbol) [0x41cb32]
	undetected_chromedriver!(No symbol) [0x412e25]
	undetected_chromedriver!(No symbol) [0x412c46]
	undetected_chromedriver!(No symbol) [0x45947f]
	undetected_chromedriver!(No symbol) [0x458c97]
	undetected_chromedriver!(No symbol) [0x44d516]
	undetected_chromedriver!(No symbol) [0x4208e9]
	undetected_chromedriver!(No symbol) [0x4216a4]
	undetected_chromedriver!GetHandleVerifier [0x863014+298054]
	undetected_chromedriver!GetHandleVerifier [0x85e603+293643]
	undetected_chromedriver!GetHandleVerifier [0x87ea05+2b3a45]
	undetected_chromedriver!GetHandleVerifier [0x5f54e8+2a528]
	undetected_chromedriver!GetHandleVerifier [0x5fcd1d+31d5d]
	undetected_chromedriver!GetHandleVerifier [0x5e3e68+18ea8]
	undetected_chromedriver!GetHandleVerifier [0x5e4015+19055]
	undetected_chromedriver!GetHandleVerifier [0x5cd65f+269f]
	KERNEL32!BaseThreadInitThunk [0x7624fcc9+19]
	ntdll!RtlGetAppContainerNamedObjectPath [0x774c843e+11e]
	ntdll!RtlGetAppContainerNamedObjectPath [0x774c840e+ee]`
- **Ghi chú sửa lỗi**: Thay doi use_subprocess=True va loc trung lap chrome process bang psutil
---

## ✅ [BUG_20260527_022611_001] — start  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-05-27 02:26:11`
- **Thời gian sửa**: `2026-05-28 15:06:50`
- **Module**: `core.browser`
- **Loại lỗi**: `SessionNotCreatedException`
- **Thông báo lỗi**: `Message: session not created: cannot connect to chrome at 127.0.0.1:58579
from chrome not reachable
Stacktrace:
	undetected_chromedriver!GetHandleVerifier [0xe8b593+105d3]
	undetected_chromedriver!GetHandleVerifier [0xe8b6c4+10704]
	undetected_chromedriver!(No symbol) [0xc91cde]
	undetected_chromedriver!(No symbol) [0xc85478]
	undetected_chromedriver!(No symbol) [0xcccb32]
	undetected_chromedriver!(No symbol) [0xcc2e25]
	undetected_chromedriver!(No symbol) [0xcc2c46]
	undetected_chromedriver!(No symbol) [0xd0947f]
	undetected_chromedriver!(No symbol) [0xd08c97]
	undetected_chromedriver!(No symbol) [0xcfd516]
	undetected_chromedriver!(No symbol) [0xcd08e9]
	undetected_chromedriver!(No symbol) [0xcd16a4]
	undetected_chromedriver!GetHandleVerifier [0x1113014+298054]
	undetected_chromedriver!GetHandleVerifier [0x110e603+293643]
	undetected_chromedriver!GetHandleVerifier [0x112ea05+2b3a45]
	undetected_chromedriver!GetHandleVerifier [0xea54e8+2a528]
	undetected_chromedriver!GetHandleVerifier [0xeacd1d+31d5d]
	undetected_chromedriver!GetHandleVerifier [0xe93e68+18ea8]
	undetected_chromedriver!GetHandleVerifier [0xe94015+19055]
	undetected_chromedriver!GetHandleVerifier [0xe7d65f+269f]
	KERNEL32!BaseThreadInitThunk [0x7624fcc9+19]
	ntdll!RtlGetAppContainerNamedObjectPath [0x774c843e+11e]
	ntdll!RtlGetAppContainerNamedObjectPath [0x774c840e+ee]`
- **Ghi chú sửa lỗi**: Thay doi use_subprocess=True va loc trung lap chrome process bang psutil
---

## ✅ [BUG_20260604_002417_001] — main  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-06-04 00:24:17`
- **Thời gian sửa**: `2026-06-04 00:26:53`
- **Module**: `gui.main_window`
- **Loại lỗi**: `NameError`
- **Thông báo lỗi**: `name 'selftitle' is not defined`
- **Ghi chú sửa lỗi**: Đã đổi lệnh gọi `selftitle(...)` thành `self.title(...)` trong khởi tạo MainWindow của file [main_window.py](file:///e:/Gams-ToolAutoBcgame/gui/main_window.py#L28).
---

## ✅ [BUG_20260604_013357_001] — start  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-06-04 01:33:57`
- **Thời gian sửa**: `2026-06-04 01:39:18`
- **Module**: `core.browser`
- **Loại lỗi**: `SessionNotCreatedException`
- **Thông báo lỗi**: `Message: session not created: cannot connect to chrome at 127.0.0.1:59989`
- **Ghi chú sửa lỗi**:
  1. Tải và cài đặt bản Chrome portable v124 bằng cách chạy lại `download_chrome.py`.
  2. Sửa [browser.py](file:///e:/Gams-ToolAutoBcgame/core/browser.py#L101-L122) để tự động phát hiện và ưu tiên chạy bản Chrome portable v124 với `version_main=124` nếu tồn tại, tránh xung đột phiên bản Chrome hệ thống (v148/v149).
  3. Đổi tên thư mục profile cũ `chrome_profile_v2` sang `chrome_profile_v2_old` vì nó đã bị ghi đè dữ liệu không tương thích ngược bởi Chrome hệ thống bản mới (v148). Khi chạy lại, Chrome v124 sẽ khởi tạo profile mới hoàn toàn sạch sẽ.
---

## ✅ [BUG_20260604_013838_001] — start  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-06-04 01:38:38`
- **Thời gian sửa**: `2026-06-04 01:39:23`
- **Module**: `core.browser`
- **Loại lỗi**: `WebDriverException`
- **Thông báo lỗi**: `Message: unknown error: cannot connect to chrome` (Do lỗi kẹt profile không tương thích ngược ở trên)
- **Ghi chú sửa lỗi**: Tương tự như sửa đổi ở trên, việc dọn dẹp và reset profile `chrome_profile_v2` đã giải quyết triệt để lỗi kết nối này.
---

## ✅ [BUG_20260604_014142_001] — auto_bet  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-06-04 01:41:42`
- **Thời gian sửa**: `2026-06-04 01:42:18`
- **Module**: `gui.main_window`
- **Loại lỗi**: `NoSuchWindowException`
- **Thông báo lỗi**: `Message: no such window: target window already closed`
- **Ghi chú sửa lỗi**:
  1. Thêm phương thức `check_alive()` vào [browser.py](file:///e:/Gams-ToolAutoBcgame/core/browser.py#L178-L195) để kiểm tra xem cửa sổ Chrome có đang mở và kết nối driver còn sống hay không.
  2. Tích hợp `check_alive()` vào các luồng cược tự động, theo dõi kết quả và báo cáo trong [main_window.py](file:///e:/Gams-ToolAutoBcgame/gui/main_window.py). Nếu phát hiện cửa sổ Chrome bị đóng (do người dùng tắt thủ công hoặc crash), luồng cược/care sẽ tự động dừng lại và hiển thị cảnh báo thay vì chạy lặp vô hạn gây spam log lỗi.
---

## ✅ [BUG_20260607_231257_001] — clear_bet_slip  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-06-07 23:12:57`
- **Thời gian sửa**: `2026-06-07 23:18:43`
- **Module**: `core.bettor`
- **Loại lỗi**: `LogicError`
- **Thông báo lỗi**: Phiếu cược cũ chứa kèo không hợp lệ (Odds ngoài khoảng) không được xóa sạch, dẫn đến việc đặt cược xiên 2 trận ở vòng tiếp theo.
- **Ghi chú sửa lỗi**:
  - Viết lại hàm `clearAll()` trong `clear_bet_slip` của [bettor.py](file:///e:/Gams-ToolAutoBcgame/core/bettor.py#L149-L215) để tìm kiếm nút "Xóa tất cả" / "Clear all" trực tiếp trong toàn bộ Shadow DOM mà không phụ thuộc vào chuỗi ký tự lọc `" vs "` không ổn định.
  - Thêm phương pháp dự phòng tự động quét và nhấn từng nút Đóng (dấu X) đơn lẻ nếu không thấy nút xóa tất cả.
---

## ✅ [BUG_20260607_231257_002] — place_bet  `ĐÃ SỬA`
- **Thời gian phát hiện**: `2026-06-07 23:12:57`
- **Thời gian sửa**: `2026-06-07 23:18:27`
- **Module**: `core.bettor`
- **Loại lỗi**: `UIBindingError`
- **Thông báo lỗi**: Nhận diện đúng số tiền cược nhưng không điền được vào ô cược thực tế trên giao diện BCGame.
- **Ghi chú sửa lỗi**:
  - Khắc phục việc bộ chọn nhắm nhầm vào các thẻ `div` bọc ngoài có class chứa "stake" bằng cách lọc chặt chẽ chỉ lấy phần tử `<input>` thực sự trong `_find_bet_elements()` của [bettor.py](file:///e:/Gams-ToolAutoBcgame/core/bettor.py#L216-L270).
  - Sử dụng cơ chế Native Input Setter (`Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set`) để gán giá trị cược giúp vượt qua cơ chế ảo hóa State của các framework hiện đại (React/Vue/Svelte), đồng thời dispatch đầy đủ các sự kiện `input`, `change`, và `blur`.
---