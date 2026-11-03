import asyncio

from sqlalchemy import inspect

from app.db.base import Base
from app.db.database import engine

# Import models to register tables in Base.metadata
import app.models


async def create_tables():
    async with engine.begin() as conn:

        # Create only missing tables
        await conn.run_sync(Base.metadata.create_all)

        # Verify tables
        tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )

        print("\nDatabase Tables:")
        for table in sorted(tables):
            print(f" - {table}")

    print("\nCustomer tables created successfully!")


async def main():
    try:
        await create_tables()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())