# -*- coding: utf-8 -*-
"""
A TuBe Clean Architecture - VOD Database Engine Facade
Re-exports VODDatabaseManager, repositories, and connection management from `database`.
"""

from database import (
    get_db_connection,
    init_tables,
    VODRepository,
    ServersRepository,
    VODDatabaseManager,
)

__all__ = [
    "get_db_connection",
    "init_tables",
    "VODRepository",
    "ServersRepository",
    "VODDatabaseManager",
]
