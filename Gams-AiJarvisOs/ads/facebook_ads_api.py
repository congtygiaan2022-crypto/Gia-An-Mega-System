import requests

class FacebookAdsAPI:
    def __init__(self, access_token: str, account_id: str):
        self.token = access_token
        self.account_id = account_id

    def get_campaign_data(self):
        url = f"https://graph.facebook.com/v19.0/act_{self.account_id}/insights"
        params = {
            "fields": "campaign_name,spend,impressions,clicks,actions",
            "access_token": self.token
        }
        try:
            r = requests.get(url, params=params)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e), "data": []}
