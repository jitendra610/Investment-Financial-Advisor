
"""
Database Table Creation Script

Purpose:
1. Connect to PostgreSQL using an asynchronous SQLAlchemy engine.
2. Register all database models.
3. Create missing database tables.
4. Display all available tables.
5. Close database connections safely.
"""

import asyncio
# Import inspect to retrieve database schema information.
from sqlalchemy import inspect
# Import SQLAlchemy Base class.
# All application ORM models should inherit from this Base.
from app.db.base import Base
from app.db.database import engine

# Import application models to register their tables in Base.metadata.
# Without importing models, SQLAlchemy may not know which tables to create.
import app.models


async def create_tables():
    # Open a database connection and begin a transaction.
    async with engine.begin() as conn:

        # Create only missing tables
        # run_sync() allows synchronous SQLAlchemy metadata
        # operations to execute using an async connection
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
        # Close the engine's pooled database connections.
        # Runs even if table creation raises an exception.
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())