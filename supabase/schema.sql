-- =====================================================================
-- Fairbill database. Paste this whole file into Supabase > SQL Editor > Run.
-- Safe to run once on a new project.
-- =====================================================================

-- 1. Advertised prices (used to reject impossible prices)
create table if not exists public.plans (
  provider     text not null,
  speed        int  not null,
  name         text not null,
  advertised   numeric(7,2) not null,
  checked      date not null default current_date,
  primary key (provider, speed)
);

-- Prices are loaded from plans.sql (generated from data/precios.csv). Run it right after this file.

-- 2. Every bill people share. This is your historical data.
create table if not exists public.reports (
  id          bigint generated always as identity primary key,
  created_at  timestamptz not null default now(),
  zip         char(5) not null check (zip ~ '^[0-9]{5}$'),
  provider    text not null,
  speed       int  not null,
  price       numeric(7,2) not null check (price > 0 and price < 1000),
  tenure      smallint not null check (tenure between 0 and 2),   -- 0: <1 yr, 1: 1-3 yrs, 2: 3+ yrs
  device_id   text not null check (length(device_id) between 8 and 64),
  form_ms     int,
  photo_path  text,
  verified    boolean not null default false,
  counted     boolean not null default true,
  flag        text                                               -- why a report was not counted
);
create index if not exists reports_zip_idx on public.reports (zip, provider, speed) where counted;
create index if not exists reports_device_idx on public.reports (device_id, created_at);

-- 3. Anti-fake rules, applied to every new report.
--    Reports that break a rule are saved but NOT counted, and the person is never told.
create or replace function public.check_report() returns trigger
language plpgsql security definer set search_path = public as $$
declare adv numeric;
begin
  new.verified := false;            -- only you can verify, from the dashboard
  new.counted  := true;
  new.flag     := null;
  new.created_at := now();

  select advertised into adv from plans where provider = new.provider and speed = new.speed;
  if adv is null then
    -- plan not in plans.sql yet: count it only if the price is reasonable
    if new.price < 10 or new.price > 400 then new.counted := false; end if;
    new.flag := 'unknown plan';
  elsif new.price < adv * 0.5 or new.price > adv * 2.5 then
    new.counted := false; new.flag := 'price out of range';
  elsif coalesce(new.form_ms, 0) < 3000 then
    new.counted := false; new.flag := 'filled too fast';
  elsif exists (select 1 from reports r where r.device_id = new.device_id and r.zip = new.zip
                and r.provider = new.provider and r.speed = new.speed and r.counted
                and r.created_at > now() - interval '180 days') then
    new.counted := false; new.flag := 'repeat from same device';
  elsif (select count(*) from reports r where r.device_id = new.device_id
         and r.created_at > now() - interval '1 hour') >= 5 then
    new.counted := false; new.flag := 'too many from same device';
  end if;
  return new;
end $$;

drop trigger if exists reports_check on public.reports;
create trigger reports_check before insert on public.reports
for each row execute function public.check_report();

-- 4. Privacy: visitors can ADD reports but never read the raw table.
alter table public.reports enable row level security;
alter table public.plans   enable row level security;
drop policy if exists "anyone can add a report" on public.reports;
create policy "anyone can add a report" on public.reports for insert to anon with check (true);
drop policy if exists "anyone can read plans" on public.plans;
create policy "anyone can read plans" on public.plans for select to anon using (true);

-- 5. What the website reads: summaries per ZIP, only for plans with 5+ reports.
--    Verified reports count double. Last 12 months only.
create or replace function public.zip_stats(z text)
returns table (provider text, speed int, n int, n_verified int, median float8, p10 float8, p90 float8,
               median_new float8, median_old float8, prices numeric[], verified_flags boolean[])
language sql stable security definer set search_path = public as $$
  with r as (
    select * from reports
    where zip = z and counted and created_at > now() - interval '12 months'
  ),
  w as (   -- weighted rows: verified reports appear twice
    select r.provider, r.speed, r.price from r
    cross join lateral generate_series(1, case when r.verified then 2 else 1 end)
  ),
  agg as (
    select r.provider, r.speed, count(*)::int as n,
           count(*) filter (where verified)::int as n_verified,
           count(*) filter (where tenure = 0)::int as n_new,
           count(*) filter (where tenure = 2)::int as n_old,
           percentile_cont(0.5) within group (order by price) filter (where tenure = 0) as m_new,
           percentile_cont(0.5) within group (order by price) filter (where tenure = 2) as m_old,
           array_agg(price order by price) as prices,
           array_agg(verified order by price) as vflags
    from r group by r.provider, r.speed
  ),
  wq as (
    select provider, speed,
           percentile_cont(0.5) within group (order by price) as med,
           percentile_cont(0.1) within group (order by price) as q10,
           percentile_cont(0.9) within group (order by price) as q90
    from w group by provider, speed
  )
  select a.provider, a.speed, a.n, a.n_verified,
         case when a.n >= 5 then q.med end,
         case when a.n >= 5 then q.q10 end,
         case when a.n >= 5 then q.q90 end,
         case when a.n >= 5 and a.n_new >= 3 then a.m_new end,
         case when a.n >= 5 and a.n_old >= 3 then a.m_old end,
         case when a.n >= 5 then a.prices end,
         case when a.n >= 5 then a.vflags end
  from agg a join wq q using (provider, speed);
$$;
revoke all on function public.zip_stats(text) from public;
grant execute on function public.zip_stats(text) to anon;

-- 6. Private storage for bill photos (only you can see them).
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('bills', 'bills', false, 5242880,
        array['image/jpeg','image/png','image/webp','image/heic','image/heif','application/pdf'])
on conflict (id) do nothing;
drop policy if exists "anyone can upload a bill photo" on storage.objects;
create policy "anyone can upload a bill photo" on storage.objects
for insert to anon with check (bucket_id = 'bills');

-- =====================================================================
-- HANDY QUERIES FOR YOU (run them in SQL Editor when you need them)
-- =====================================================================
-- Photos waiting for review:
--   select id, created_at, zip, provider, speed, price, photo_path
--   from reports where photo_path is not null and not verified order by created_at;
-- After checking a photo matches the price (then delete the file in Storage > bills):
--   update reports set verified = true, photo_path = null where id = 123;
-- If the photo does NOT match:
--   update reports set counted = false, flag = 'photo mismatch', photo_path = null where id = 123;
-- Reports not counted and why:
--   select flag, count(*) from reports where not counted group by flag;
-- Monthly trend for a plan in a ZIP (your historical data):
--   select date_trunc('month', created_at) as month, count(*),
--          percentile_cont(0.5) within group (order by price) as median
--   from reports where counted and zip = '78704' and provider = 'Spectrum' and speed = 500
--   group by 1 order by 1;
