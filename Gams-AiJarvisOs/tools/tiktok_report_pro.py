import os
import random
from datetime import datetime
from tools.tool_registry import tool
from tools.excel_tool import save_to_excel

@tool(name="bao_cao_ads_tiktok", description="Tạo báo cáo quảng cáo TikTok chuyên sâu và xuất file Excel.")
def bao_cao_ads_tiktok(campaign_name: str = "Chiến dịch chung"):
    """
    Quy trình tự động: Phân tích -> Tổng hợp -> Xuất Excel.
    """
    # 1. Giả lập phân tích dữ liệu chuyên sâu
    metrics = {
        "Chi tiêu": random.uniform(5000000, 20000000),
        "Lượt xem": random.randint(100000, 500000),
        "Click": random.randint(5000, 20000),
        "Chuyển đổi": random.randint(100, 500),
    }
    
    ctr = (metrics["Click"] / metrics["Lượt xem"]) * 100
    cvr = (metrics["Chuyển đổi"] / metrics["Click"]) * 100
    cpc = metrics["Chi tiêu"] / metrics["Click"]
    
    # 2. Chuẩn bị dữ liệu cho Excel
    excel_data = [
        ["Chỉ số", "Giá trị", "Đơn vị"],
        ["Chi tiêu", f"{metrics['Chi tiêu']:,}", "VND"],
        ["CTR", f"{ctr:.2f}", "%"],
        ["CVR", f"{cvr:.2f}", "%"],
        ["CPC", f"{cpc:,.0f}", "VND"],
        ["Lượt mua", metrics["Chuyển đổi"], "Đơn hàng"]
    ]
    
    # 3. Xuất file
    filename = f"TikTok_Report_{campaign_name}_{datetime.now().strftime('%d%m%Y')}.csv"
    save_res = save_to_excel(excel_data, filename)
    
    summary = f"""
    📌 BÁO CÁO CHIẾN DỊCH: {campaign_name}
    - Tổng chi: {metrics['Chi tiêu']:,.0f} VND
    - Tỷ lệ Click (CTR): {ctr:.2f}%
    - Tỷ lệ Chốt (CVR): {cvr:.2f}%
    - Giá mỗi click (CPC): {cpc:,.0f} VND
    -------------------
    {save_res}
    """
    return summary
