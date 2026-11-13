import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
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
    return Path(os.environ.get("PAYMENT_RECON_DB") or DEFAULT_DB_PATH)


def connect() -> sqlite3.Connection:
    # Schema creation is idempotent, so every connection can ensure it.
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def save_run(report_json: str) -> int:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with closing(connect()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO runs (created_at, report_json) VALUES (?, ?)",
            (created_at, report_json),
        )
        return cur.lastrowid


def list_runs(limit: int = 20) -> list[sqlite3.Row]:
    with closing(connect()) as conn:
        return conn.execute(
            "SELECT id, created_at FROM runs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()


def get_run(run_id: int) -> sqlite3.Row | None:
    with closing(connect()) as conn:
        return conn.execute(
            "SELECT id, created_at, report_json FROM runs WHERE id = ?", (run_id,)
        ).fetchone()
