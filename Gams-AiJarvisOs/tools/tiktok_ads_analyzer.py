import os
import random
from tools.tool_registry import tool

@tool(name="analyze_tiktok_ads", description="Phân tích báo cáo chi tiêu quảng cáo TikTok từ file dữ liệu hoặc API.")
def analyze_tiktok_ads(fanpage_id: str, period: str = "last_7_days"):
    """
    Giả lập việc truy xuất và phân tích dữ liệu quảng cáo TikTok.
    Trong thực tế, tool này sẽ gọi TikTok Marketing API.
    """
    # Giả lập dữ liệu cho bản demo
    days = 7 if period == "last_7_days" else 30
    spend = random.uniform(1000, 5000)
    conversions = random.randint(50, 200)
    cpa = spend / conversions if conversions > 0 else 0
    
    report = f"""
    === BÁO CÁO QUẢNG CÁO TIKTOK - {fanpage_id} ===
    Giai đoạn: {period}
    Tổng chi tiêu: ${spend:.2f}
    Số lượt chuyển đổi: {conversions}
    CPA trung bình: ${cpa:.2f}
    Đánh giá: {'Hiệu quả tốt' if cpa < 25 else 'Cần tối ưu hóa nội dung'}
    =============================================
    """
    
    # Log to a local report file for Javis OS awareness
    os.makedirs("data/reports", exist_ok=True)
    report_path = f"data/reports/tiktok_{fanpage_id}_{period}.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
        
    return f"Đã trích xuất báo cáo tại {report_path}. {report}"

@tool(name="search_tiktok_trends", description="Tìm kiếm xu hướng TikTok cho một từ khóa cụ thể.")
def search_tiktok_trends(keyword: str):
    """
    Giả lập tìm kiếm trend theo keyword.
    """
    trends = ["#trending", f"#{keyword}_challenge", f"#{keyword}_review", "#tiktokmademebuyit"]
    return f"Các hashtag đang nổi cho '{keyword}': {', '.join(trends)}"
