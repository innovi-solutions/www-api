"""
Manual integration check for the archive_stale_leads() Supabase cron job.

Not a pytest suite - it hits the real project over the REST API, so it's
meant to be run on demand:

    python app/tests/pg_cron_test.py
    python app/tests/pg_cron_test.py --force-gate   # bypass the 4-day gate

Inserts a disposable stale lead and a fresh lead, calls archive_stale_leads(),
reports what happened, and deletes both test rows afterward regardless of
the outcome. Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env.
"""

import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
}

STALE_EMAIL = "cron-test-stale@example.com"
FRESH_EMAIL = "cron-test-fresh@example.com"


def insert_lead(email: str, name: str, ip_hash: str, created_at: str | None = None) -> dict:
    payload = {
        "session_type": "discovery",
        "name": name,
        "email": email,
        "company": "CRON TEST",
        "preferred_date": "2026-09-01",
        "project_type": "Custom Software",
        "message": "Dummy row for testing archive_stale_leads cron - safe to delete",
        "consent": True,
        "ip_hash": ip_hash,
    }
    if created_at:
        payload["created_at"] = created_at
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/leads",
        headers={**HEADERS, "Prefer": "return=representation"},
        json=payload,
    )
    r.raise_for_status()
    return r.json()[0]


def delete_lead(lead_id: str) -> None:
    requests.delete(
        f"{SUPABASE_URL}/rest/v1/leads",
        headers=HEADERS,
        params={"id": f"eq.{lead_id}"},
    )


def get_lead(lead_id: str) -> dict:
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/leads",
        headers=HEADERS,
        params={"id": f"eq.{lead_id}", "select": "id,name,created_at,archived,archived_at"},
    )
    r.raise_for_status()
    return r.json()[0]


def get_cron_job_runs() -> list:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/cron_job_runs", headers=HEADERS)
    r.raise_for_status()
    return r.json()


def set_last_run_at(iso_timestamp: str) -> None:
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/cron_job_runs",
        headers=HEADERS,
        params={"job_name": "eq.archive_stale_leads"},
        json={"last_run_at": iso_timestamp},
    )


def call_archive_stale_leads() -> None:
    r = requests.post(f"{SUPABASE_URL}/rest/v1/rpc/archive_stale_leads", headers=HEADERS, json={})
    r.raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force-gate",
        action="store_true",
        help="Backdate cron_job_runs.last_run_at 5 days so the 4-day gate doesn't block this run.",
    )
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    stale_created_at = (now - timedelta(days=35)).isoformat()

    print("Inserting test leads...")
    stale = insert_lead(STALE_EMAIL, "CRON TEST - stale", "cron-test-hash-stale", created_at=stale_created_at)
    fresh = insert_lead(FRESH_EMAIL, "CRON TEST - fresh", "cron-test-hash-fresh")
    print(f"  stale: {stale['id']} (created_at={stale['created_at']})")
    print(f"  fresh: {fresh['id']} (created_at={fresh['created_at']})")

    try:
        runs_before = get_cron_job_runs()

        if args.force_gate:
            backdated = (now - timedelta(days=5)).isoformat()
            print(f"--force-gate: backdating last_run_at to {backdated}")
            set_last_run_at(backdated)

        print("Calling archive_stale_leads()...")
        call_archive_stale_leads()

        stale_after = get_lead(stale["id"])
        fresh_after = get_lead(fresh["id"])
        runs_after = get_cron_job_runs()

        print(f"stale after: archived={stale_after['archived']} archived_at={stale_after['archived_at']}")
        print(f"fresh after: archived={fresh_after['archived']} archived_at={fresh_after['archived_at']}")
        print(f"cron_job_runs: {runs_after}")

        if runs_after == runs_before:
            print(
                "\nGATED: last_run_at didn't change, so the 4-day cadence check blocked this run "
                "(expected if archive_stale_leads ran within the last 4 days). "
                "Re-run with --force-gate to bypass it for testing."
            )
        elif stale_after["archived"] and not fresh_after["archived"]:
            print("\nPASS: stale lead archived, fresh lead untouched.")
        else:
            print("\nUNEXPECTED RESULT - inspect manually.")
    finally:
        print("Cleaning up test leads...")
        delete_lead(stale["id"])
        delete_lead(fresh["id"])
        print("Done.")


if __name__ == "__main__":
    main()
