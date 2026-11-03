import asyncio

from sqlalchemy import text

from app.core.config import settings
from app.db.database import AsyncSessionLocal, engine


def test_configuration():
    print("\n1. Testing configuration")

    assert settings.APP_NAME
    assert settings.DATABASE_URL.startswith(
        "postgresql+asyncpg://"
    )

    print("Configuration: PASSED")


async def test_database():
    print("\n2. Testing database connection")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT 1")
        )

        assert result.scalar_one() == 1

    print("Database connection: PASSED")


async def test_pgvector():
    print("\n3. Testing pgvector extension")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text(
                "SELECT extversion "
                "FROM pg_extension "
                "WHERE extname = 'vector'"
            )
        )

        version = result.scalar_one_or_none()

        assert version is not None, (
            "pgvector extension is not enabled"
        )

    print(f"pgvector version: {version}")
    print("pgvector: PASSED")


async def main():
    try:
        test_configuration()

        await test_database()

        await test_pgvector()

        print("\nALL TESTS PASSED")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())