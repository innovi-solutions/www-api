import logging
import httpx

logger = logging.getLogger("innovi.security")
VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

async def verify_turnstile(token: str, ip: str, secret: str) -> bool:
    if not token:
        return False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(VERIFY_URL, data={
                "secret": secret,
                "response": token,
                "remoteip": ip,
            })
            return bool(resp.json().get("success"))
    except Exception:
        logger.exception("Turnstile verification errored")
        # Fail-closed: if we can't verify, we don't trust it
        return False