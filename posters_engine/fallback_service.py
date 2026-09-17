# -*- coding: utf-8 -*-
"""
A TuBe Posters Engine - Thumbnail & Poster Fallback Service
Protects series and episodes from rogue foreign keywords or missing assets.
"""

from typing import Optional, Dict, Any

def get_episode_thumbnail(episode_thumbnail: Optional[str], parent_media: Dict[str, Any]) -> str:
    """
    Strict Fallback Engine:
    1. If the episode has an authentic TMDB scene still, use it.
    2. Fallback ONLY to parent series backdrop or poster.
    3. Global default platform asset (/assets/default_episode_thumb.jpg).
    Prevents foreign movie name keywords (gladiator, avengers) from leaking into series episodes.
    """
    rogue_keywords = ("gladiator", "avengers", "gladiator_hero")
    if episode_thumbnail and isinstance(episode_thumbnail, str) and episode_thumbnail.strip():
        thumb = episode_thumbnail.strip()
        if not any(kw in thumb.lower() for kw in rogue_keywords):
            return thumb

    # 2. Parent Series Fallback ONLY (Backdrop or Poster of the parent series)
    parent_backdrop = (parent_media.get("backdrop") or "").strip()
    parent_poster = (parent_media.get("poster") or parent_media.get("poster_url") or "").strip()
    if parent_backdrop and not any(kw in parent_backdrop.lower() for kw in rogue_keywords):
        return parent_backdrop
    if parent_poster and not any(kw in parent_poster.lower() for kw in rogue_keywords):
        return parent_poster

    # 3. Global Platform Safe Default
    return "/assets/default_episode_thumb.jpg"
