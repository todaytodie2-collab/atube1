# -*- coding: utf-8 -*-
"""
A TuBe Database Schema & Table Initialization
"""

from database.connection import get_db_connection

def init_tables():
    """Initializes tables and indexes if they do not already exist."""
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Media Titles Metadata
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vod_media (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            arabic_title TEXT,
            content_type TEXT NOT NULL DEFAULT 'movie',
            type TEXT,
            is_live INTEGER NOT NULL DEFAULT 0,
            category TEXT NOT NULL DEFAULT 'foreign',
            sub_category TEXT DEFAULT 'subbed',
            year TEXT,
            rating TEXT,
            duration TEXT,
            quality TEXT,
            language TEXT,
            translation TEXT,
            production TEXT,
            country TEXT,
            genres TEXT,
            poster TEXT,
            backdrop TEXT,
            synopsis TEXT,
            trailer_youtube_id TEXT,
            director TEXT,
            total_seasons INTEGER DEFAULT 0,
            tmdb_id TEXT,
            updated_at INTEGER
        );
    """)

    # 2. Source Watch / Embed Servers
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vod_servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id TEXT NOT NULL,
            season_number INTEGER,
            episode_number INTEGER,
            site TEXT,
            server_name TEXT,
            stream_url TEXT NOT NULL,
            quality TEXT DEFAULT '1080p FHD',
            badge TEXT,
            FOREIGN KEY (media_id) REFERENCES vod_media(id) ON DELETE CASCADE
        );
    """)

    # 3. Seasons Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vod_seasons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id TEXT NOT NULL,
            season_number INTEGER NOT NULL,
            season_title TEXT,
            UNIQUE(media_id, season_number),
            FOREIGN KEY (media_id) REFERENCES vod_media(id) ON DELETE CASCADE
        );
    """)

    # 4. Series Episodes Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vod_episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id TEXT NOT NULL,
            season_number INTEGER NOT NULL DEFAULT 1,
            episode_number INTEGER NOT NULL,
            episode_title TEXT,
            thumbnail TEXT,
            duration TEXT,
            synopsis TEXT,
            UNIQUE(media_id, season_number, episode_number),
            FOREIGN KEY (media_id) REFERENCES vod_media(id) ON DELETE CASCADE
        );
    """)

    # 5. Cast Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vod_cast (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id TEXT NOT NULL,
            name TEXT NOT NULL,
            arabic_name TEXT,
            role TEXT,
            photo TEXT,
            FOREIGN KEY (media_id) REFERENCES vod_media(id) ON DELETE CASCADE
        );
    """)

    # 6. Stills Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vod_stills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id TEXT NOT NULL,
            photo_url TEXT NOT NULL,
            FOREIGN KEY (media_id) REFERENCES vod_media(id) ON DELETE CASCADE
        );
    """)

    # Indexes for fast querying
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vod_media_type_cat ON vod_media(content_type, category);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vod_media_title ON vod_media(title);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vod_servers_media ON vod_servers(media_id, season_number, episode_number);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vod_episodes_media ON vod_episodes(media_id, season_number, episode_number);")

    conn.commit()
    conn.close()
