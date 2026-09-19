import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('config/atube_data.sqlite')
cur = conn.cursor()

print("--- SUMMARY OF VOD_MEDIA BY ID PREFIX ---")
prefixes = cur.execute("SELECT SUBSTR(id, 1, 7) as pfx, COUNT(*) FROM vod_media GROUP BY pfx").fetchall()
for p in prefixes:
    print(p)

print("\n--- NON-AKWAM ITEMS IN VOD_MEDIA ---")
non_akwam = cur.execute("SELECT id, title, category, poster FROM vod_media WHERE id NOT LIKE 'akwam_%'").fetchall()
print(f"Total non-akwam: {len(non_akwam)}")
for m in non_akwam:
    print(m)

conn.close()
