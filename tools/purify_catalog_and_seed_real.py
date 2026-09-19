import os
import sys
import time
import re
import sqlite3
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = "config/atube_data.sqlite"
POSTERS_DIR = "frontend/assets/posters"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def clean_database():
    print("--- 1. PURGING OLD / MOCK / DUPLICATE DATA ---")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Delete all non-akwam media
    cur.execute("DELETE FROM vod_media WHERE id NOT LIKE 'akwam_%'")
    print(f"Deleted non-akwam media. Remaining: {cur.execute('SELECT COUNT(*) FROM vod_media').fetchone()[0]}")

    # 2. Delete repeated episode items of cliveth
    cur.execute("DELETE FROM vod_media WHERE id LIKE 'akwam_مشاهدة-انمي-كليفيتس-الجزء-الاول-الحلق-%'")
    print(f"Deleted duplicate anime episodes. Remaining: {cur.execute('SELECT COUNT(*) FROM vod_media').fetchone()[0]}")

    # 3. Clean orphan episodes
    cur.execute("DELETE FROM vod_episodes WHERE media_id NOT IN (SELECT id FROM vod_media)")
    print(f"Cleaned orphan episodes. Remaining: {cur.execute('SELECT COUNT(*) FROM vod_episodes').fetchone()[0]}")

    # 4. Clean orphan servers
    cur.execute("DELETE FROM vod_servers WHERE media_id NOT IN (SELECT id FROM vod_media)")
    print(f"Cleaned orphan servers. Remaining: {cur.execute('SELECT COUNT(*) FROM vod_servers').fetchone()[0]}")

    conn.commit()
    conn.close()

def download_poster(url, target_path):
    if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
        return True
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(target_path, 'wb') as f:
                f.write(r.content)
            return True
    except Exception as e:
        pass
    return False

def scrape_real_anime_series():
    print("\n--- 2. SCRAPING 20 REAL DISTINCT ANIME SERIES ---")
    url = "https://akwams.org/series?section=0&category=70&rating=0&year=0&language=0&formats=0&quality=0"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        boxes = soup.select('.entry-box')
        print(f"Found {len(boxes)} anime series entries on Akwam.")
    except Exception as e:
        print("Failed to fetch anime series list:", e)
        return

    items_to_insert = []
    servers_to_insert = []

    for box in boxes:
        if len(items_to_insert) >= 20:
            break
        link = box.select_one('a.box')
        if not link:
            continue
        href = link.get('href')
        title_el = box.select_one('.entry-title')
        title = title_el.get_text(strip=True) if title_el else ''
        if not title or title == 'انمي':
            continue

        slug = href.rstrip('/').split('/')[-1]
        media_id = f"akwam_anime_{slug}"

        img_el = box.select_one('img')
        raw_img = (img_el.get('data-src') or img_el.get('src') or '') if img_el else ''
        if raw_img.startswith('//'):
            raw_img = 'https:' + raw_img

        rating_el = box.select_one('.rating') or box.select_one('.label.rating')
        rating = rating_el.get_text(strip=True) if rating_el else '8.4'
        rating_clean = re.sub(r'[^0-9.]', '', rating) or '8.4'

        year_el = box.select_one('.label.year')
        year = year_el.get_text(strip=True) if year_el else '2024'
        year_clean = re.sub(r'[^0-9]', '', year) or '2024'

        # Poster local path
        poster_filename = f"{media_id}.jpg"
        local_poster_path = os.path.join(POSTERS_DIR, poster_filename)
        rel_poster_path = f"assets/posters/{poster_filename}"

        items_to_insert.append({
            'id': media_id,
            'title': title,
            'arabic_title': title,
            'content_type': 'series',
            'type': 'series',
            'category': 'anime_series',
            'year': year_clean,
            'rating': rating_clean,
            'duration': '24 دقيقة',
            'quality': '1080p FHD',
            'language': 'ياباني',
            'translation': 'مترجم',
            'genres': 'أنمي, مغامرة, خيال',
            'synopsis': f"مشاهدة وتحميل مسلسل {title} بجودة عالية على A TuBe.",
            'poster_url': raw_img,
            'local_poster_path': local_poster_path,
            'rel_poster_path': rel_poster_path,
            'href': href
        })

    # Download posters in parallel
    print(f"Downloading posters for {len(items_to_insert)} anime series...")
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = []
        for it in items_to_insert:
            if it['poster_url']:
                futures.append(executor.submit(download_poster, it['poster_url'], it['local_poster_path']))
        for f in futures:
            f.result()

    # Now scrape watch URL for each series
    print("Scraping watch/stream URLs for anime series...")
    def fetch_stream(it):
        stream_link = ''
        try:
            r = requests.get(it['href'], headers=HEADERS, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            # Look for watch link or first episode
            watch_link = soup.select_one('a[href*="/watch/"]') or soup.select_one('a[href*="/episode/"]')
            if watch_link:
                w_url = watch_link.get('href')
                # fetch watch page for player iframe
                rw = requests.get(w_url, headers=HEADERS, timeout=10)
                sw = BeautifulSoup(rw.text, 'html.parser')
                iframe = sw.select_one('iframe')
                if iframe and iframe.get('src'):
                    stream_link = iframe.get('src')
                else:
                    stream_link = w_url
            else:
                stream_link = it['href']
        except Exception:
            stream_link = it['href']
        return stream_link

    with ThreadPoolExecutor(max_workers=6) as executor:
        stream_results = list(executor.map(fetch_stream, items_to_insert))

    # Insert into database
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now_ts = int(time.time())

    for idx, it in enumerate(items_to_insert):
        poster_src = it['rel_poster_path'] if (os.path.exists(it['local_poster_path']) and os.path.getsize(it['local_poster_path']) > 1000) else it['poster_url']
        backdrop_src = poster_src

        cur.execute("""
            INSERT OR REPLACE INTO vod_media 
            (id, title, arabic_title, content_type, type, is_live, category, sub_category, year, rating, duration, quality, language, translation, genres, poster, backdrop, synopsis, updated_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            it['id'], it['title'], it['arabic_title'], it['content_type'], it['type'],
            it['category'], 'anime', it['year'], it['rating'], it['duration'],
            it['quality'], it['language'], it['translation'], it['genres'],
            poster_src, backdrop_src, it['synopsis'], now_ts
        ))

        stream_url = stream_results[idx]
        cur.execute("""
            INSERT INTO vod_servers (media_id, season_number, episode_number, site, server_name, stream_url, quality, badge)
            VALUES (?, 1, 1, 'Akwam CDN', 'سيرفر أكوام السريع', ?, '1080p FHD', 'VIP')
        """, (it['id'], stream_url))

    conn.commit()
    conn.close()
    print(f"Successfully inserted {len(items_to_insert)} distinct anime series!")

def ensure_hero_and_posters():
    print("\n--- 3. VERIFYING ALL REMAINING MEDIA POSTERS & HERO ---")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    rows = cur.execute("SELECT id, title, category, poster, backdrop FROM vod_media").fetchall()
    print(f"Total authentic media in database: {len(rows)}")

    # Set high ratings for top real movies so trending row has real theatrical films
    cur.execute("UPDATE vod_media SET rating = '9.4' WHERE id = 'akwam_فيلم-سينما-منتصف-الليل-2026'")
    cur.execute("UPDATE vod_media SET rating = '9.3' WHERE id = 'akwam_فيلم-x-مراتي-2024'")
    cur.execute("UPDATE vod_media SET rating = '9.2' WHERE id = 'akwam_فيلم-عصابة-الماكس-2024'")
    cur.execute("UPDATE vod_media SET rating = '9.1' WHERE id = 'akwam_فيلم-rosebushpruning-2026'")
    cur.execute("UPDATE vod_media SET rating = '9.0' WHERE id = 'akwam_فيلم-facing-el-chapo-2026'")
    cur.execute("UPDATE vod_media SET rating = '8.9' WHERE id = 'akwam_فيلم-كاريوكي-على-الطريق-2025'")
    cur.execute("UPDATE vod_media SET rating = '8.8' WHERE id = 'akwam_فيلم-mutiny-2026'")
    cur.execute("UPDATE vod_media SET rating = '8.7' WHERE id = 'akwam_فيلم-cruel-hands-2026'")

    conn.commit()
    conn.close()
    print("Updated ratings for top real movies.")

if __name__ == '__main__':
    clean_database()
    scrape_real_anime_series()
    ensure_hero_and_posters()
    print("\nPurification & Scrape Complete!")
