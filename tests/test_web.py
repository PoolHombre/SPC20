"""Tests for spc20.web.app — Flask dashboard."""
import json
import os
import tempfile

import pytest

# Set required env vars before any spc20 imports
os.environ.setdefault("DEVICE_ID", "test-device-web")
os.environ.setdefault("DEVICE_TOKEN", "test-token-web")
os.environ.setdefault("SUPABASE_INGEST_URL", "http://localhost/test")
# Use a temp DB so tests don't touch /var/lib/spc20
_TMP_DB = tempfile.mktemp(suffix=".db")
os.environ["LOCAL_DB_PATH"] = _TMP_DB

from spc20.web.app import create_app


@pytest.fixture()
def client(tmp_path):
    # Each test gets a fresh DB path
    db = str(tmp_path / "test.db")
    os.environ["LOCAL_DB_PATH"] = db
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
    os.environ["LOCAL_DB_PATH"] = _TMP_DB


# ── /api/status ───────────────────────────────────────────────────────────────

def test_api_status_returns_200(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200


def test_api_status_is_json(client):
    resp = client.get("/api/status")
    data = resp.get_json()
    assert data is not None
    assert isinstance(data, dict)


def test_api_status_has_device_id(client):
    resp = client.get("/api/status")
    data = resp.get_json()
    assert "device_id" in data
    assert isinstance(data["device_id"], str)
    assert len(data["device_id"]) > 0


def test_api_status_no_device_token(client):
    """DEVICE_TOKEN must never appear in /api/status response."""
    resp = client.get("/api/status")
    raw = resp.get_data(as_text=True)
    assert "test-token-web" not in raw
    # Also check the key name doesn't leak
    assert "device_token" not in raw.lower()


def test_api_status_no_supabase_key(client):
    """No Supabase service role key in response."""
    resp = client.get("/api/status")
    raw = resp.get_data(as_text=True)
    assert "service_role" not in raw.lower()
    assert "SERVICE_ROLE" not in raw


def test_api_status_has_expected_fields(client):
    resp = client.get("/api/status")
    data = resp.get_json()
    expected_keys = [
        "device_id", "software_version", "trial_phase",
        "uptime_seconds", "upload_queue_depth", "db_integrity_ok",
    ]
    for key in expected_keys:
        assert key in data, f"Missing field: {key}"


# ── /api/health ───────────────────────────────────────────────────────────────

def test_api_health_returns_200(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_api_health_db_integrity_ok(client):
    resp = client.get("/api/health")
    data = resp.get_json()
    assert data["db_integrity"] is True


# ── /api/live ─────────────────────────────────────────────────────────────────

def test_api_live_returns_200(client):
    resp = client.get("/api/live")
    assert resp.status_code == 200


def test_api_live_has_status_field(client):
    resp = client.get("/api/live")
    data = resp.get_json()
    assert "status" in data


# ── Auth blocks calibration routes ───────────────────────────────────────────

def test_calibration_ambient_zero_requires_auth(client):
    """POST /api/calibration/ambient-zero without credentials → 401."""
    resp = client.post(
        "/api/calibration/ambient-zero",
        json={"channel": "p1"},
    )
    assert resp.status_code == 401


def test_calibration_static_baseline_requires_auth(client):
    """POST /api/calibration/static-baseline without credentials → 401."""
    resp = client.post(
        "/api/calibration/static-baseline",
        json={},
    )
    assert resp.status_code == 401


def test_calibration_accepted_with_open_auth(client, monkeypatch):
    """When no password is configured (DASHBOARD_PASSWORD not set), access is open."""
    # Remove both password env vars so auth falls through to 'open' mode
    monkeypatch.delenv("DASHBOARD_PASSWORD_HASH", raising=False)
    monkeypatch.delenv("DASHBOARD_PASSWORD", raising=False)

    import spc20.web.auth as auth_module
    # Patch verify_password to return True (simulates open config)
    monkeypatch.setattr(auth_module, "verify_password", lambda pw: True)

    resp = client.post(
        "/api/calibration/ambient-zero",
        json={"channel": "p1"},
        headers={"Authorization": "Basic dGVjaDp0ZXN0"},  # tech:test
    )
    assert resp.status_code == 200


# ── Debug mode check ──────────────────────────────────────────────────────────

def test_debug_mode_disabled(client, tmp_path):
    """create_app() must not produce an app with debug=True."""
    db = str(tmp_path / "debug_test.db")
    os.environ["LOCAL_DB_PATH"] = db
    app = create_app()
    assert app.debug is False
