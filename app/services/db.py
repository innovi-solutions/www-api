import hashlib
import logging
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger("innovi.db")

_client: Client | None = None

def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    return _client

def hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()

def insert_lead(payload, ip: str) -> str | None:
    """Insert a lead; return its id, or None on failure."""
    try:
        result = get_client().table("leads").insert({
            "session_type": payload.session,
            "name": payload.name,
            "email": payload.email.lower(),
            "company": payload.company,
            "preferred_date": payload.date.isoformat(),
            "project_type": payload.type,
            "message": payload.message,
            "consent": payload.consent,
            "ip_hash": hash_ip(ip),
        }).execute()
        return result.data[0]["id"]
    except Exception:
        logger.exception("Failed to insert lead")
        return None