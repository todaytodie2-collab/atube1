# -*- coding: utf-8 -*-
"""
A TuBe Clean Architecture (v2.0) - Asian & Turkish Drama Harvester
Manages ongoing weekly Turkish and Asian series releases, tracking airing status.
"""

import os
import sys
import json
import time
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import VODDatabaseManager

class AsianTurkishHarvester:
    """Manages Turkish & Asian drama episodic updates and ongoing status."""

    @classmethod
    def mark_ongoing_status(cls, media_id: str, is_ongoing: bool = True) -> bool:
        conn = VODDatabaseManager.get_connection()
        cur = conn.cursor()
        status_tag = "جاري العرض" if is_ongoing else "مكتمل"
        cur.execute("UPDATE vod_media SET sub_category = ? WHERE id = ?", (status_tag, media_id))
        conn.commit()
        conn.close()
        return True
