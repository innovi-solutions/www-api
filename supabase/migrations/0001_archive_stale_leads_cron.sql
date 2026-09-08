-- Archives leads older than 30 days, checked daily but only acted on every 4 days.


create extension if not exists pg_cron with schema extensions;

alter table public.leads
  add column if not exists archived boolean not null default false,
  add column if not exists archived_at timestamptz;

create index if not exists leads_created_at_idx on public.leads (created_at);
create index if not exists leads_archived_idx on public.leads (archived);

-- Tracks when the archive job last actually ran, so cadence survives

create table if not exists public.cron_job_runs (
  job_name text primary key,
  last_run_at timestamptz
);

create or replace function public.archive_stale_leads()
returns void
language plpgsql
security definer
set search_path = public
as $func$
declare
  last_run timestamptz;
  stale_after interval := interval '30 days';
  run_every interval := interval '4 days';
begin
  select last_run_at into last_run
  from public.cron_job_runs
  where job_name = 'archive_stale_leads';

  if last_run is not null and now() - last_run < run_every then
    return;
  end if;

  update public.leads
  set archived = true,
      archived_at = now()
  where archived = false
    and created_at < now() - stale_after;

  insert into public.cron_job_runs (job_name, last_run_at)
  values ('archive_stale_leads', now())
  on conflict (job_name) do update set last_run_at = excluded.last_run_at;
end;
$func$;

do $$
begin
  if not exists (select 1 from cron.job where jobname = 'archive-stale-leads-daily-check') then
    perform cron.schedule(
      'archive-stale-leads-daily-check',
      '0 3 * * *',
      $job$select public.archive_stale_leads();$job$
    );
  end if;
end;
$$;
