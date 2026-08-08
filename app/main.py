from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.limiter import limiter
from app.routes.leads import router as leads_router
import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

app = FastAPI(title="INNOVI Solutions API", docs_url=None, redoc_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

app.include_router(leads_router)

@app.get("/health")
def health():
    return {"status": "ok"}