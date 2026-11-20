-- Nexus Research AI — saved reports (Supabase / Postgres).
--
-- SETUP (Sharjeel does this once, in his own Supabase project):
--   1. supabase.com → New project (free tier, no card) → open the
--      SQL Editor → paste this whole file → Run.
--   2. Project Settings → API → copy the Project URL and the
--      SERVICE_ROLE key (NOT the anon key) into Vercel → Project
--      Settings → Environment Variables (Production):
--        SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
--      …then redeploy. Until then the app keeps history on-device
--      (localStorage) and the api routes answer 503.
--
-- SECURITY: Row Level Security is ON with NO public policies, so the
-- anon key can read/write nothing. Only the service-role key (server
-- env only, used by api/history.ts) can touch this table.

create table if not exists public.reports (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  question text not null,
  mode text not null check (mode in ('live', 'demo')),
  depth text not null default 'Standard',
  style text not null default 'Detailed Report',
  words integer not null default 0,
  sources integer not null default 0,
  findings integer not null default 0,
  saved boolean not null default false,
  -- Full report payload: { md (live only), sources, kpis, flagged }.
  -- The demo report has md = null and renders from the app's static data.
  data jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists reports_created_at_idx
  on public.reports (created_at desc);

alter table public.reports enable row level security;
-- No policies on purpose: only the service-role key (api routes) may
-- read/write. Do NOT add a public read/insert policy.
