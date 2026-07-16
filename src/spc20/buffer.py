"""Local SQLite telemetry buffer with WAL mode and upload queue."""
from __future__ import annotations
import json
import sqlite3
from contextlib import contextmanager
from typing import Generator


CREATE_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
PRAGMA busy_timeout=5000;

CREATE TABLE IF NOT EXISTS telemetry_queue (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    observed_at TEXT NOT NULL,
    payload    TEXT NOT NULL,
    uploaded   INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_uploaded ON telemetry_queue(uploaded);
"""


@contextmanager
def _conn(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    con = sqlite3.connect(db_path, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=FULL")
    con.execute("PRAGMA busy_timeout=5000")
    try:
        yield con
        con.commit()
    finally:
        con.close()


class LocalBuffer:
    def __init__(self, db_path: str = "/var/lib/spc20/spc20.db") -> None:
        self.db_path = db_path
        self._init()

    def _init(self) -> None:
        with _conn(self.db_path) as con:
            con.executescript(CREATE_SQL)

    def integrity_check(self) -> bool:
        """Run PRAGMA integrity_check. Returns True if database is intact."""
        with _conn(self.db_path) as con:
            rows = con.execute("PRAGMA integrity_check").fetchall()
        return len(rows) == 1 and rows[0][0] == "ok"

    def enqueue(self, payload: dict) -> int:
        with _conn(self.db_path) as con:
            cur = con.execute(
                "INSERT INTO telemetry_queue (observed_at, payload) VALUES (?, ?)",
                (payload["observed_at"], json.dumps(payload)),
            )
            return cur.lastrowid  # type: ignore

    def pending(self, limit: int = 50) -> list[sqlite3.Row]:
        with _conn(self.db_path) as con:
            return con.execute(
                "SELECT id, payload FROM telemetry_queue WHERE uploaded=0 ORDER BY id LIMIT ?",
                (limit,),
            ).fetchall()

    def pending_count(self) -> int:
        with _conn(self.db_path) as con:
            row = con.execute(
                "SELECT COUNT(*) FROM telemetry_queue WHERE uploaded=0"
            ).fetchone()
            return row[0] if row else 0

    def mark_uploaded(self, row_id: int) -> None:
        with _conn(self.db_path) as con:
            con.execute("UPDATE telemetry_queue SET uploaded=1 WHERE id=?", (row_id,))

    def last_upload_time(self) -> str | None:
        """Return the observed_at of the last successfully uploaded row, or None."""
        with _conn(self.db_path) as con:
            row = con.execute(
                "SELECT observed_at FROM telemetry_queue WHERE uploaded=1 ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return row["observed_at"] if row else None
