import asyncio
from tools.tool_registry import tool
from core.logger import get_module_logger

logger = get_module_logger("TikTokScraper")

@tool(name="scrape_tiktok_metrics", description="Cào dữ liệu thô từ profile TikTok để tra soát chi tiêu.")
async def scrape_tiktok_metrics(profile_url: str):
    """
    Giả lập scraper sử dụng browser controller.
    """
    logger.info(f"Đang bắt đầu cào dữ liệu cho: {profile_url}")
    # Trong thực tế, gọi browser_controller.open_url, search, extraction...
    await asyncio.sleep(2) 
    
    data = {
        "views": "1.2M",
        "likes": "45K",
        "shares": "2.1K",
        "estimated_spend": "$1,200"
    }
    
    return f"Đã thu thập dữ liệu từ {profile_url}: {data}"
