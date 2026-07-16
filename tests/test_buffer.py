"""Tests for spc20.buffer — SQLite local telemetry buffer."""
import json
import os
import sqlite3
import tempfile
import pytest

from spc20.buffer import LocalBuffer


@pytest.fixture()
def tmp_db(tmp_path):
    return str(tmp_path / "test_spc20.db")


def _payload(observed_at="2026-07-16T10:00:00+00:00", pump=True, flow=320.0) -> dict:
    return {
        "observed_at": observed_at,
        "device_id": "test",
        "pump_running": pump,
        "flow_gpm_avg": flow,
    }


# ── insert ────────────────────────────────────────────────────────────────────

def test_enqueue_returns_row_id(tmp_db):
    buf = LocalBuffer(tmp_db)
    row_id = buf.enqueue(_payload())
    assert isinstance(row_id, int)
    assert row_id > 0


def test_enqueue_appears_in_pending(tmp_db):
    buf = LocalBuffer(tmp_db)
    buf.enqueue(_payload(observed_at="2026-07-16T10:00:00+00:00"))
    pending = buf.pending()
    assert len(pending) == 1


def test_pending_count(tmp_db):
    buf = LocalBuffer(tmp_db)
    buf.enqueue(_payload("2026-07-16T10:01:00+00:00"))
    buf.enqueue(_payload("2026-07-16T10:02:00+00:00"))
    assert buf.pending_count() == 2


# ── mark_uploaded ─────────────────────────────────────────────────────────────

def test_mark_uploaded(tmp_db):
    buf = LocalBuffer(tmp_db)
    row_id = buf.enqueue(_payload())
    buf.mark_uploaded(row_id)
    assert buf.pending_count() == 0


def test_mark_uploaded_removes_from_pending(tmp_db):
    buf = LocalBuffer(tmp_db)
    id1 = buf.enqueue(_payload("2026-07-16T10:01:00+00:00"))
    id2 = buf.enqueue(_payload("2026-07-16T10:02:00+00:00"))
    buf.mark_uploaded(id1)
    pending = buf.pending()
    ids = [row["id"] for row in pending]
    assert id1 not in ids
    assert id2 in ids


# ── retry of pending uploads ──────────────────────────────────────────────────

def test_pending_returns_only_not_uploaded(tmp_db):
    buf = LocalBuffer(tmp_db)
    id1 = buf.enqueue(_payload("2026-07-16T10:01:00+00:00"))
    id2 = buf.enqueue(_payload("2026-07-16T10:02:00+00:00"))
    buf.mark_uploaded(id1)
    pending = buf.pending()
    assert len(pending) == 1
    assert pending[0]["id"] == id2


def test_pending_preserves_payload(tmp_db):
    buf = LocalBuffer(tmp_db)
    p = _payload(flow=999.0)
    buf.enqueue(p)
    pending = buf.pending()
    loaded = json.loads(pending[0]["payload"])
    assert loaded["flow_gpm_avg"] == 999.0


# ── idempotent replay ─────────────────────────────────────────────────────────

def test_same_payload_twice_inserts_two_rows(tmp_db):
    """Two inserts of the same payload = two rows (idempotency is caller's responsibility)."""
    buf = LocalBuffer(tmp_db)
    p = _payload()
    buf.enqueue(p)
    buf.enqueue(p)
    # Both rows should be present — the buffer does not deduplicate
    assert buf.pending_count() == 2


# ── restart survival ──────────────────────────────────────────────────────────

def test_restart_survival(tmp_db):
    """Data written to SQLite survives a re-instantiation (simulates reboot)."""
    buf1 = LocalBuffer(tmp_db)
    id1 = buf1.enqueue(_payload("2026-07-16T10:01:00+00:00"))
    id2 = buf1.enqueue(_payload("2026-07-16T10:02:00+00:00"))
    buf1.mark_uploaded(id1)
    # "Reboot": create a new LocalBuffer pointing to the same file
    buf2 = LocalBuffer(tmp_db)
    assert buf2.pending_count() == 1
    pending = buf2.pending()
    assert pending[0]["id"] == id2


def test_integrity_check_passes_on_new_db(tmp_db):
    buf = LocalBuffer(tmp_db)
    assert buf.integrity_check() is True


def test_last_upload_time_none_when_nothing_uploaded(tmp_db):
    buf = LocalBuffer(tmp_db)
    buf.enqueue(_payload())
    assert buf.last_upload_time() is None


def test_last_upload_time_after_upload(tmp_db):
    buf = LocalBuffer(tmp_db)
    row_id = buf.enqueue(_payload(observed_at="2026-07-16T10:00:00+00:00"))
    buf.mark_uploaded(row_id)
    assert buf.last_upload_time() == "2026-07-16T10:00:00+00:00"
