from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.database import get_auth_session
from app.auth.security import (
    verify_password,
    create_access_token,
)
from app.api.dependencies import get_current_user
from app.models.api_user import APIUser
from app.schemas.auth import TokenResponse, UserResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_auth_session),
):
    result = await session.execute(
        select(APIUser).where(
            APIUser.username == form.username
        )
    )

    user = result.scalar_one_or_none()

    if user is None or not verify_password(
        form.password, user.hashed_password
    ) or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(user.id)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: APIUser = Depends(get_current_user),
):
    return user