# -*- coding: utf-8 -*-
"""Config package initialization."""
from config.settings import (
    BASE_DIR,
    PROJECT_ROOT,
    DB_PATH,
    SERVER_HOST,
    SERVER_PORT,
    DEBUG_MODE,
    USER_AGENT,
    get_tmdb_api_key,
    HOST_SPOOF_MAP,
    TRUSTED_EMBED_KEYWORDS,
    CATEGORY_MAP,
)

__all__ = [
    "BASE_DIR",
    "PROJECT_ROOT",
    "DB_PATH",
    "SERVER_HOST",
    "SERVER_PORT",
    "DEBUG_MODE",
    "USER_AGENT",
    "get_tmdb_api_key",
    "HOST_SPOOF_MAP",
    "TRUSTED_EMBED_KEYWORDS",
    "CATEGORY_MAP",
]
