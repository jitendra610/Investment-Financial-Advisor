import asyncio

from app.auth.database import engine
from app.models.api_user import AuthBase


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(AuthBase.metadata.create_all)

    print("Authentication tables created successfully.")


if __name__ == "__main__":
    asyncio.run(main())