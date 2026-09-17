# -*- coding: utf-8 -*-
"""
A TuBe Clean Architecture (v2.0) - Movies Harvester
Extracts, parses, and enriches movies (Foreign, Arabic, Asian) with TMDB metadata,
quality tags (1080p, 4K HDR, BluRay), runtime, and direct servers.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USER_AGENT, get_tmdb_api_key
from database import VODDatabaseManager

class MoviesHarvester:
    """Smart movie harvester extracting rich metadata, posters, and servers."""

    @classmethod
    def fetch_tmdb_movie(cls, tmdb_id_or_title: str, year: Optional[str] = None) -> Optional[Dict[str, Any]]:
        api_key = get_tmdb_api_key()
        if not api_key:
            return None

        # If numeric TMDB ID
        if str(tmdb_id_or_title).isdigit():
            url = f"https://api.themoviedb.org/3/movie/{tmdb_id_or_title}?api_key={api_key}&language=ar-SA&append_to_response=credits,videos"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=6.0) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception:
                # Fallback to en-US
                try:
                    url_en = f"https://api.themoviedb.org/3/movie/{tmdb_id_or_title}?api_key={api_key}&language=en-US"
                    req = urllib.request.Request(url_en, headers={"User-Agent": USER_AGENT})
                    with urllib.request.urlopen(req, timeout=5.0) as resp:
                        return json.loads(resp.read().decode("utf-8"))
                except Exception:
                    return None

        # Search by title
        q = urllib.parse.quote(str(tmdb_id_or_title).strip())
        url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={q}&language=ar-SA"
        if year:
            url += f"&year={year}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=6.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("results", [])
                if results:
                    return cls.fetch_tmdb_movie(str(results[0]["id"]))
        except Exception:
            return None
        return None

    @classmethod
    def ingest_movie(cls, movie_data: Dict[str, Any]) -> bool:
        """Stores a fully structured movie in SQLite with quality and servers."""
        if not movie_data or not movie_data.get("title"):
            return False

        m_id = movie_data.get("id") or str(movie_data["title"]).lower().replace(" ", "-").replace(":", "")
        movie_data["id"] = m_id
        movie_data["content_type"] = "movie"
        if "category" not in movie_data:
            movie_data["category"] = "foreign"

        VODDatabaseManager.save_media(movie_data)
        return True
