#!/usr/bin/env python3
"""db_integrity_check.py — Check SPC 2.0 SQLite database integrity.

Reports:
  - PRAGMA integrity_check result
  - Row counts for each table
  - Pending (not yet uploaded) telemetry count

SECURITY: Never prints secrets, credentials, key material, or payload content.
Exit code: 0 = OK, 1 = degraded, 2 = error.
"""
from __future__ import annotations
import os
import sqlite3
import sys
from pathlib import Path


def main() -> int:
    db_path = os.getenv("LOCAL_DB_PATH", "/var/lib/spc20/spc20.db")

    if not Path(db_path).exists():
        print(f"[ERROR] Database not found: {db_path}")
        return 2

    print(f"Checking: {db_path}")
    print()

    try:
        con = sqlite3.connect(db_path, timeout=10)
        con.row_factory = sqlite3.Row
    except Exception as e:
        print(f"[ERROR] Cannot connect to database: {e}")
        return 2

    exit_code = 0

    try:
        # 1. Integrity check
        rows = con.execute("PRAGMA integrity_check").fetchall()
        integrity_ok = len(rows) == 1 and rows[0][0] == "ok"
        if integrity_ok:
            print("[OK]   PRAGMA integrity_check: ok")
        else:
            print(f"[FAIL] PRAGMA integrity_check:")
            for r in rows:
                print(f"       {r[0]}")
            exit_code = 1

        # 2. WAL mode
        wal = con.execute("PRAGMA journal_mode").fetchone()
        print(f"[INFO] Journal mode: {wal[0]}")

        # 3. Row counts per table
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        print()
        print("Table row counts:")
        for t in tables:
            try:
                count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                print(f"  {t}: {count} rows")
            except Exception as e:
                print(f"  {t}: ERROR — {e}")
                exit_code = 1

        # 4. Pending upload count
        if "telemetry_queue" in tables:
            pending = con.execute(
                "SELECT COUNT(*) FROM telemetry_queue WHERE uploaded=0"
            ).fetchone()[0]
            total = con.execute("SELECT COUNT(*) FROM telemetry_queue").fetchone()[0]
            print()
            print(f"Upload queue: {pending} pending / {total} total")

        # 5. Calibration events
        if "calibration_events" in tables:
            cal_count = con.execute("SELECT COUNT(*) FROM calibration_events").fetchone()[0]
            print(f"Calibration events: {cal_count} stored")

    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return 2
    finally:
        con.close()

    print()
    if exit_code == 0:
        print("Result: OK")
    else:
        print("Result: DEGRADED — review failures above")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
