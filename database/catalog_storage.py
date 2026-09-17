# -*- coding: utf-8 -*-
"""
A TuBe Clean Architecture - Folder & Per-Item Database Storage Engine
================================================================================
Organizes catalog into structured folders per category and per title:
    data/catalog/{category_slug}/{item_slug}/
        ├── metadata.json   (Core metadata, title, synopsis, rating, year, duration, genres)
        ├── servers.json    (Streaming servers list with quality, badges, proxy URLs)
        ├── cast.json       (Cast & crew members, roles, photos)
        └── stills.json     (Gallery snapshots & backdrops)

Also synchronizes bidirectional data with SQLite WAL database.
"""

import os
import sys
import json
import time
import re
import sqlite3
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROJECT_ROOT, DB_PATH
from database.connection import get_db_connection

CATALOG_ROOT = os.path.join(PROJECT_ROOT, "data", "catalog")

CATEGORY_FOLDERS_MAP = {
    "foreign_movies": "movies_foreign",
    "arabic_movies": "movies_arabic",
    "anime_movies": "movies_anime",
    "indian_movies": "movies_indian",
    "hindi_movies": "movies_indian",
    "turkish_movies": "movies_turkish",
    "asian_movies": "movies_asian",
    "foreign_series": "series_foreign",
    "arabic_series": "series_arabic",
    "turkish_series": "series_turkish",
    "korean_series": "series_korean",
    "asian_series": "series_korean",
    "anime_series": "series_anime",
    "wwe": "wwe",
    "live_tv": "live_tv"
}

class CatalogStorageManager:
    """Manages disk-based per-item folder databases and synchronization with SQLite."""

    @classmethod
    def get_category_folder(cls, category: str, content_type: str = "movie") -> str:
        cat_key = category.lower().strip()
        if cat_key in CATEGORY_FOLDERS_MAP:
            return CATEGORY_FOLDERS_MAP[cat_key]
        if content_type == "series":
            return f"series_{cat_key}"
        return f"movies_{cat_key}"

    @classmethod
    def save_item_to_folder(cls, media_data: Dict[str, Any]) -> str:
        """Saves a media item and its servers/cast/stills into an isolated directory structure."""
        m_id = media_data.get("id", "")
        if not m_id:
            return ""

        cat = media_data.get("category", "foreign_movies")
        c_type = media_data.get("content_type", "movie")
        cat_folder = cls.get_category_folder(cat, c_type)

        slug = re.sub(r'[^a-zA-Z0-9\u0600-\u06FF]+', '-', m_id).strip('-').lower()
        item_dir = os.path.join(CATALOG_ROOT, cat_folder, slug)
        os.makedirs(item_dir, exist_ok=True)

        # 1. metadata.json
        metadata = {
            "id": m_id,
            "title": media_data.get("title", ""),
            "arabic_title": media_data.get("arabic_title") or media_data.get("title", ""),
            "original_title": media_data.get("original_title") or media_data.get("title", ""),
            "year": str(media_data.get("year", "2024")),
            "rating": str(media_data.get("rating", "8.5")),
            "duration": media_data.get("duration", "120 دقيقة"),
            "quality": media_data.get("quality", "1080p FHD"),
            "category": cat,
            "content_type": c_type,
            "sub_category": media_data.get("sub_category", "subbed"),
            "poster": media_data.get("poster", ""),
            "backdrop": media_data.get("backdrop") or media_data.get("poster", ""),
            "country": media_data.get("country", ""),
            "language": media_data.get("language", "مترجم"),
            "director": media_data.get("director", ""),
            "writer": media_data.get("writer", ""),
            "genres": media_data.get("genres", []),
            "synopsis": media_data.get("synopsis", ""),
            "total_seasons": media_data.get("total_seasons", 1 if c_type in ("series", "anime") else 0),
            "updated_at": int(time.time())
        }
        with open(os.path.join(item_dir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 2. servers.json
        servers = media_data.get("servers", [])
        with open(os.path.join(item_dir, "servers.json"), "w", encoding="utf-8") as f:
            json.dump(servers, f, ensure_ascii=False, indent=2)

        # 3. cast.json
        cast = media_data.get("cast", [])
        with open(os.path.join(item_dir, "cast.json"), "w", encoding="utf-8") as f:
            json.dump(cast, f, ensure_ascii=False, indent=2)

        # 4. stills.json
        stills = media_data.get("stills", [])
        with open(os.path.join(item_dir, "stills.json"), "w", encoding="utf-8") as f:
            json.dump(stills, f, ensure_ascii=False, indent=2)

        return item_dir

    @classmethod
    def sync_all_from_folders_to_db(cls):
        """Loads all folder items and writes them to SQLite database."""
        if not os.path.exists(CATALOG_ROOT):
            return 0

        conn = get_db_connection()
        cur = conn.cursor()
        count = 0

        for cat_dir in os.listdir(CATALOG_ROOT):
            cat_path = os.path.join(CATALOG_ROOT, cat_dir)
            if not os.path.isdir(cat_path):
                continue

            for item_slug in os.listdir(cat_path):
                item_path = os.path.join(cat_path, item_slug)
                meta_file = os.path.join(item_path, "metadata.json")
                if not os.path.isfile(meta_file):
                    continue

                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)

                    servers_file = os.path.join(item_path, "servers.json")
                    servers = []
                    if os.path.exists(servers_file):
                        with open(servers_file, "r", encoding="utf-8") as f:
                            servers = json.load(f)

                    cast_file = os.path.join(item_path, "cast.json")
                    cast = []
                    if os.path.exists(cast_file):
                        with open(cast_file, "r", encoding="utf-8") as f:
                            cast = json.load(f)

                    # Insert or Update in SQLite vod_media
                    genres_val = meta.get("genres", [])
                    if isinstance(genres_val, list):
                        genres_val = json.dumps(genres_val, ensure_ascii=False)

                    cur.execute("""
                        INSERT INTO vod_media (
                            id, title, arabic_title, year, rating, duration, quality,
                            poster, backdrop, category, content_type, sub_category,
                            country, language, director, genres, synopsis, total_seasons, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            title=excluded.title,
                            arabic_title=excluded.arabic_title,
                            year=excluded.year,
                            rating=excluded.rating,
                            duration=excluded.duration,
                            quality=excluded.quality,
                            poster=excluded.poster,
                            backdrop=excluded.backdrop,
                            category=excluded.category,
                            content_type=excluded.content_type,
                            sub_category=excluded.sub_category,
                            country=excluded.country,
                            language=excluded.language,
                            director=excluded.director,
                            genres=excluded.genres,
                            synopsis=excluded.synopsis,
                            total_seasons=excluded.total_seasons,
                            updated_at=excluded.updated_at
                    """, (
                        meta["id"], meta["title"], meta.get("arabic_title", meta["title"]),
                        meta.get("year", "2024"), meta.get("rating", "8.5"), meta.get("duration", "120 دقيقة"),
                        meta.get("quality", "1080p FHD"), meta.get("poster", ""), meta.get("backdrop", ""),
                        meta.get("category", "foreign_movies"), meta.get("content_type", "movie"),
                        meta.get("sub_category", "subbed"), meta.get("country", ""), meta.get("language", "مترجم"),
                        meta.get("director", ""), genres_val, meta.get("synopsis", ""),
                        int(meta.get("total_seasons", 0)), int(time.time())
                    ))

                    # Insert servers
                    cur.execute("DELETE FROM vod_servers WHERE media_id = ?", (meta["id"],))
                    for s in servers:
                        s_name = s.get("name") or s.get("server_name") or "سيرفر المشاهدة"
                        s_url = s.get("url") or s.get("stream_url") or ""
                        s_qual = s.get("quality") or "1080p FHD"
                        s_badge = s.get("badge") or "1080P"
                        if s_url:
                            cur.execute("""
                                INSERT INTO vod_servers (media_id, server_name, stream_url, quality, badge, site)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (meta["id"], s_name, s_url, s_qual, s_badge, "VerifiedDirect"))

                    # Insert cast
                    if cast:
                        cur.execute("DELETE FROM vod_cast WHERE media_id = ?", (meta["id"],))
                        for c in cast:
                            c_name = c.get("name") or c.get("arabic_name") or ""
                            if c_name:
                                cur.execute("""
                                    INSERT INTO vod_cast (media_id, name, arabic_name, role, photo)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (meta["id"], c_name, c.get("arabic_name") or c_name, c.get("role") or "شخصية رئيسية", c.get("photo") or "assets/default_avatar.png"))

                    count += 1
                except Exception as e:
                    print(f"[CatalogStorage] Error syncing {meta_file}: {e}")

        conn.commit()
        conn.close()
        return count
