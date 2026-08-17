import sqlite3
from collections.abc import Generator
from pathlib import Path

from fastapi import HTTPException

from src.config import DB_PATH

def get_db() -> Generator[sqlite3.Connection, None, None]:

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)

        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e!s}")
    finally:
        if conn:
            conn.close()