import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from app.main import limiter          # see note below if this import circles
from app.schemas import LeadIn, LeadOut
from app.services.db import insert_lead
from app.services.email import send_lead_notification
from app.security.turnstile import verify_turnstile
from app.security.checks import (
    is_honeypot_filled, is_too_fast, is_recent_duplicate, email_cap_reached,
)
from app.config import settings

logger = logging.getLogger("innovi.leads")
router = APIRouter(prefix="/api")

def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"

@router.post("/leads", response_model=LeadOut)
@limiter.limit("3/minute;10/day")
async def create_lead(
    payload: LeadIn,
    request: Request,
    background: BackgroundTasks,
) -> LeadOut:
    ip = client_ip(request)

    # Layer 1+2: honeypot & timing — silent drop, fake success
    if is_honeypot_filled(payload):
        logger.warning("Silent drop (honeypot filled: %r) from %s", payload.website, ip)
        return LeadOut()
    if is_too_fast(payload):
        logger.warning("Silent drop (too fast: %sms) from %s", payload.elapsed_ms, ip)
        return LeadOut()

    # Layer 3: Turnstile — the only check that visibly rejects
    if not await verify_turnstile(payload.turnstile_token, ip, settings.turnstile_secret):
        logger.warning("Turnstile failed from %s", ip)
        raise HTTPException(status_code=403, detail="Verification failed. Please refresh and try again.")

    # Layer 4: duplicate — fake success, no store, no email
    if is_recent_duplicate(payload.email):
        logger.info("Duplicate suppressed: %s", payload.email)
        return LeadOut()

    # Store (the one hard requirement)
    lead_id = insert_lead(payload, ip=ip)
    if lead_id is None:
        raise HTTPException(status_code=503, detail="Please try again shortly.")

    # Layer 5: circuit breaker — store yes, notify no
    if email_cap_reached():
        logger.warning("Daily email cap reached — lead %s stored, notification skipped", lead_id)
        return LeadOut()

    background.add_task(send_lead_notification, lead_id, payload)
    return LeadOut()