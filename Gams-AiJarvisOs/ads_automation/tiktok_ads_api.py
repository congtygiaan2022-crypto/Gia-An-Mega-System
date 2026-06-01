import requests

class TikTokAdsAPI:
    def __init__(self, token, advertiser_id):
        self.token = token
        self.advertiser_id = advertiser_id

    def fetch(self):
        url = "https://business-api.tiktok.com/open_api/v1.3/report/integrated/get/"
        headers = {
            "Access-Token": self.token
        }
        params = {
            "advertiser_id": self.advertiser_id,
            "metrics": [
                "spend",
                "impressions",
                "clicks",
                "conversions"
            ],
            "dimensions": ["campaign_id"]
        }
        try:
            r = requests.get(url, headers=headers, params=params)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            print(f"Lỗi kết nối API TikTok: {e}")
            return {"data": {"list": []}}
