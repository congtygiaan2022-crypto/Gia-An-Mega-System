def generate_tiktok_report(data: dict) -> str:
    report = f"""
BÁO CÁO TIKTOK ADS – TỰ ĐỘNG

Tổng quan chiến dịch: {data.get('campaign', 'N/A')}

Tổng ngân sách: {data.get('spend', 0)}
Impressions: {data.get('impressions', 0)}
Clicks: {data.get('clicks', 0)}
CTR: {data.get('ctr', '0%')}
Conversions: {data.get('conversions', 0)}
CPA: {data.get('cpa', 0)}

Phân tích hiệu quả:
Chiến dịch có tỷ lệ CTR là {data.get('ctr', '0%')}, cho thấy nội dung video
có khả năng thu hút người dùng tốt hay không tùy cấu hình ngành hàng.

Với {data.get('conversions', 0)} chuyển đổi và mức CPA là {data.get('cpa', 0)},
hiệu suất có thể đánh giá dựa trên biên lợi nhuận sản phẩm.

Đề xuất tối ưu:
• Test thêm các video (creatives) mới.
• Tăng ngân sách cho nhóm quảng cáo đang có hiệu quả tốt.
• Tối ưu lại 3 giây đầu tiên (hook) của video để tăng tỷ lệ giữ chân.
"""
    return report
