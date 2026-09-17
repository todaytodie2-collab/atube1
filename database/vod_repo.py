# -*- coding: utf-8 -*-
"""
A TuBe Database - VOD Media Repository
Handles CRUD operations and complex queries for movies, series, episodes, and cast.
"""

import json
import time
import re
import hashlib
from typing import Dict, Any, List, Optional
from database.connection import get_db_connection
from database.servers_repo import ServersRepository
from posters_engine.fallback_service import get_episode_thumbnail
from config import DB_PATH

class VODRepository:
    """Repository for managing media content, feeds, and details."""

    @classmethod
    def get_feed(cls, content_type: str = "all", category: str = "all", page: int = 1, limit: int = 40, search: str = "") -> Dict[str, Any]:
        """Retrieves paginated feed of media items."""
        conn = get_db_connection()
        cur = conn.cursor()
        offset = max(0, (page - 1) * limit)

        conditions = []
        params = []

        if content_type and content_type != "all":
            conditions.append("(content_type = ? OR type = ?)")
            params.extend([content_type, content_type])

        if category and category != "all":
            if category in ("recent", "trending_sa", "wwe_ppv", "anime_trending", "atube_originals"):
                conditions.append("(sub_category = ? OR category = ?)")
                params.extend([category, category])
            else:
                conditions.append("(category = ? OR content_type = ?)")
                params.extend([category, category])

        if search:
            s = f"%{search.strip()}%"
            conditions.append("(title LIKE ? OR arabic_title LIKE ? OR id LIKE ? OR genres LIKE ?)")
            params.extend([s, s, s, s])

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # Count total items
        cur.execute(f"SELECT COUNT(*) FROM vod_media {where_clause}", tuple(params))
        total_items = cur.fetchone()[0]

        # Fetch page items
        query = f"""
            SELECT * FROM vod_media 
            {where_clause} 
            ORDER BY updated_at DESC, id DESC 
            LIMIT ? OFFSET ?
        """
        cur.execute(query, tuple(params + [limit, offset]))
        rows = cur.fetchall()

        items = []
        for r in rows:
            d = dict(r)
            items.append({
                "id": d.get("id"),
                "title": d.get("title") or "",
                "arabic_title": d.get("arabic_title") or d.get("title") or "",
                "year": d.get("year") or "",
                "rating": d.get("rating") or "8.0",
                "duration": d.get("duration") or "120 دقيقة",
                "quality": d.get("quality") or "1080p FHD",
                "poster": d.get("poster") or "",
                "backdrop": d.get("backdrop") or d.get("poster") or "",
                "category": d.get("category") or "foreign",
                "sub_category": d.get("sub_category") or "subbed",
                "content_type": d.get("content_type") or "movie",
                "synopsis": d.get("synopsis") or "",
                "genres": d.get("genres") or "",
                "trailer_youtube_id": d.get("trailer_youtube_id") or "",
                "tmdb_id": d.get("tmdb_id") or "",
                "total_seasons": d.get("total_seasons") or 0
            })

        conn.close()
        total_pages = (total_items + limit - 1) // limit if total_items > 0 else 1

        return {
            "page": page,
            "limit": limit,
            "total_items": total_items,
            "total_pages": total_pages,
            "items": items
        }

    @classmethod
    def get_details(cls, media_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves full details for a movie or series including episodes, servers, cast, and stills."""
        if not media_id:
            return None
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM vod_media WHERE id = ?", (media_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return None

        d = dict(row)

        # Parse genres
        genres = []
        raw_genres = d.get("genres") or ""
        if raw_genres:
            try:
                genres = json.loads(raw_genres) if raw_genres.startswith("[") else [g.strip() for g in raw_genres.split(",")]
            except Exception:
                genres = [raw_genres]

        # 1. Fetch Movie Servers
        cur.execute("""
            SELECT id, server_name, stream_url, site, quality, badge, season_number, episode_number 
            FROM vod_servers 
            WHERE media_id = ? 
            ORDER BY id ASC
        """, (media_id,))
        s_rows = cur.fetchall()

        all_servers = []
        movie_servers = []
        for s in s_rows:
            sd = dict(s)
            s_dict = {
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
            }
            all_servers.append(s_dict)
            if sd.get("season_number") is None:
                movie_servers.append(s_dict)

        if not movie_servers:
            movie_servers = all_servers

        # 2. Fetch Seasons and Episodes
        seasons = []
        is_series = d.get("content_type") in ("series", "anime", "tv_show") or (d.get("total_seasons") and int(d.get("total_seasons") or 0) > 0)
        if is_series:
            cur.execute("SELECT season_number, season_title FROM vod_seasons WHERE media_id = ? ORDER BY season_number ASC", (media_id,))
            season_rows = cur.fetchall()
            
            cur.execute("""
                SELECT season_number, episode_number, episode_title, thumbnail, duration, synopsis 
                FROM vod_episodes 
                WHERE media_id = ? 
                ORDER BY season_number ASC, episode_number ASC
            """, (media_id,))
            ep_rows = cur.fetchall()

            seasons_dict: Dict[int, List[Dict[str, Any]]] = {}
            for ep in ep_rows:
                ed = dict(ep)
                s_num = ed.get("season_number") or 1
                if s_num not in seasons_dict:
                    seasons_dict[s_num] = []
                
                ep_num = ed.get("episode_number")
                ep_servers = [srv for srv in all_servers if srv.get("season") == s_num and srv.get("episode") == ep_num]
                
                parent_media = {
                    "poster": d.get("poster") or "",
                    "backdrop": d.get("backdrop") or d.get("poster") or "",
                    "poster_url": d.get("poster") or ""
                }
                seasons_dict[s_num].append({
                    "episode_number": ep_num,
                    "title": ed.get("episode_title") or f"الحلقة {ep_num}",
                    "thumbnail": get_episode_thumbnail(ed.get("thumbnail"), parent_media),
                    "duration": ed.get("duration") or "45 دقيقة",
                    "synopsis": ed.get("synopsis") or "",
                    "servers": ep_servers
                })

            season_titles = {sr["season_number"]: sr["season_title"] for sr in season_rows} if season_rows else {}

            for s_num in sorted(seasons_dict.keys()):
                seasons.append({
                    "season_number": s_num,
                    "title": season_titles.get(s_num) or f"الموسم {s_num}",
                    "episodes": seasons_dict[s_num]
                })

        # 3. Fetch Cast
        cur.execute("SELECT name, arabic_name, role, photo FROM vod_cast WHERE media_id = ?", (media_id,))
        cast = [dict(c) for c in cur.fetchall()]

        # 4. Fetch Stills
        cur.execute("SELECT photo_url FROM vod_stills WHERE media_id = ?", (media_id,))
        stills = [s["photo_url"] for s in cur.fetchall()]

        # 5. Fetch Similar Recommendations
        media_cat = d.get("category") or "foreign"
        cur.execute("""
            SELECT id, title, arabic_title, poster, backdrop, year, rating, quality, category, content_type
            FROM vod_media
            WHERE category = ? AND id != ?
            ORDER BY rating DESC, year DESC
            LIMIT 12
        """, (media_cat, media_id))
        rec_rows = cur.fetchall()
        recommendations = []
        for r in rec_rows:
            rd = dict(r)
            recommendations.append({
                "id": rd.get("id"),
                "title": rd.get("title"),
                "arabic_title": rd.get("arabic_title") or rd.get("title"),
                "poster": rd.get("poster") or rd.get("backdrop"),
                "backdrop": rd.get("backdrop") or rd.get("poster"),
                "year": rd.get("year") or "2024",
                "rating": rd.get("rating") or "8.0",
                "quality": rd.get("quality") or "WEB-DL",
                "category": rd.get("category") or "foreign",
                "content_type": rd.get("content_type") or "movie"
            })

        conn.close()

        return {
            "id": d.get("id"),
            "title": d.get("title") or "",
            "arabic_title": d.get("arabic_title") or d.get("title") or "",
            "original_title": d.get("title") or "",
            "year": d.get("year") or "",
            "rating": d.get("rating") or "8.0",
            "poster": d.get("poster") or "",
            "backdrop": d.get("backdrop") or d.get("poster") or "",
            "category": d.get("category") or "foreign",
            "content_type": d.get("content_type") or "movie",
            "synopsis": d.get("synopsis") or "",
            "duration": d.get("duration") or "120 دقيقة",
            "quality": d.get("quality") or "WEB-DL",
            "language": d.get("language") or "مترجم",
            "country": "أمريكا" if d.get("category") == "foreign" else "مصر",
            "translation": d.get("translation") or "العربية",
            "genres": genres,
            "tmdb_id": d.get("tmdb_id") or "",
            "trailer_youtube_id": d.get("trailer_youtube_id") or "",
            "director": d.get("director") or "Lauren Bond",
            "writer": "Jim Carlson",
            "total_seasons": d.get("total_seasons") or len(seasons),
            "servers": movie_servers,
            "seasons": seasons,
            "cast": cast,
            "stills": stills,
            "recommendations": recommendations
        }

    @classmethod
    def get_cast(cls, media_id: str) -> List[Dict[str, Any]]:
        """Retrieves cast and crew for a given media title."""
        if not media_id:
            return []
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name, arabic_name, role, photo FROM vod_cast WHERE media_id = ?", (media_id,))
        cast = [dict(c) for c in cur.fetchall()]
        conn.close()
        return cast

    @classmethod
    def get_episodes(cls, media_id: str, season_number: int = 1) -> List[Dict[str, Any]]:
        """Retrieves episodes and streaming servers for a specific season."""
        if not media_id:
            return []
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT episode_number, episode_title, thumbnail, duration, synopsis 
            FROM vod_episodes 
            WHERE media_id = ? AND season_number = ? 
            ORDER BY episode_number ASC
        """, (media_id, season_number))
        ep_rows = cur.fetchall()

        cur.execute("""
            SELECT id, server_name, stream_url, site, quality, badge, episode_number 
            FROM vod_servers 
            WHERE media_id = ? AND season_number = ? 
            ORDER BY id ASC
        """, (media_id, season_number))
        srv_rows = cur.fetchall()

        cur.execute("SELECT poster, backdrop FROM vod_media WHERE id = ?", (media_id,))
        p_row = cur.fetchone()
        parent_media = {
            "poster": p_row["poster"] if p_row and p_row["poster"] else "",
            "backdrop": p_row["backdrop"] if p_row and p_row["backdrop"] else "",
            "poster_url": p_row["poster"] if p_row and p_row["poster"] else ""
        } if p_row else {}

        cur.execute("""
            SELECT id, server_name, stream_url, site, quality, badge 
            FROM vod_servers 
            WHERE media_id = ? 
            ORDER BY id ASC
        """, (media_id,))
        gen_srv_rows = cur.fetchall()
        fallback_servers = [{
            "id": gs["id"],
            "name": gs["server_name"] or "سيرفر سحابي",
            "server_name": gs["server_name"] or "سيرفر سحابي",
            "stream_url": gs["stream_url"],
            "url": gs["stream_url"],
            "site": gs["site"] or "Cloud",
            "quality": gs["quality"] or "1080p FHD",
            "badge": gs["badge"] or "VIP ⚡"
        } for gs in gen_srv_rows]

        conn.close()

        servers_by_ep: Dict[int, List[Dict[str, Any]]] = {}
        for s in srv_rows:
            sd = dict(s)
            ep_n = sd.get("episode_number") or 1
            if ep_n not in servers_by_ep:
                servers_by_ep[ep_n] = []
            servers_by_ep[ep_n].append({
                "id": sd.get("id"),
                "name": sd.get("server_name") or "سيرفر سحابي",
                "server_name": sd.get("server_name") or "سيرفر سحابي",
                "stream_url": sd.get("stream_url"),
                "url": sd.get("stream_url"),
                "site": sd.get("site") or "Cloud",
                "quality": sd.get("quality") or "1080p FHD",
                "badge": sd.get("badge") or "VIP ⚡"
            })

        episodes = []
        for ep in ep_rows:
            ed = dict(ep)
            ep_num = ed.get("episode_number")
            ep_srvs = servers_by_ep.get(ep_num) or []
            episodes.append({
                "episode_number": ep_num,
                "title": ed.get("episode_title") or f"الحلقة {ep_num}",
                "thumbnail": get_episode_thumbnail(ed.get("thumbnail"), parent_media),
                "duration": ed.get("duration") or "45 دقيقة",
                "synopsis": ed.get("synopsis") or "",
                "servers": ep_srvs
            })
        return episodes

    @classmethod
    def save_media(cls, media_data: Dict[str, Any]):
        """Persists or updates media metadata."""
        if not media_data or not media_data.get("id"):
            return
        conn = get_db_connection()
        cur = conn.cursor()

        genres_val = media_data.get("genres", [])
        if isinstance(genres_val, list):
            genres_val = json.dumps(genres_val, ensure_ascii=False)

        cur.execute("""
            INSERT INTO vod_media (
                id, title, arabic_title, year, rating, poster, backdrop, 
                category, content_type, synopsis, duration, quality, genres, tmdb_id, 
                trailer_youtube_id, total_seasons, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                arabic_title = coalesce(excluded.arabic_title, vod_media.arabic_title),
                year = coalesce(excluded.year, vod_media.year),
                rating = coalesce(excluded.rating, vod_media.rating),
                poster = coalesce(excluded.poster, vod_media.poster),
                backdrop = coalesce(excluded.backdrop, vod_media.backdrop),
                category = coalesce(excluded.category, vod_media.category),
                content_type = coalesce(excluded.content_type, vod_media.content_type),
                synopsis = coalesce(excluded.synopsis, vod_media.synopsis),
                duration = coalesce(excluded.duration, vod_media.duration),
                quality = coalesce(excluded.quality, vod_media.quality),
                genres = coalesce(excluded.genres, vod_media.genres),
                tmdb_id = coalesce(excluded.tmdb_id, vod_media.tmdb_id),
                total_seasons = max(excluded.total_seasons, vod_media.total_seasons),
                updated_at = excluded.updated_at
        """, (
            media_data["id"],
            media_data.get("title", ""),
            media_data.get("arabic_title") or media_data.get("title", ""),
            str(media_data.get("year", "")),
            str(media_data.get("rating", "8.0")),
            media_data.get("poster", ""),
            media_data.get("backdrop") or media_data.get("poster", ""),
            media_data.get("category", "foreign"),
            media_data.get("content_type", "movie"),
            media_data.get("synopsis", ""),
            media_data.get("duration", "120 دقيقة"),
            media_data.get("quality", "1080p FHD"),
            genres_val,
            str(media_data.get("tmdb_id") or ""),
            str(media_data.get("trailer_youtube_id") or ""),
            int(media_data.get("total_seasons") or 0),
            int(time.time())
        ))

        # Save servers
        ServersRepository.save_servers_batch(cur, media_data["id"], media_data.get("servers", []))

        # Save cast
        cast_items = media_data.get("cast", [])
        if cast_items:
            cur.execute("DELETE FROM vod_cast WHERE media_id = ?", (media_data["id"],))
            for c in cast_items:
                c_name = c.get("name") or c.get("arabic_name") or ""
                if c_name:
                    cur.execute("""
                        INSERT INTO vod_cast (media_id, name, arabic_name, role, photo)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        media_data["id"],
                        c_name,
                        c.get("arabic_name") or c_name,
                        c.get("role") or "شخصية رئيسية",
                        c.get("photo") or "assets/default_avatar.png"
                    ))

        conn.commit()
        conn.close()

    @classmethod
    def insert_media(cls, content_type: str = "movie", title: str = "", category: str = "arabic", link: str = "", servers: Optional[List[Any]] = None, **kwargs) -> str:
        """Convenience insertion method for crawler scripts with auto TMDB enrichment."""
        slug = re.sub(r'[^a-zA-Z0-9\u0600-\u06FF]+', '-', title).strip('-').lower()
        if not slug:
            slug = hashlib.md5(title.encode('utf-8')).hexdigest()[:10]
        media_id = f"{content_type}_{slug}"
        
        parsed_servers = []
        if servers:
            for s in servers:
                if isinstance(s, str) and s.strip():
                    parsed_servers.append({
                        "url": s.strip(),
                        "name": "سيرفر مشاهدة سحابي",
                        "quality": "1080p FHD",
                        "site": "Cloud"
                    })
                elif isinstance(s, dict):
                    parsed_servers.append(s)

        # Fallback TMDB Enrichment if poster or synopsis or cast is missing
        poster = kwargs.get("poster") or ""
        backdrop = kwargs.get("backdrop") or ""
        synopsis = kwargs.get("synopsis") or ""
        cast = kwargs.get("cast") or []
        tmdb_id = kwargs.get("tmdb_id") or ""
        year = kwargs.get("year") or ""
        rating = kwargs.get("rating") or "8.0"

        if not poster or not synopsis or not cast:
            try:
                from posters_engine.tmdb_service import TMDBService
                tmdb_meta = TMDBService.get_full_metadata(title, content_type=content_type, year=year)
                if tmdb_meta:
                    poster = poster or tmdb_meta.get("poster") or ""
                    backdrop = backdrop or tmdb_meta.get("backdrop") or poster
                    synopsis = synopsis or tmdb_meta.get("synopsis") or f"مشاهدة وتحميل {title} بجودة عالية."
                    cast = cast or tmdb_meta.get("cast") or []
                    tmdb_id = tmdb_id or tmdb_meta.get("tmdb_id") or ""
                    year = year or tmdb_meta.get("year") or "2024"
                    rating = rating if rating != "8.0" else tmdb_meta.get("rating", "8.0")
            except Exception:
                pass
                    
        media_data = {
            "id": media_id,
            "title": title,
            "arabic_title": kwargs.get("arabic_title") or title,
            "category": "arabic" if "arabic" in category else category,
            "content_type": content_type,
            "poster": poster,
            "backdrop": backdrop or poster,
            "synopsis": synopsis or f"مشاهدة وتحميل {title} بجودة عالية عبر منصة A TuBe.",
            "cast": cast,
            "tmdb_id": tmdb_id,
            "year": year or "2024",
            "rating": rating,
            "servers": parsed_servers,
            **kwargs
        }
        cls.save_media(media_data)
        return media_id

    @classmethod
    def insert_series_episode(cls, series_title: str, season_number: int = 1, episode_number: int = 1,
                              category: str = "foreign_series", link: str = "", servers: Optional[List[Any]] = None,
                              episode_title: Optional[str] = None, thumbnail: Optional[str] = None, **kwargs) -> str:
        """Properly links an episode and its servers to its parent series container."""
        # 1. Ensure parent series exists
        series_id = cls.insert_media(
            content_type="series",
            title=series_title,
            category=category,
            link=link,
            servers=[],
            **kwargs
        )

        conn = get_db_connection()
        cur = conn.cursor()

        # 2. Register season
        cur.execute("""
            INSERT OR IGNORE INTO vod_seasons (media_id, season_number, season_title)
            VALUES (?, ?, ?)
        """, (series_id, season_number, f"الموسم {season_number}"))

        # 3. Register episode
        ep_title = episode_title or f"الحلقة {episode_number}"
        cur.execute("""
            INSERT INTO vod_episodes (media_id, season_number, episode_number, episode_title, thumbnail, duration, synopsis)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(media_id, season_number, episode_number) DO UPDATE SET
                episode_title = coalesce(excluded.episode_title, vod_episodes.episode_title),
                thumbnail = coalesce(excluded.thumbnail, vod_episodes.thumbnail),
                synopsis = coalesce(excluded.synopsis, vod_episodes.synopsis)
        """, (
            series_id,
            season_number,
            episode_number,
            ep_title,
            thumbnail or "",
            kwargs.get("duration", "45 دقيقة"),
            kwargs.get("synopsis", "")
        ))

        # 4. Save episode servers (Clear stale servers first to adopt only freshly scraped ones)
        if servers:
            cur.execute("""
                DELETE FROM vod_servers 
                WHERE media_id = ? AND season_number = ? AND episode_number = ?
            """, (series_id, season_number, episode_number))

            for s in servers:
                s_url = s.get("url") or s.get("stream_url") if isinstance(s, dict) else str(s).strip()
                if not s_url:
                    continue
                s_name = s.get("name") or s.get("server_name") or "سيرفر مشاهدة سحابي" if isinstance(s, dict) else "سيرفر مشاهدة سحابي"
                s_site = s.get("site") or "Cloud" if isinstance(s, dict) else "Cloud"
                cur.execute("""
                    INSERT INTO vod_servers (media_id, season_number, episode_number, site, server_name, stream_url, quality, badge)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    series_id,
                    season_number,
                    episode_number,
                    s_site,
                    s_name,
                    s_url,
                    "1080p FHD",
                    "VIP ⚡"
                ))

        conn.commit()
        conn.close()
        return series_id

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Returns database metadata counts."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM vod_media")
        total_media = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM vod_servers")
        total_servers = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM vod_episodes")
        total_episodes = cur.fetchone()[0]
        conn.close()
        return {
            "total_media": total_media,
            "total_servers": total_servers,
            "total_episodes": total_episodes,
            "db_path": DB_PATH
        }

