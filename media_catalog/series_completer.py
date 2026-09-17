# -*- coding: utf-8 -*-
"""
A TuBe Clean Architecture (v1.0.1) - Series Completer Daemon
Monitors ongoing series, anime, and TV shows in the background.
Automatically detects and registers missing/newly released episodes in SQLite,
enriches them with TMDB metadata, and binds failover streaming servers.
"""

import os
import re
import sys
import time
import json
import sqlite3
import threading
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USER_AGENT, get_tmdb_api_key
from database import VODDatabaseManager



class SeriesCompleter:
    _thread: Optional[threading.Thread] = None
    _running: bool = False

    @classmethod
    def fetch_tmdb_tv_meta(cls, tmdb_id: str) -> Optional[Dict[str, Any]]:
        """Queries TMDB API for TV show season structure and episode names."""
        if not tmdb_id:
            return None
        api_key = get_tmdb_api_key()
        url = f"https://api.themoviedb.org/3/tv/{tmdb_id}?api_key={api_key}&language=ar-SA"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    @classmethod
    def fetch_tmdb_season_episodes(cls, tmdb_id: str, season_number: int) -> List[Dict[str, Any]]:
        """Queries TMDB API for episodes in a given season."""
        api_key = get_tmdb_api_key()
        url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season_number}?api_key={api_key}&language=ar-SA"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("episodes", [])
        except Exception:
            return []

    @classmethod
    def check_and_complete_series(cls, media_id: str) -> Dict[str, Any]:
        """Checks and syncs missing episodes for a single series."""
        media = VODDatabaseManager.get_details(media_id)
        if not media or media.get("content_type") not in ("series", "anime", "tv_show"):
            return {"status": "skipped", "message": "Not an episodic series"}

        tmdb_id = media.get("tmdb_id")
        if not tmdb_id or not str(tmdb_id).isdigit():
            return {"status": "skipped", "message": "Missing numeric TMDB ID"}

        tmdb_meta = cls.fetch_tmdb_tv_meta(str(tmdb_id))
        if not tmdb_meta:
            return {"status": "failed", "message": "TMDB TV metadata lookup failed"}

        seasons_meta = tmdb_meta.get("seasons", [])
        total_seasons = len([s for s in seasons_meta if s.get("season_number", 0) > 0])
        new_episodes_added = 0

        conn = VODDatabaseManager.get_connection()
        cur = conn.cursor()

        # Ensure seasons exist in vod_seasons
        for s in seasons_meta:
            s_num = s.get("season_number", 0)
            if s_num <= 0:
                continue
            s_title = s.get("name") or f"الموسم {s_num}"
            cur.execute("""
                INSERT INTO vod_seasons (media_id, season_number, season_title)
                VALUES (?, ?, ?)
                ON CONFLICT(media_id, season_number) DO UPDATE SET season_title = excluded.season_title
            """, (media_id, s_num, s_title))

            # Fetch existing episodes in DB
            cur.execute("""
                SELECT episode_number FROM vod_episodes 
                WHERE media_id = ? AND season_number = ?
            """, (media_id, s_num))
            existing_ep_nums = {r[0] for r in cur.fetchall()}

            # Fetch fresh TMDB episodes
            tmdb_eps = cls.fetch_tmdb_season_episodes(str(tmdb_id), s_num)
            for ep in tmdb_eps:
                ep_num = ep.get("episode_number")
                if not ep_num or ep_num in existing_ep_nums:
                    continue

                ep_title = ep.get("name") or f"الحلقة {ep_num}"
                still_path = ep.get("still_path")
                thumbnail = f"https://image.tmdb.org/t/p/w500{still_path}" if still_path else (media.get("poster") or "")
                synopsis = ep.get("overview") or ""

                cur.execute("""
                    INSERT INTO vod_episodes (media_id, season_number, episode_number, episode_title, thumbnail, duration, synopsis)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(media_id, season_number, episode_number) DO NOTHING
                """, (media_id, s_num, ep_num, ep_title, thumbnail, "45 دقيقة", synopsis))

                # Add default Universal failover mirrors for this newly released episode
                cur.execute("""
                    INSERT INTO vod_servers (media_id, season_number, episode_number, site, server_name, stream_url, quality, badge)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    media_id,
                    s_num,
                    ep_num,
                    "VidLink",
                    "VidLink Global FHD ⭐",
                    f"https://vidlink.pro/tv/{tmdb_id}/{s_num}/{ep_num}",
                    "1080p FHD",
                    "عالمي ⭐"
                ))
                cur.execute("""
                    INSERT INTO vod_servers (media_id, season_number, episode_number, site, server_name, stream_url, quality, badge)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    media_id,
                    s_num,
                    ep_num,
                    "MultiEmbed",
                    "MultiEmbed Universal ⭐",
                    f"https://multiembed.mov/?video_id={tmdb_id}&tmdb=1&s={s_num}&e={ep_num}",
                    "1080p FHD",
                    "عالمي ⭐"
                ))

                new_episodes_added += 1

        # Update total seasons in vod_media
        cur.execute("""
            UPDATE vod_media 
            SET total_seasons = max(total_seasons, ?), updated_at = ?
            WHERE id = ?
        """, (total_seasons, int(time.time()), media_id))

        conn.commit()
        conn.close()

        return {
            "media_id": media_id,
            "title": media.get("title"),
            "total_seasons": total_seasons,
            "new_episodes_added": new_episodes_added,
            "status": "success"
        }

    @classmethod
    def run_check_cycle(cls, limit: int = 25):
        """Scans active series in the database and updates them with newly aired episodes."""
        conn = VODDatabaseManager.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, tmdb_id 
            FROM vod_media 
            WHERE content_type IN ('series', 'anime', 'tv_show') AND tmdb_id IS NOT NULL AND trim(tmdb_id) != ''
            ORDER BY updated_at ASC 
            LIMIT ?
        """, (limit,))
        series_list = cur.fetchall()
        conn.close()

        for s in series_list:
            try:
                cls.check_and_complete_series(s["id"])
            except Exception as ex:
                print(f"[SeriesCompleter] Series check warning on {s['id']}: {ex}")
            time.sleep(0.5)

    @classmethod
    def start_background_worker(cls, interval_hours: int = 4):
        """Starts the background worker thread."""
        if cls._running:
            return

        cls._running = True

        def _worker():
            print(f"[SeriesCompleter] Background worker started. Checking ongoing series every {interval_hours} hours.")
            while cls._running:
                try:
                    cls.run_check_cycle(limit=30)
                except Exception as ex:
                    print(f"[SeriesCompleter] Cycle warning: {ex}")
                time.sleep(interval_hours * 3600)

        cls._thread = threading.Thread(target=_worker, daemon=True)
        cls._thread.start()

    @classmethod
    def stop_worker(cls):
        cls._running = False
