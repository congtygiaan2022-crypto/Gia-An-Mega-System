import json
import os

class APISettings:
    def __init__(self):
        self.path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "api_accounts.json")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        
        if not os.path.exists(self.path):
            self.data = {
                "facebook_ads": {},
                "tiktok_ads": {},
                "google_sheets": {}
            }
            self._save()
        else:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    def get_all_accounts(self, service: str) -> dict:
        return self.data.get(service, {})

    def get_account(self, service: str, account_name: str) -> dict:
        return self.data.get(service, {}).get(account_name, {})

    def add_or_update_account(self, service: str, account_name: str, account_data: dict):
        if service not in self.data:
            self.data[service] = {}
        self.data[service][account_name] = account_data
        self._save()
        print(f"[APISettings] Saved account '{account_name}' for {service}")

    def delete_account(self, service: str, account_name: str):
        if service in self.data and account_name in self.data[service]:
            del self.data[service][account_name]
            self._save()
            print(f"[APISettings] Deleted account '{account_name}' from {service}")

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
