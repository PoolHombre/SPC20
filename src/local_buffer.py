from __future__ import annotations
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


CREATE_SQL = """
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
    try:
        yield con
        con.commit()
    finally:
        con.close()


class LocalBuffer:
    def __init__(self, db_path: str = "spc20_buffer.db") -> None:
        self.db_path = db_path
        self._init()

    def _init(self) -> None:
        with _conn(self.db_path) as con:
            con.executescript(CREATE_SQL)

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

    def mark_uploaded(self, row_id: int) -> None:
        with _conn(self.db_path) as con:
            con.execute("UPDATE telemetry_queue SET uploaded=1 WHERE id=?", (row_id,))
