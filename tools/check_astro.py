import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('config/atube_data.sqlite')
conn.row_factory = sqlite3.Row
r = conn.cursor().execute("SELECT id, title, poster, backdrop, synopsis FROM vod_media WHERE title LIKE '%Astro%'").fetchone()
if r:
    print("Astro Note:", dict(r))
else:
    print("Not found")
conn.close()
