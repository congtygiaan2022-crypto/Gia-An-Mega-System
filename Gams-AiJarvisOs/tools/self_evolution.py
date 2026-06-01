import os
from tools.tool_registry import tool

@tool(name="read_project_file", description="Đọc nội dung của một file trong dự án Javis để phân tích code.")
def read_project_file(file_path: str):
    """
    Đọc file từ thư mục gốc của dự án.
    Example: tools/self_evolution.py
    """
    # Security: restrict to project dir
    base_dir = os.getcwd()
    abs_path = os.path.abspath(os.path.join(base_dir, file_path))
    
    if not abs_path.startswith(base_dir):
        return "Lỗi: Không được phép truy cập ngoài thư mục dự án."
    
    if not os.path.exists(abs_path):
        return f"Lỗi: File {file_path} không tồn tại."
        
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Lỗi khi đọc file: {str(e)}"

@tool(name="write_project_file", description="Ghi nội dung mới vào một file trong dự án Javis (Tự nâng cấp code).")
def write_project_file(file_path: str, content: str):
    """
    Ghi đè nội dung file. Cần cẩn thận khi sử dụng.
    """
    base_dir = os.getcwd()
    abs_path = os.path.abspath(os.path.join(base_dir, file_path))
    
    if not abs_path.startswith(base_dir):
        return "Lỗi: Không được phép ghi file ngoài thư mục dự án."
        
    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Thành công: Đã cập nhật file {file_path}. Hệ thống sẽ tự reload nếu cần."
    except Exception as e:
        return f"Lỗi khi ghi file: {str(e)}"
