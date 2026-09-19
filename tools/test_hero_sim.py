import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('config/atube_data.sqlite')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Query used by /api/media/feed with type='all', category='all'
query = """
    SELECT id, title, category, rating, poster, backdrop, synopsis
    FROM vod_media
    ORDER BY updated_at DESC, id DESC
    LIMIT 60
"""
rows = cur.execute(query).fetchall()
allItems = [dict(r) for r in rows]

topMovies = [i for i in allItems if i['category'] in ('arabic_movies', 'foreign_movies') and i['poster']]
print(f"Total allItems: {len(allItems)}")
print(f"Total topMovies: {len(topMovies)}")
if topMovies:
    print("First topMovie:", topMovies[0]['title'], topMovies[0]['category'], topMovies[0]['poster'])

print("\nFirst 5 of allItems:")
for i in allItems[:5]:
    print(i['id'], i['title'], i['category'])

conn.close()
