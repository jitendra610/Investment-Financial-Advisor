from collections.abc import AsyncGenerator


# AsyncSession: Supports asynchronous database operations.
# async_sessionmaker: Factory for creating async DB sessions.
# create_async_engine: Creates an asynchronous database engine.
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# The engine manages database connections and connection pooling.

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5, # Maintain up to 5 persistent connections in the pool.
    max_overflow=10,  # Allow up to 10 additional temporary connections
    pool_pre_ping=True,
)

# Used to create independent sessions for database operations.
AsyncSessionLocal = async_sessionmaker(
    bind=engine, # Bind the session factory to the database engine.
    class_=AsyncSession,
    expire_on_commit=False, # Prevents automatic expiration of loaded attributes.docker 
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # Create a new asynchronous database session.
    # The session is automatically closed when this block exits.
    async with AsyncSessionLocal() as session:
        # Provide the session to the FastAPI endpoint.
        # Execution resumes here for cleanup after dependency use
        yield session