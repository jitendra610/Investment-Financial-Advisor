from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db.database import AsyncSessionLocal


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
async def health():
    return {"status": "ok"}


@router.get("/db")
async def database_health():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))

        return {"database": "connected"}

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        )