import requests

class FacebookAdsAPI:
    def __init__(self, token, account_id):
        self.token = token
        self.account_id = account_id

    def fetch(self):
        url = f"https://graph.facebook.com/v19.0/act_{self.account_id}/insights"
        params = {
            "fields": "campaign_name,spend,impressions,clicks,actions",
            "access_token": self.token
        }
        try:
            r = requests.get(url, params=params)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            print(f"Lỗi kết nối API Facebook: {e}")
            return {"data": []}
