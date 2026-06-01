import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

class SheetWriter:
    def __init__(self, sheet_name):
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Safe initialization in case credentials.json doesn't exist yet
        try:
            if os.path.exists("credentials.json"):
                creds = ServiceAccountCredentials.from_json_keyfile_name(
                    "credentials.json",
                    scope
                )
                client = gspread.authorize(creds)
                self.sheet = client.open(sheet_name).sheet1
            else:
                print("Chưa cấu hình credentials.json cho Google Sheets.")
                self.sheet = None
        except Exception as e:
            print(f"Lỗi khởi tạo SheetWriter: {e}")
            self.sheet = None

    def write_rows(self, rows):
        if not self.sheet:
            print(f"[SheetWriter] Giả lập ghi dũ liệu (Do thiếu credentials): {rows}")
            return
            
        try:
            for r in rows:
                self.sheet.append_row(r)
        except Exception as e:
            print(f"Lỗi khi ghi dữ liệu vào Sheet: {e}")
