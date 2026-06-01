class Plugin:
    def run(self, **kwargs):
        """
        Adapter plugin for Tiktok Ads Automation.
        Maps standard Plugin run() inputs to the AdsAutomation module.
        """
        if kwargs.get("action") == "stop":
            return {"status": "success", "message": "Stopped."}
        from ads_automation.ads_automation import AdsAutomation
        import logging
        
        # Extract accounts passed from kwargs
        accounts = kwargs.get("accounts", {})
        tk_acc = accounts.get("tiktok_ads", "tiktok_A")
        sh_acc = accounts.get("google_sheets", "sheet_A")
        
        automation = AdsAutomation(tk_account=tk_acc, sh_account=sh_acc)
        
        # The actual business logic
        print("Fetching TikTok Ads & Writing Google Sheets Report")
        automation.run()
        
        return {"status": "success", "message": "Report generated successfully."}
