import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from core.logger import get_module_logger

logger = get_module_logger("SheetWriter")

class SheetWriter:
    def __init__(self):
        self.sheet = None
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            creds_path = "credentials.json"
            if os.path.exists(creds_path):
                creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
                client = gspread.authorize(creds)
                self.sheet = client.open("Ads Report").sheet1
            else:
                logger.warning("credentials.json not found. SheetWriter will be disabled.")
        except Exception as e:
            logger.error(f"Failed to init SheetWriter: {e}")

    def write_row(self, data: list):
        if self.sheet:
            try:
                self.sheet.append_row(data)
            except Exception as e:
                logger.error(f"Failed to append row: {e}")
        else:
            logger.warning(f"Simulating append_row (no credentials): {data}")
