from .tiktok_ads_api import TikTokAdsAPI
from .sheet_writer import SheetWriter
from .report_generator import ReportGenerator
from core.api_settings import APISettings

class AdsAutomation:
    def __init__(self, tk_account="tiktok_A", sh_account="sheet_A"):
        settings = APISettings()
        tk = settings.get_account("tiktok_ads", tk_account)
        
        self.tiktok = TikTokAdsAPI(
            token=tk.get("access_token", ""),
            advertiser_id=tk.get("advertiser_id", "")
        )
        
        sh = settings.get_account("google_sheets", sh_account)
        sheet_desc = sh.get("description", "Ads Report")
        
        self.sheet = SheetWriter(sheet_desc)
        self.report = ReportGenerator()

    def run(self):
        print("Fetching TikTok Ads data...")
        data = self.tiktok.fetch()
        
        if "data" not in data or "list" not in data["data"]:
            print(f"Không có dữ liệu Ads hoặc lỗi API: {data}")
            return

        campaigns = data["data"]["list"]
        rows = []

        for c in campaigns:
            rows.append([
                c.get("campaign_id", ""),
                c.get("spend", 0),
                c.get("impressions", 0),
                c.get("clicks", 0),
                c.get("conversions", 0)
            ])

        if rows:
            print("Ghi dữ liệu vào Google Sheet...")
            self.sheet.write_rows(rows)

            print("Tạo báo cáo tổng hợp...")
            report_text = self.report.generate(campaigns)
            print(report_text)
        else:
            print("Không có chiến dịch nào để báo cáo.")
