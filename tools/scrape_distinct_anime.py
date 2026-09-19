import requests
from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://akwams.org/series?section=0&category=70&rating=0&year=0&language=0&formats=0&quality=0"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

resp = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(resp.text, 'html.parser')
boxes = soup.select('.entry-box')
print(f"Found {len(boxes)} boxes:")
for b in boxes[:15]:
    link = b.select_one('a.box')
    title_el = b.select_one('.entry-title')
    img_el = b.select_one('img')
    href = link.get('href') if link else ''
    title = title_el.get_text(strip=True) if title_el else ''
    src = img_el.get('data-src') or img_el.get('src') if img_el else ''
    print(f"- {title} | {href} | {src[:60]}")
