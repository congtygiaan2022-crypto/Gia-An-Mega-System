class ReportGenerator:
    def generate(self, data):
        total_spend = 0
        total_clicks = 0
        total_impressions = 0
        total_conversions = 0

        for d in data:
            total_spend += float(d.get("spend", 0))
            total_clicks += int(d.get("clicks", 0))
            total_impressions += int(d.get("impressions", 0))
            total_conversions += int(d.get("conversions", 0))

        ctr = (total_clicks / total_impressions) * 100 if total_impressions else 0

        report = f"""
ADS REPORT

Spend: {total_spend:,.0f}
Impressions: {total_impressions:,}
Clicks: {total_clicks:,}
Conversions: {total_conversions:,}
CTR: {round(ctr, 2)}%
"""
        return report
