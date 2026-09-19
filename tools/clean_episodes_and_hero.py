import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('config/atube_data.sqlite')
cur = conn.cursor()

# 1. Check all items starting with series_ or containing mock in vod_media
bad_media = cur.execute("SELECT id, title FROM vod_media WHERE id NOT LIKE 'akwam_%'").fetchall()
print(f"Non-akwam media to purge: {len(bad_media)}")
for m in bad_media:
    print("Deleting:", m)
cur.execute("DELETE FROM vod_media WHERE id NOT LIKE 'akwam_%'")

# 2. Delete all mock episodes in vod_episodes
print("Deleting all mock episodes in vod_episodes...")
cur.execute("DELETE FROM vod_episodes")
print("Remaining vod_episodes count:", cur.execute("SELECT COUNT(*) FROM vod_episodes").fetchone()[0])

# 3. Ensure hero is a real top blockbuster movie:
# Let's check top Arabic and foreign movies
print("\nTop movies candidate for Hero:")
movies = cur.execute("""
    SELECT id, title, rating, poster, backdrop 
    FROM vod_media 
    WHERE category IN ('arabic_movies', 'foreign_movies') 
    ORDER BY rating DESC 
    LIMIT 5
""").fetchall()
for m in movies:
    print(m)

# Set "فيلم سينما منتصف الليل 2026" or "فيلم عصابة الماكس 2024" with backdrop
cur.execute("""
    UPDATE vod_media 
    SET backdrop = poster 
    WHERE backdrop IS NULL OR backdrop = ''
""")

conn.commit()
conn.close()
print("\nCleaning complete!")
