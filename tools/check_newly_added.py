import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('config/atube_data.sqlite')
c = conn.cursor()

print("--- EPISODES ---")
eps = c.execute("SELECT id, media_id, episode_title FROM vod_episodes").fetchall()
print(f"Total episodes: {len(eps)}")
for ep in eps:
    print(ep)

print("\n--- MEDIA IDS NOT LIKE 'akwam_%' ---")
non_akwam = c.execute("SELECT id, title, category FROM vod_media WHERE id NOT LIKE 'akwam_%'").fetchall()
print(f"Total non-akwam: {len(non_akwam)}")
for m in non_akwam:
    print(m)

conn.close()
