import requests

class TikTokAdsAPI:
    def __init__(self, access_token: str, advertiser_id: str):
        self.token = access_token
        self.advertiser_id = advertiser_id

    def get_campaign_report(self):
        url = "https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/"
        headers = {
            "Access-Token": self.token
        }
        params = {
            "advertiser_id": self.advertiser_id,
            "report_type": "BASIC",
            "dimensions": ["campaign_id"],
            "metrics": [
                "spend",
                "impressions",
                "clicks",
                "conversions"
            ]
        }
        try:
            r = requests.get(url, headers=headers, params=params)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e), "data": {"list": []}}
