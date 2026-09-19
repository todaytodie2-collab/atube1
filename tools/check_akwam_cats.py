import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('config/atube_data.sqlite')
cur = conn.cursor()

cats = cur.execute("SELECT category, COUNT(*) FROM vod_media WHERE id LIKE 'akwam_%' GROUP BY category").fetchall()
print("Akwam items per category:")
for c in cats:
    print(c)

print("\nSample items in anime_series:")
anime = cur.execute("SELECT id, title, category FROM vod_media WHERE category = 'anime_series' AND id LIKE 'akwam_%' LIMIT 15").fetchall()
for a in anime:
    print(a)

conn.close()
