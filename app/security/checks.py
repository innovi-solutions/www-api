import logging
from datetime import datetime, timedelta, timezone
from app.services.db import get_client

logger = logging.getLogger("innovi.security")

MIN_ELAPSED_MS = 3000        # forms filled in under 3s are bots
DUPLICATE_WINDOW_MIN = 10    # same email within 10 min = duplicate
DAILY_EMAIL_CAP = 50         # max notification emails per day

def is_honeypot_filled(payload) -> bool:
    return bool(payload.website.strip())

def is_too_fast(payload) -> bool:
    return payload.elapsed_ms < MIN_ELAPSED_MS

def is_recent_duplicate(email: str) -> bool:
    """Same email submitted within the window? On DB error, allow (fail-open)."""
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=DUPLICATE_WINDOW_MIN)).isoformat()
    try:
        result = (
            get_client().table("leads")
            .select("id")
            .eq("email", email.lower())
            .gte("created_at", cutoff)
            .limit(1)
            .execute()
        )
        return len(result.data) > 0
    except Exception:
        logger.exception("Duplicate check failed")
        return False

def email_cap_reached() -> bool:
    """Have we already sent today's quota of notifications? On error, assume yes (protect quota)."""
    midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    try:
        result = (
            get_client().table("leads")
            .select("id", count="exact")
            .eq("email_sent", True)
            .gte("created_at", midnight)
            .execute()
        )
        return (result.count or 0) >= DAILY_EMAIL_CAP
    except Exception:
        logger.exception("Email cap check failed")
        return True