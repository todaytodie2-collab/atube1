import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('config/atube_data.sqlite', isolation_level=None)
cur = conn.cursor()

# 1. Clean non-akwam
cur.execute("DELETE FROM vod_media WHERE id NOT LIKE 'akwam_%'")
print("Deleted non-akwam media.")

# 2. Clean vod_episodes
cur.execute("DELETE FROM vod_episodes")
print("Deleted all mock episodes.")

# 3. Clean orphan servers
cur.execute("DELETE FROM vod_servers WHERE media_id NOT IN (SELECT id FROM vod_media)")
print("Deleted orphan servers.")

# 4. Checkpoint WAL & Vacuum
cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
cur.execute("VACUUM")

print("\n--- FINAL STATS ---")
print("vod_media count:", cur.execute("SELECT COUNT(*) FROM vod_media").fetchone()[0])
print("vod_servers count:", cur.execute("SELECT COUNT(*) FROM vod_servers").fetchone()[0])
print("vod_episodes count:", cur.execute("SELECT COUNT(*) FROM vod_episodes").fetchone()[0])

non_akwam = cur.execute("SELECT COUNT(*) FROM vod_media WHERE id NOT LIKE 'akwam_%'").fetchone()[0]
print("Non-akwam items in vod_media:", non_akwam)

conn.close()
