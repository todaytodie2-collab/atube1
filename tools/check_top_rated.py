import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('config/atube_data.sqlite')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

query = """
    SELECT id, title, arabic_title, type, category, rating, poster, backdrop
    FROM vod_media
    ORDER BY rating DESC, updated_at DESC, id DESC
    LIMIT 10
"""
rows = cur.execute(query).fetchall()
print("Top rated rows:")
for r in rows:
    print(dict(r))

conn.close()
