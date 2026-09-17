# -*- coding: utf-8 -*-
"""
A TuBe Scrapers Engine - Base Scraper & Request Helper
Provides common HTTP headers, request timeouts, and error handling for scrapers.
"""

import urllib.request
import urllib.parse
from typing import Dict, Any, Optional
from config import USER_AGENT

class BaseScraper:
    """Base class for all site scrapers."""

    DEFAULT_HEADERS = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ar,en-US;q=0.7,en;q=0.3",
        "Connection": "keep-alive"
    }

    @classmethod
    def get_headers(cls, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = cls.DEFAULT_HEADERS.copy()
        if extra_headers:
            headers.update(extra_headers)
        return headers

    @classmethod
    def fetch_url(cls, url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> Optional[str]:
        req = urllib.request.Request(url, headers=cls.get_headers(headers))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception:
            return None
