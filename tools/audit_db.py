import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('config/atube_data.sqlite')
cur = conn.cursor()

print("--- ORPHAN EPISODES ---")
orphans = cur.execute("SELECT id, media_id, episode_title FROM vod_episodes WHERE media_id NOT IN (SELECT id FROM vod_media)").fetchall()
print(f"Orphan episodes count: {len(orphans)}")
for o in orphans[:10]:
    print(o)

print("\n--- ALL EPISODES IN VOD_EPISODES ---")
all_eps = cur.execute("SELECT e.id, e.media_id, m.title, e.episode_title FROM vod_episodes e LEFT JOIN vod_media m ON e.media_id = m.id").fetchall()
print(f"Total episodes: {len(all_eps)}")
for e in all_eps[:20]:
    print(e)

print("\n--- CHECK FOR FAKE/MOCK MEDIA IDS IN VOD_MEDIA ---")
mock_media = cur.execute("SELECT id, title, category FROM vod_media WHERE id LIKE 'mov_%' OR id LIKE 'ser_%'").fetchall()
print(f"Mock media count: {len(mock_media)}")
for m in mock_media:
    print(m)

conn.close()
