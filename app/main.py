from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.investment import router as investment_router


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