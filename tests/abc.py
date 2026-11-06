# Dependency function to enforce that the authenticated user
import jwt
from fastapi import Depends, HTTPException, status
# Extracts the Bearer token from the Authorization header.
from fastapi.security import OAuth2PasswordBearer
# Used to construct SQL SELECT queries.
from sqlalchemy import select
# Provides asynchronous database operations.
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.database import get_auth_session
from app.auth.security import decode_access_token
from app.models.api_user import APIUser, CustomerAccess

# Configure OAuth2 Bearer authentication.
# FastAPI expects the token in the request header:
# Authorization: Bearer <access_token>
# tokenUrl specifies the login endpoint used by Swagger UI
# to obtain an access token.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


def unauthorized():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",

        headers={"WWW-Authenticate": "Bearer"}, # Indicates that Bearer authentication is required.
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


# create_api_user.py

import asyncio
import getpass

from sqlalchemy import select
from app.models.api_user import APIUser, CustomerAccess
from app.auth.database import AuthSessionLocal
from app.auth.security import hash_password
from app.models.api_user import APIUser, CustomerAccess


async def main():
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    if not username or len(password) < 12:
        raise ValueError(
            "Username is required and password must "
            "contain at least 12 characters"
        )

    async with AuthSessionLocal() as session:
        existing = await session.scalar(
            select(APIUser).where(
                APIUser.username == username
            )
        )

        if existing:
            raise ValueError("Username already exists")

        user = APIUser(
            username=username,
            hashed_password=hash_password(password),
            is_active=True,
        )

        session.add(user)
        await session.flush()

        session.add(
            CustomerAccess(
                user_id=user.id,
                customer_id="CUST-003",
            )
        )

        await session.commit()

    print("Development user created.")
    print("Authorized customer: CUST-003")


if __name__ == "__main__":
    asyncio.run(main())
