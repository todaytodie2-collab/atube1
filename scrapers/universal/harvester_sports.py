# -*- coding: utf-8 -*-
"""
A TuBe Clean Architecture (v2.0) - WWE & Sports Harvester
Fetches and structures WWE shows (RAW, SmackDown, NXT, WrestleMania, Royal Rumble).
"""

import os
import sys
import json
import time
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import VODDatabaseManager

class SportsWrestlingHarvester:
    """Manages WWE weekly shows, pay-per-view events, and match records."""

    @classmethod
    def register_wwe_event(cls, title: str, arabic_title: str, event_date: str, quality: str = "1080p 60fps") -> str:
        event_id = f"wwe-{title.lower().replace(' ', '-')}"
        data = {
            "id": event_id,
            "title": title,
            "arabic_title": arabic_title,
            "content_type": "wwe",
            "category": "wwe",
            "year": event_date[:4] if event_date else "2024",
            "rating": "9.0",
            "duration": "180 دقيقة",
            "quality": quality,
            "genres": ["مصارعة حرة", "عروض أسبوعية", "رياضة"],
            "production": "WWE Network / USA Network",
            "synopsis": f"عرض {arabic_title} المباشر كاملاً ومترجماً بأعلى جودة مع نزالات اللقب والأحداث النارية."
        }
        VODDatabaseManager.save_media(data)
        return event_id
