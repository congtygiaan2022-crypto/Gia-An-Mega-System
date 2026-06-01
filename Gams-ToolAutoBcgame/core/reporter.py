"""
Reporter - Ghi báo cáo ra Google Sheets theo định dạng All-in
"""
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from typing import Dict
from loguru import logger
import os

class GoogleSheetsReporter:
    """Xử lý ghi báo cáo vào Google Sheets"""
    
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    def __init__(self, spreadsheet_url: str, credentials_path: str = "data/credentials.json"):
        self.spreadsheet_url = spreadsheet_url
        self.credentials_path = credentials_path
        self.client = None
        self.sheet = None

    def _authenticate(self) -> bool:
        if not os.path.exists(self.credentials_path):
            logger.error(f"❌ Không tìm thấy file credentials tại {self.credentials_path}")
            return False
            
        try:
            creds = Credentials.from_service_account_file(self.credentials_path, scopes=self.SCOPES)
            self.client = gspread.authorize(creds)
            spreadsheet = self.client.open_by_url(self.spreadsheet_url)
            self.sheet = spreadsheet.get_worksheet(0)
            return True
        except Exception as e:
            logger.error(f"❌ Lỗi xác thực Google Sheets: {e}")
            return False

    def add_bet_report(self, data: Dict):
        """
        Thêm báo cáo đặt cược mới
        data: {
            'match': str,
            'capital': float (vốn),
            'stake': float (tiền cược),
            'odds': float (tỷ lệ),
            'date': str
        }
        Cột: [Ngày, Trận Đấu, Tiền Vốn, Tiền Cược, Tỉ Lệ, Trạng Thái, Tổng Kết]
        """
        if not self.sheet and not self._authenticate():
            return False
        if not self.sheet:
            logger.error("❌ Sheet vẫn None sau khi xác thực — kiểm tra credentials/spreadsheet URL")
            return False

        try:
            now_str = data.get('date', datetime.now().strftime("%d/%m/%Y %H:%M"))
            row = [
                now_str,
                data.get('match', 'N/A'),
                data.get('capital', 0),
                data.get('stake', 0),
                data.get('odds', 0),
                "ĐANG CHỜ",
                "..."
            ]
            self.sheet.insert_row(row, 2)
            return True
        except Exception as e:
            logger.error(f"❌ Lỗi ghi báo cáo: {e}")
            return False

    def finalize_report(self, match_name: str, won: bool, odds: float, stake: float):
        """Cập nhật kết quả cuối cùng: Thắng -> Vốn * Tỉ lệ, Thua -> 0"""
        if not self.sheet and not self._authenticate():
            return False
        if not self.sheet:
            logger.error("❌ Sheet vẫn None sau khi xác thực — kiểm tra credentials/spreadsheet URL")
            return False

        try:
            records = self.sheet.get_all_values()
            for i, row in enumerate(records):
                if i == 0: continue
                if len(row) >= 6 and match_name in row[1] and row[5] == "ĐANG CHỜ":
                    status = "THẮNG" if won else "THUA"
                    total = stake * (odds - 1) if won else -stake
                    
                    # Cập nhật cột Trạng Thái (index 5) và Tổng Kết (index 6)
                    self.sheet.update_cell(i + 1, 6, status)
                    self.sheet.update_cell(i + 1, 7, total)
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Lỗi cập nhật báo cáo: {e}")
            return False
