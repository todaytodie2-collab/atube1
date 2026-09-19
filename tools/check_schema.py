import sqlite3

conn = sqlite3.connect('config/atube_data.sqlite')
c = conn.cursor()
for table in ['vod_media', 'vod_servers', 'vod_episodes']:
    print(f"Table {table}:")
    for col in c.execute(f"PRAGMA table_info({table})").fetchall():
        print(" ", col[1], col[2])
conn.close()
