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