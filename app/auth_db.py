import sqlite3
from contextlib import contextmanager

from app.config import settings


AUTH_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    display_name TEXT,
    avatar_url TEXT,
    plan_tier TEXT NOT NULL DEFAULT 'free',
    created_at TEXT NOT NULL,
    last_login_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_identities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    provider_user_id TEXT NOT NULL,
    provider_email TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(provider, provider_user_id),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    refresh_token_hash TEXT NOT NULL UNIQUE,
    device_label TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_auth_identities_user_id ON auth_identities(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
"""


def init_auth_db() -> None:
    conn = sqlite3.connect(settings.auth_db_path)
    try:
        conn.executescript(AUTH_SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def auth_db():
    init_auth_db()
    conn = sqlite3.connect(settings.auth_db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
