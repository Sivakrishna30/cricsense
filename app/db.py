import sqlite3
from contextlib import contextmanager

from app.config import settings


@contextmanager
def source_db():
    conn = sqlite3.connect(settings.source_db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def analytics_db():
    conn = sqlite3.connect(settings.analytics_db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
