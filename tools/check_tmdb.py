import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('config/atube_data.sqlite')
rows = conn.cursor().execute("SELECT id, title, category, tmdb_id FROM vod_media WHERE tmdb_id IS NOT NULL AND tmdb_id != ''").fetchall()
print(f"Total with tmdb_id: {len(rows)}")
for r in rows:
    print(r)
conn.close()
