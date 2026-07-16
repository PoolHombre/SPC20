-- SPC 2.0 initial schema
-- Run via: supabase db push  OR  apply_migration MCP tool

create extension if not exists "pgcrypto";

-- Pools (one row per physical pool)
create table pools (
  id               uuid primary key default gen_random_uuid(),
  name             text not null,
  location_name    text,
  pool_volume_gal  numeric,
  required_flow_gpm numeric,
  filter_warning_hours numeric default 24,
  created_at       timestamptz default now()
);

-- Devices (one row per hardware box)
create table devices (
  id                text primary key,
  pool_id           uuid references pools(id),
  name              text,
  device_token_hash text,
  active            boolean default true,
  created_at        timestamptz default now()
);

-- Per-device sensor and threshold configuration
create table device_configs (
  device_id                        text primary key references devices(id),
  p1_min_psi                       numeric default -15,
  p1_max_psi                       numeric default 15,
  p2_min_psi                       numeric default 0,
  p2_max_psi                       numeric default 100,
  p3_min_psi                       numeric default 0,
  p3_max_psi                       numeric default 100,
  flow_min_gpm                     numeric default 0,
  flow_max_gpm                     numeric default 500,
  pipe_inside_diameter_in          numeric,
  filter_clean_dp_psi              numeric default 5,
  filter_service_dp_psi            numeric default 12,
  low_flow_red_threshold_percent   numeric default 20,
  red_confirm_seconds              integer default 60,
  stale_data_red_minutes           integer default 10,
  updated_at                       timestamptz default now()
);

-- One-minute telemetry readings
create table readings_1min (
  id                        bigint generated always as identity primary key,
  device_id                 text references devices(id),
  observed_at               timestamptz not null,
  pump_running              boolean,
  p1_suction_psi_avg        numeric,
  p1_suction_psi_min        numeric,
  p1_suction_psi_max        numeric,
  p2_filter_inlet_psi_avg   numeric,
  p2_filter_inlet_psi_min   numeric,
  p2_filter_inlet_psi_max   numeric,
  p3_filter_outlet_psi_avg  numeric,
  p3_filter_outlet_psi_min  numeric,
  p3_filter_outlet_psi_max  numeric,
  filter_dp_psi_avg         numeric,
  flow_gpm_avg              numeric,
  flow_gpm_min              numeric,
  flow_gpm_max              numeric,
  flow_gpm_stddev           numeric,
  samples                   integer,
  raw                       jsonb,
  inserted_at               timestamptz default now(),
  unique(device_id, observed_at)
);

create index on readings_1min(device_id, observed_at desc);

-- Current route status per pool (one live row per pool)
create table route_status_current (
  pool_id          uuid primary key references pools(id),
  device_id        text references devices(id),
  dispatch_status  text not null check (dispatch_status in ('GREEN','YELLOW','RED')),
  dispatch_action  text not null check (dispatch_action in ('NO_VISIT','ROUTE_TODAY','SEND_NOW')),
  reason           text,
  summary          text,
  confidence       numeric,
  evidence         jsonb,
  recommended_first_checks jsonb,
  updated_at       timestamptz default now()
);

-- Historical status events
create table status_events (
  id              bigint generated always as identity primary key,
  pool_id         uuid references pools(id),
  device_id       text references devices(id),
  started_at      timestamptz,
  ended_at        timestamptz,
  dispatch_status text,
  reason          text,
  summary         text,
  evidence        jsonb,
  created_at      timestamptz default now()
);

-- Seed: one bench device and pool for initial testing
insert into pools (id, name, location_name, pool_volume_gal, required_flow_gpm)
values (
  '00000000-0000-0000-0000-000000000001',
  'Bench Test Pool',
  'Poolsure Workshop',
  50000,
  300
);

insert into devices (id, pool_id, name, device_token_hash, active)
values (
  'spc20-poc-0001',
  '00000000-0000-0000-0000-000000000001',
  'Bench POC Unit',
  -- hash of 'bench-test-token-replace-me' — replace with: select encode(digest('your-token','sha256'),'hex')
  encode(digest('bench-test-token-replace-me','sha256'),'hex'),
  true
);

insert into device_configs (device_id)
values ('spc20-poc-0001');
