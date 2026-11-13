import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = "data/recon.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    report_json TEXT NOT NULL
)
"""


def db_path() -> Path:
    return Path(DEFAULT_DB_PATH)


def connect() -> sqlite3.Connection:
    # Schema creation is idempotent, so every connection can ensure it.
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn
