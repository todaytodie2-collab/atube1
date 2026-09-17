# -*- coding: utf-8 -*-
"""
A TuBe Posters Engine - TMDB API Metadata & Poster Client
Provides enriched multi-source metadata: posters, backdrops, ratings, synopses, and full cast.
"""

import urllib.request
import urllib.parse
import json
import re
from typing import Dict, Any, Optional, List
from config import get_tmdb_api_key, USER_AGENT

class TMDBService:
    """Client for fetching high-resolution posters, backdrops, cast, and metadata from TMDB."""
    
    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_W500 = "https://image.tmdb.org/t/p/w500"
    IMAGE_BASE_ORIGINAL = "https://image.tmdb.org/t/p/original"

    @classmethod
    def clean_search_title(cls, title: str) -> str:
        """Strips Arabic and English release keywords (e.g. مدبلج, مترجم, الموسم, الحلقة, 1080p, Bluray)."""
        t = title
        # Remove season / episode patterns
        t = re.sub(r'الموسم\s*\d+|الحلقة\s*\d+|حلقة\s*\d+|موسم\s*\d+|S\d+E\d+|S\d+|E\d+', '', t, flags=re.IGNORECASE)
        # Remove tags
        t = re.sub(r'مترجم|مدبلج|مشاهدة|تحميل|فيلم|مسلسل|اون لاين|بجودة|عالية|كامل|HD|FHD|1080p|720p|WEB-DL|BluRay', '', t, flags=re.IGNORECASE)
        # Remove extra brackets and punctuation
        t = re.sub(r'[\(\)\[\]\{\}\-_:]', ' ', t)
        return t.strip()

    @classmethod
    def search_media(cls, query: str, content_type: str = "movie", year: Optional[str] = None) -> Optional[Dict[str, Any]]:
        clean_q = cls.clean_search_title(query) or query
        api_key = get_tmdb_api_key()
        endpoint = "tv" if content_type in ("series", "tv", "anime") else "movie"
        encoded_query = urllib.parse.quote(clean_q)
        url = f"{cls.BASE_URL}/search/{endpoint}?api_key={api_key}&query={encoded_query}&language=ar-SA"
        if year and str(year).isdigit():
            url += f"&year={year}" if endpoint == "movie" else f"&first_air_date_year={year}"

        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("results", [])
                if results:
                    return results[0]
        except Exception:
            pass
        return None

    @classmethod
    def get_full_metadata(cls, query: str, content_type: str = "movie", year: Optional[str] = None) -> Dict[str, Any]:
        """Fetches full rich metadata including TMDB ID, posters, backdrop, overview, genres, and cast."""
        search_res = cls.search_media(query, content_type, year)
        if not search_res:
            return {}

        tmdb_id = search_res.get("id")
        api_key = get_tmdb_api_key()
        endpoint = "tv" if content_type in ("series", "tv", "anime") else "movie"
        
        detail_url = f"{cls.BASE_URL}/{endpoint}/{tmdb_id}?api_key={api_key}&language=ar-SA&append_to_response=credits"
        req = urllib.request.Request(detail_url, headers={"User-Agent": USER_AGENT})
        
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                d = json.loads(resp.read().decode("utf-8"))
                poster_path = d.get("poster_path")
                backdrop_path = d.get("backdrop_path")
                
                # Parse cast
                cast_list = []
                credits = d.get("credits", {})
                for actor in credits.get("cast", [])[:10]:
                    profile = actor.get("profile_path")
                    cast_list.append({
                        "name": actor.get("name") or "",
                        "arabic_name": actor.get("name") or "",
                        "role": actor.get("character") or "شخصية رئيسية",
                        "photo": f"https://image.tmdb.org/t/p/w185{profile}" if profile else "assets/default_avatar.png"
                    })

                genres = [g.get("name") for g in d.get("genres", []) if g.get("name")]
                vote_avg = d.get("vote_average")
                rating = f"{vote_avg:.1f}" if vote_avg else "8.0"
                release_date = d.get("release_date") or d.get("first_air_date") or ""
                year_val = release_date[:4] if len(release_date) >= 4 else (year or "2024")

                return {
                    "tmdb_id": str(tmdb_id),
                    "arabic_title": d.get("title") or d.get("name") or query,
                    "original_title": d.get("original_title") or d.get("original_name") or query,
                    "poster": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "",
                    "backdrop": f"https://image.tmdb.org/t/p/original{backdrop_path}" if backdrop_path else "",
                    "synopsis": d.get("overview") or "",
                    "rating": rating,
                    "year": year_val,
                    "genres": genres,
                    "cast": cast_list,
                    "total_seasons": d.get("number_of_seasons") or 1 if endpoint == "tv" else 0
                }
        except Exception:
            pass

        return {}

    @classmethod
    def get_poster_url(cls, path: Optional[str], size: str = "w500") -> str:
        if not path:
            return ""
        if path.startswith("http"):
            return path
        base = cls.IMAGE_BASE_ORIGINAL if size == "original" else cls.IMAGE_BASE_W500
        return f"{base}{path}"
