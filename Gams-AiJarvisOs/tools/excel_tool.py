import os
import csv
from datetime import datetime
from tools.tool_registry import tool

@tool(name="save_to_excel", description="Lưu dữ liệu vào file Excel (.csv/xlsx giả lập) để báo cáo doanh nghiệp.")
def save_to_excel(data: list, filename: str = None):
    """
    Chuyển đổi list data thành file báo cáo.
    """
    if not filename:
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    if not filename.endswith(".csv"):
        filename += ".csv"

    os.makedirs("data/exports", exist_ok=True)
    file_path = os.path.join("data/exports", filename)
    
    try:
        if not data:
            return "Lỗi: Không có dữ liệu để lưu."
            
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            # Assuming data[0] is header if it's a list of lists
            writer.writerows(data)
            
        return f"Đã xuất dữ liệu thành công tại: {file_path}"
    except Exception as e:
        return f"Lỗi khi lưu file: {str(e)}"
