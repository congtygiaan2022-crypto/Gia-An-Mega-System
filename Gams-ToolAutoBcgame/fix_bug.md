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
from session not created: This version of ChromeDriver only supports Chrome version 149
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
