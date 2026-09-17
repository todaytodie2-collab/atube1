# -*- coding: utf-8 -*-
"""
A TuBe Database - Streaming Servers Repository
Handles registering, updating, and querying streaming server links from SQLite.
"""

from typing import List, Dict, Any, Optional
from database.connection import get_db_connection

class ServersRepository:
    """Repository for managing stream servers in `vod_servers` table."""

    @classmethod
    def get_servers_for_media(cls, media_id: str) -> List[Dict[str, Any]]:
        """Fetches all server links registered for a specific media item."""
        if not media_id:
            return []
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, server_name, stream_url, site, quality, badge, season_number, episode_number 
            FROM vod_servers 
            WHERE media_id = ? 
            ORDER BY id ASC
        """, (media_id,))
        rows = cur.fetchall()
        conn.close()

        servers = []
        for s in rows:
            sd = dict(s)
            servers.append({
                "id": sd.get("id"),
                "name": sd.get("server_name") or "سيرفر مشاهدة سحابي",
                "server_name": sd.get("server_name") or "سيرفر مشاهدة سحابي",
                "raw_name": sd.get("site") or sd.get("server_name"),
                "url": sd.get("stream_url"),
                "stream_url": sd.get("stream_url"),
                "raw_url": sd.get("stream_url"),
                "site": sd.get("site") or "Cloud",
                "quality": sd.get("quality") or "1080p FHD",
                "badge": sd.get("badge") or "VIP ⚡",
                "season": sd.get("season_number"),
                "episode": sd.get("episode_number")
            })
        return servers

    @classmethod
    def add_server(cls, media_id: str, stream_url: str, server_name: str = "سيرفر مشاهدة مباشر", 
                   quality: str = "1080p FHD", badge: str = "VIP ⚡", site: str = "Direct",
                   season_number: Optional[int] = None, episode_number: Optional[int] = None) -> bool:
        """Explicitly registers or updates a streaming URL in SQLite for any media or episode."""
        if not media_id or not stream_url:
            return False
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM vod_servers 
            WHERE media_id = ? AND stream_url = ? 
            AND (season_number = ? OR (season_number IS NULL AND ? IS NULL))
            AND (episode_number = ? OR (episode_number IS NULL AND ? IS NULL))
        """, (media_id, stream_url, season_number, season_number, episode_number, episode_number))
        existing = cur.fetchone()
        if existing:
            cur.execute("""
                UPDATE vod_servers 
                SET server_name = ?, quality = ?, badge = ?, site = ? 
                WHERE id = ?
            """, (server_name, quality, badge, site, existing["id"]))
        else:
            cur.execute("""
                INSERT INTO vod_servers (media_id, season_number, episode_number, site, server_name, stream_url, quality, badge)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (media_id, season_number, episode_number, site, server_name, stream_url, quality, badge))
        conn.commit()
        conn.close()
        return True

    @classmethod
    def save_servers_batch(cls, cur, media_id: str, servers: List[Dict[str, Any]]):
        """Batch inserts servers using an existing transaction cursor."""
        for s in servers:
            s_url = s.get("url") or s.get("stream_url") or ""
            if not s_url:
                continue
            cur.execute("""
                INSERT INTO vod_servers (media_id, season_number, episode_number, site, server_name, stream_url, quality, badge)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                media_id,
                s.get("season"),
                s.get("episode"),
                s.get("site") or s.get("raw_name") or "Direct",
                s.get("name") or s.get("server_name") or "سيرفر مشاهدة سحابي",
                s_url,
                s.get("quality", "1080p FHD"),
                s.get("badge", "VIP ⚡")
            ))
