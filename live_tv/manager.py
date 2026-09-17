# -*- coding: utf-8 -*-
"""
A TuBe Live TV Package - Manager & Channel Provider
"""

import os
import json
from typing import List, Dict, Any, Optional

CHANNELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "channels.json")

class LiveTVManager:
    """Manages, categorizes, and serves live IPTV channels."""
    _cached_channels: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def load_channels(cls) -> List[Dict[str, Any]]:
        """Loads and normalizes channels from isolated live_tv directory."""
        if cls._cached_channels is not None:
            return cls._cached_channels

        channels = []
        if os.path.exists(CHANNELS_FILE):
            try:
                with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    for item in raw:
                        stream_url = item.get("streamUrl") or item.get("directHls") or item.get("url") or item.get("embedUrl") or ""
                        if not stream_url:
                            continue
                        channels.append({
                            "id": item.get("id") or f"live-{item.get('name', 'ch')}",
                            "name": item.get("name") or "قناة مباشرة",
                            "category": item.get("category") or item.get("group") or "قنوات عامة",
                            "logo": item.get("logo") or "assets/app_icon.jpg",
                            "url": stream_url,
                            "stream_url": stream_url,
                            "quality": item.get("quality") or "1080p FHD",
                            "badge": "مباشر ⚡",
                            "desc": item.get("desc") or f"البث المباشر لقناة {item.get('name')} بجودة فائقة.",
                            "is_live": True
                        })
            except Exception as e:
                print(f"[LiveTVManager] Error loading channels: {e}")

        cls._cached_channels = channels
        return cls._cached_channels

    @classmethod
    def get_categories(cls) -> List[str]:
        """Returns sorted unique categories."""
        channels = cls.load_channels()
        cats = sorted(list(set(c["category"] for c in channels if c.get("category"))))
        return ["الكل 🌟"] + cats

    @classmethod
    def get_channels(cls, category: str = "all", search: str = "") -> List[Dict[str, Any]]:
        """Filters live channels by category and search query."""
        channels = cls.load_channels()
        filtered = channels

        if category and category != "all" and category != "الكل 🌟":
            filtered = [c for c in filtered if c.get("category") == category]

        if search:
            q = search.strip().lower()
            filtered = [c for c in filtered if q in c.get("name", "").lower() or q in c.get("category", "").lower()]

        return filtered
