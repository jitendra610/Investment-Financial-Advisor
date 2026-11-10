from fastapi import FastAPI
import logging

from app.api.routes.auth import router as auth_router
from app.api.routes.investment import router as investment_router

from app.core.logging_config import setup_logging

# Initialize logging.
log_file = setup_logging()

logger = logging.getLogger(__name__)
logger.info("FastAPI application starting")

app = FastAPI(
    title="Investment Advisor API",
    description="Multi-Agent Investment Guidance API",
    version="1.0.0",
)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(
    auth_router,
    prefix="/api/v1",
)

app.include_router(
    investment_router,
    prefix="/api/v1",
)