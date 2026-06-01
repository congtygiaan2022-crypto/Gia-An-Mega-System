"""
tools/report_tool.py — Save LLM output as a text report file.
"""
import datetime
import os


def create_report(topic: str, content: str) -> str:
    """Save content to a timestamped report file in /reports/."""
    os.makedirs("reports", exist_ok=True)
    today = datetime.date.today()
    filename = f"reports/report_{topic}_{today}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Topic: {topic}\nDate: {today}\n\n")
        f.write(content)
    return f"Report saved: {filename}"
