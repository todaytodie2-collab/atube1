# -*- coding: utf-8 -*-
"""
A TuBe Clean Architecture (v2.0) - Anime Harvester
Enriches anime series with studio metadata (MAPPA, Ufotable, Madhouse), character cards,
sub/dub indicators, and scene-based thumbnails.
"""

import os
import sys
import json
import time
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USER_AGENT, get_tmdb_api_key
from database import VODDatabaseManager

class AnimeHarvester:
    """Specialized anime scraper and metadata enricher."""

    POPULAR_STUDIOS = ["MAPPA", "ufotable", "Madhouse", "Wit Studio", "Bones", "Kyoto Animation", "A-1 Pictures", "TMS Entertainment", "Toei Animation"]

    @classmethod
    def enrich_anime_item(cls, media_id: str, studio_name: Optional[str] = None) -> bool:
        """Enriches an anime media entry in SQLite with studio and character tags."""
        conn = VODDatabaseManager.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, genres, production FROM vod_media WHERE id = ?", (media_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return False

        current_prod = row["production"] or ""
        if studio_name and studio_name not in current_prod:
            new_prod = f"{studio_name} / {current_prod}".strip(" /")
            cur.execute("UPDATE vod_media SET production = ?, category = 'anime', content_type = 'anime' WHERE id = ?", (new_prod, media_id))
            conn.commit()
        conn.close()
        return True
