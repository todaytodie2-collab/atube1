import urllib.request
from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding='utf-8')

urls = [
    ("arabic_movies", "https://akwams.org/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%b9%d8%b1%d8%a8%d9%8a/"),
    ("foreign_movies", "https://akwams.org/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%ac%d9%86%d8%a8%d9%89-%d9%85%d8%aa%d8%b1%d8%ac%d9%85%d9%87-2026/"),
    ("arabic_series", "https://akwams.org/category/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%b1%d9%85%d8%b6%d8%a7%d9%86-2026/"),
    ("foreign_series", "https://akwams.org/category/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%a7%d8%ac%d9%86%d8%a8%d9%8a/"),
    ("turkish_series", "https://akwams.org/category/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%aa%d8%b1%d9%83%d9%8a%d8%a9/"),
    ("turkish_movies", "https://akwams.org/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%aa%d8%b1%d9%83%d9%8a%d8%a9/"),
    ("hindi_movies", "https://akwams.org/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d9%87%d9%86%d8%af%d9%8a%d8%a9/"),
    ("anime_movies", "https://akwams.org/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d9%86%d9%85%d9%8a/"),
    ("anime_series", "https://akwams.org/category/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%a7%d9%86%d9%85%d9%8a/")
]

for name, u in urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=8).read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        boxes = soup.select('.entry-box')
        sample = ""
        if boxes:
            img = boxes[0].select_one('img')
            sample = img.get('alt', '') if img else ''
        print(f"[{name}] -> {len(boxes)} items | Sample: {sample}", flush=True)
    except Exception as e:
        print(f"[{name}] -> Error: {e}", flush=True)
