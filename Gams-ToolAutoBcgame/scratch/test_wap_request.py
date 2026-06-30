import requests
from bs4 import BeautifulSoup

url = "https://bongda.wap.vn/phong-do-peru-vs-t-b-nha-6245-894190.html"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.text)}")
    soup = BeautifulSoup(response.text, 'html.parser')
    print(f"Title: {soup.title.text if soup.title else 'No Title'}")
    page_text = soup.get_text().lower()
    definitive_live_kw = ['đang diễn ra', 'đang thi đấu', 'hiệp 1:', 'hiệp 2:']
    print(f"Has live keywords: {[kw for kw in definitive_live_kw if kw in page_text]}")
except Exception as e:
    print(f"Error: {e}")
