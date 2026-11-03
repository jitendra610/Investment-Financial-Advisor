import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.database import get_auth_session
from app.auth.security import decode_access_token
from app.models.api_user import APIUser, CustomerAccess


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


def unauthorized():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_auth_session),
) -> APIUser:
    try:
        payload = decode_access_token(token)

        if payload.get("type") != "access":
            raise unauthorized()

        user_id = int(payload["sub"])

    except (jwt.PyJWTError, ValueError, KeyError):
        raise unauthorized()

    user = await session.get(APIUser, user_id)

    if user is None or not user.is_active:
        raise unauthorized()

    return user


async def require_customer_access(
    customer_id: str,
    user: APIUser,
    session: AsyncSession,
) -> None:
    stmt = select(CustomerAccess.user_id).where(
        CustomerAccess.user_id == user.id,
        CustomerAccess.customer_id == customer_id,
    )

    result = await session.execute(stmt)

    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to access this customer",
        )