## Quy Trình Hoạt Động (V2)
1.  **Quét Wap.vn:** Lấy danh sách trận đấu có nhận định "TÀI".
2.  **Chọn Ngẫu Nhiên:** Chọn 1 trận từ danh sách (Giả lập Wheel of Names).
3.  **Tìm Kiếm & Khớp Tên:** Tìm trận trên BCGame và dùng Fuzzy Matching (>80%) để khớp tên đội bóng.
4.  **Đặt Cược All-in:** Tìm kèo Tài có odds thấp nhất và đặt cược toàn bộ số dư.
5.  **Theo Dõi & Báo Cáo:** Check kết quả từ Flashscore.vn và ghi vào Google Sheets.

## Cấu Hình Google Sheets
1.  Truy cập Google Cloud Console, tạo Service Account và tải file `credentials.json`.
2.  Copy file này vào thư mục `data/` của tool.
3.  Chia sẻ (Share) file Google Sheet của bạn cho email của Service Account (có trong file json).
4.  Dán URL của Google Sheet vào ô tương ứng trên giao diện tool.

Tool tự động cá cược bóng đá trên BCGame (bcvn2.com) với giao diện GUI hiện đại.

## Tính Năng
- **Tự động đăng nhập:** Hỗ trợ phone/password và quản lý session.
- **Scraper Real-time:** Tự động quét kèo 1X2 từ trang thể thao BCGame.
- **Chiến thuật đa dạng:**
  - Flat Bet (Cố định)
  - Martingale (Nhân đôi khi thua)
  - Fibonacci (Tăng theo dãy số)
  - D'Alembert (Tăng/giảm 1 đơn vị)
- **Quản lý rủi ro:** Cài đặt Stop-loss và Take-profit.
- **Giao diện hiện đại:** Dark mode, Log real-time, Thống kê chi tiết.

## Cài Đặt

1. Cài đặt Python 3.10+
2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

## Cách Sử Dụng

1. Chạy file `main.py`:
```bash
python main.py
```
2. Nhập số điện thoại và mật khẩu BCGame.
3. Cấu hình số tiền cược, chiến thuật và các giới hạn SL/TP.
4. Nhấn **BẮT ĐẦU**.

## Lưu Ý
- Tool sử dụng Selenium (undetected-chromedriver) để bypass bot detection.
- Đảm bảo bạn có kết nối internet ổn định.
- **Cảnh báo:** Cá cược có rủi ro, hãy sử dụng tool một cách có trách nhiệm.

## Cấu Trúc Thư Mục
- `core/`: Chứa các module điều khiển trình duyệt, login, scraper và betting engine.
- `gui/`: Chứa các thành phần giao diện người dùng.
- `strategies/`: Chứa logic các thuật toán đặt cược.
- `data/`: Chứa cấu hình và lịch sử cược.