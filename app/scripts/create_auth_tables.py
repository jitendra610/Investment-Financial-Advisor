
"""
Authentication Database Initialization

Purpose:
1. Connect to PostgreSQL using an asynchronous engine.
2. Create authentication-related tables.
3. Preserve existing tables.
4. Display a success message.
"""

import asyncio
# Import asynchronous SQLAlchemy database engine
# configured for authentication.
from app.auth.database import engine

# Import AuthBase containing authentication table metadata.
# Authentication models must inherit from this base.
from app.models.api_user import AuthBase


async def main():
    # Open an asynchronous PostgreSQL connection.
    # engine.begin() starts a database transaction.
    async with engine.begin() as conn:
        # Create authentication tables registered in AuthBase.metadata.
        # create_all() creates only missing tables by default.
        # Existing tables are not recreated.
        #
        # run_sync() executes synchronous SQLAlchemy metadata
        # operations through the asynchronous connection.
        await conn.run_sync(AuthBase.metadata.create_all)

    print("Authentication tables created successfully.")


if __name__ == "__main__":
    asyncio.run(main())