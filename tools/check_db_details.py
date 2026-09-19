import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('config/atube_data.sqlite')
c = conn.cursor()

print("--- VOD_EPISODES ---")
episodes = c.execute("SELECT id, media_id, season_number, episode_number, episode_title FROM vod_episodes").fetchall()
print(f"Total episodes: {len(episodes)}")
for ep in episodes:
    print(ep)

print("\n--- CLIVETH ITEMS IN VOD_MEDIA ---")
cliveth = c.execute("SELECT id, title, type, category, rating FROM vod_media WHERE title LIKE '%كليفيث%'").fetchall()
print(f"Total cliveth: {len(cliveth)}")
for cl in cliveth:
    print(cl)

print("\n--- CHECK ALL MEDIA WITH DUPLICATE TITLES ---")
dup_titles = c.execute("SELECT title, COUNT(*) as cnt FROM vod_media GROUP BY title HAVING cnt > 1").fetchall()
for d in dup_titles:
    print(d)

conn.close()
