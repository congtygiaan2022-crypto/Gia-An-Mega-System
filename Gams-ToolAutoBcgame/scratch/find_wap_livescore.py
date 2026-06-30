import requests
from bs4 import BeautifulSoup
import re

url = "https://bongda.wap.vn/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    soup = BeautifulSoup(response.text, 'html.parser')
    print("Links containing 'kq' or 'live' or 'tuyen':")
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.text.strip()
        if any(x in href.lower() or x in text.lower() for x in ['kqbd', 'tructuyen', 'livescore', 'truc-tuyen', 'ty-so', 'tỷ số']):
            print(f"  Text: {text} | Href: {href}")
            
except Exception as e:
    print(f"Error: {e}")
