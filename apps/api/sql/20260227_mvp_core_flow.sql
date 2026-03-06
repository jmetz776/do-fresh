-- DemandOrchestrator MVP Core Flow schema (Postgres)
-- Created: 2026-02-27

create extension if not exists pgcrypto;

create type source_type as enum ('csv','url');
create type source_status as enum ('pending','normalized','failed');
create type content_status as enum ('draft','approved','scheduled','published','failed');
create type schedule_status as enum ('scheduled','processing','published','failed','canceled');
create type job_status as enum ('queued','processing','succeeded','failed');

create table if not exists workspaces (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now()
);

create table if not exists sources (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id) on delete cascade,
  type source_type not null,
  raw_payload text not null,
  status source_status not null default 'pending',
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists source_items (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references sources(id) on delete cascade,
  external_ref text,
  title text,
  body text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists content_items (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references workspaces(id) on delete cascade,
  source_item_id uuid references source_items(id) on delete set null,
  channel text not null,
  title text,
  hook text,
  caption text not null,
  variant_no int not null default 1,
  status content_status not null default 'draft',
  provider_post_id text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists schedules (
  id uuid primary key default gen_random_uuid(),
  content_item_id uuid not null references content_items(id) on delete cascade,
  publish_at timestamptz not null,
  timezone text not null default 'America/New_York',
  status schedule_status not null default 'scheduled',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists publish_jobs (
  id uuid primary key default gen_random_uuid(),
  schedule_id uuid not null references schedules(id) on delete cascade,
  attempt int not null default 1,
  idempotency_key text not null,
  status job_status not null default 'queued',
  provider_response jsonb,
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (idempotency_key, attempt)
);

create unique index if not exists uniq_schedule_content_time
  on schedules(content_item_id, publish_at);

create index if not exists idx_schedules_due
  on schedules(status, publish_at);

create index if not exists idx_content_status
  on content_items(status);
