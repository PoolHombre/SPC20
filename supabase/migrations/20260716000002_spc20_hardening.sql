-- SPC 2.0 Build 1A Hardening Migration
-- 2026-07-16
--
-- Adds:
--   1. trial_runs table — tracks start/end of each named trial run
--   2. calibration_events table — mirrors the local SQLite calibration log in the cloud
--   3. Additional columns on readings_1min for trial metadata, corrected DP, dispatch result

-- ────────────────────────────────────────────────────────────────────────────
-- 1. trial_runs
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trial_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id       TEXT NOT NULL,
    trial_run_id    TEXT NOT NULL UNIQUE,          -- matches TRIAL_RUN_ID env var
    trial_phase     TEXT NOT NULL CHECK (trial_phase IN ('BENCH', 'YARD', 'FIELD')),
    site_id         TEXT,                           -- null for bench runs
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at        TIMESTAMPTZ,
    notes           TEXT,
    created_by      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_trial_runs_device_id ON trial_runs(device_id);
CREATE INDEX IF NOT EXISTS idx_trial_runs_phase ON trial_runs(trial_phase);

-- ────────────────────────────────────────────────────────────────────────────
-- 2. calibration_events
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS calibration_events (
    id                  BIGSERIAL PRIMARY KEY,
    device_id           TEXT NOT NULL,
    trial_phase         TEXT,
    trial_run_id        TEXT,
    channel             TEXT NOT NULL,              -- p1, p2, p3, flow, p2_p3_static
    mode                TEXT NOT NULL,              -- ambient_zero | static_baseline
    offset_value        REAL,
    units               TEXT DEFAULT 'mA',
    sample_count        INTEGER,
    sample_duration_sec REAL,
    mean                REAL,
    stddev              REAL,
    min_value           REAL,
    max_value           REAL,
    accepted            BOOLEAN NOT NULL DEFAULT TRUE,
    rejection_reason    TEXT,
    p2_static_mean      REAL,
    p3_static_mean      REAL,
    static_p23_offset   REAL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by          TEXT,
    notes               TEXT
);

CREATE INDEX IF NOT EXISTS idx_calib_device_id ON calibration_events(device_id);
CREATE INDEX IF NOT EXISTS idx_calib_trial_run  ON calibration_events(trial_run_id);
CREATE INDEX IF NOT EXISTS idx_calib_channel    ON calibration_events(channel);

-- ────────────────────────────────────────────────────────────────────────────
-- 3. readings_1min — additional columns for Build 1A hardening
-- ────────────────────────────────────────────────────────────────────────────

-- Trial provenance
ALTER TABLE readings_1min ADD COLUMN IF NOT EXISTS trial_phase    TEXT;
ALTER TABLE readings_1min ADD COLUMN IF NOT EXISTS trial_run_id   TEXT;

-- Calibration-corrected differential pressure
ALTER TABLE readings_1min ADD COLUMN IF NOT EXISTS filter_dp_psi_raw       REAL;
ALTER TABLE readings_1min ADD COLUMN IF NOT EXISTS filter_dp_psi_corrected REAL;

-- Pulsing / flow quality
ALTER TABLE readings_1min ADD COLUMN IF NOT EXISTS flow_near_zero_count INTEGER;

-- Dispatch result
ALTER TABLE readings_1min ADD COLUMN IF NOT EXISTS dispatch_status TEXT;     -- GREEN | YELLOW | RED
ALTER TABLE readings_1min ADD COLUMN IF NOT EXISTS dispatch_action TEXT;     -- NO_VISIT | ROUTE_TODAY | SEND_NOW
ALTER TABLE readings_1min ADD COLUMN IF NOT EXISTS reason          TEXT;
ALTER TABLE readings_1min ADD COLUMN IF NOT EXISTS confidence      REAL;
ALTER TABLE readings_1min ADD COLUMN IF NOT EXISTS summary         TEXT;
ALTER TABLE readings_1min ADD COLUMN IF NOT EXISTS recommended_first_checks JSONB;

-- Index for common dashboard queries
CREATE INDEX IF NOT EXISTS idx_readings_dispatch   ON readings_1min(dispatch_status);
CREATE INDEX IF NOT EXISTS idx_readings_trial_run  ON readings_1min(trial_run_id);
CREATE INDEX IF NOT EXISTS idx_readings_trial_phase ON readings_1min(trial_phase);

-- ────────────────────────────────────────────────────────────────────────────
-- 4. Row-level security (RLS) stubs
-- Devices write via the ingest Edge Function (service role) — no direct device access.
-- ────────────────────────────────────────────────────────────────────────────
ALTER TABLE trial_runs         ENABLE ROW LEVEL SECURITY;
ALTER TABLE calibration_events ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users (dashboard) to read
CREATE POLICY IF NOT EXISTS "allow_authenticated_read_trial_runs"
    ON trial_runs FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY IF NOT EXISTS "allow_authenticated_read_calib"
    ON calibration_events FOR SELECT
    TO authenticated
    USING (true);
