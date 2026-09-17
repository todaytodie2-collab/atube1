# -*- coding: utf-8 -*-
"""
A TuBe Database Connection Engine
Provides thread-safe SQLite connection with WAL mode and busy timeout.
"""

import os
import sqlite3
from config import DB_PATH

def get_db_connection() -> sqlite3.Connection:
    """Returns a thread-safe connection to the SQLite database with WAL mode configured."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=15000;")
    conn.row_factory = sqlite3.Row
    return conn
