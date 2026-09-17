# -*- coding: utf-8 -*-
"""
A TuBe Database Package
Provides unified VODDatabaseManager, repositories, and connection management.
"""

import sqlite3
from typing import Dict, Any, List, Optional
from database.connection import get_db_connection
from database.schema import init_tables
from database.vod_repo import VODRepository
from database.servers_repo import ServersRepository

class VODDatabaseManager:
    """Unified Facade for Database operations."""

    @staticmethod
    def get_connection() -> sqlite3.Connection:
        return get_db_connection()

    @classmethod
    def init_db(cls):
        return init_tables()

    @classmethod
    def get_feed(cls, content_type: str = "all", category: str = "all", page: int = 1, limit: int = 40, search: str = "") -> Dict[str, Any]:
        return VODRepository.get_feed(content_type=content_type, category=category, page=page, limit=limit, search=search)

    @classmethod
    def get_details(cls, media_id: str) -> Optional[Dict[str, Any]]:
        return VODRepository.get_details(media_id)

    @classmethod
    def get_cast(cls, media_id: str) -> List[Dict[str, Any]]:
        return VODRepository.get_cast(media_id)

    @classmethod
    def get_episodes(cls, media_id: str, season_number: int = 1) -> List[Dict[str, Any]]:
        return VODRepository.get_episodes(media_id, season_number)

    @classmethod
    def get_recent_episodes(cls, category: str = "all", limit: int = 16) -> List[Dict[str, Any]]:
        return VODRepository.get_recent_episodes(category, limit)

    @classmethod
    def save_media(cls, media_data: Dict[str, Any]):
        return VODRepository.save_media(media_data)

    @classmethod
    def insert_media(cls, content_type: str = "movie", title: str = "", category: str = "arabic", link: str = "", servers: Optional[List[Any]] = None, **kwargs) -> str:
        return VODRepository.insert_media(content_type=content_type, title=title, category=category, link=link, servers=servers, **kwargs)

    @classmethod
    def insert_series_episode(cls, series_title: str, season_number: int = 1, episode_number: int = 1,
                              category: str = "foreign_series", link: str = "", servers: Optional[List[Any]] = None,
                              episode_title: Optional[str] = None, thumbnail: Optional[str] = None, **kwargs) -> str:
        return VODRepository.insert_series_episode(
            series_title=series_title,
            season_number=season_number,
            episode_number=episode_number,
            category=category,
            link=link,
            servers=servers,
            episode_title=episode_title,
            thumbnail=thumbnail,
            **kwargs
        )

    @classmethod
    def add_server(cls, media_id: str, stream_url: str, server_name: str = "سيرفر مشاهدة مباشر", 
                   quality: str = "1080p FHD", badge: str = "VIP ⚡", site: str = "Direct",
                   season_number: Optional[int] = None, episode_number: Optional[int] = None) -> bool:
        return ServersRepository.add_server(
            media_id=media_id,
            stream_url=stream_url,
            server_name=server_name,
            quality=quality,
            badge=badge,
            site=site,
            season_number=season_number,
            episode_number=episode_number
        )

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        return VODRepository.get_stats()


__all__ = [
    "get_db_connection",
    "init_tables",
    "VODRepository",
    "ServersRepository",
    "VODDatabaseManager"
]
