"""
Independent synchronous SQLAlchemy engine for RAG.
The existing asynchronous database configuration remains unchanged.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import DateTime, func

# Import SQLAlchemy components for database operations.
from sqlalchemy import create_engine, text, String, Text, Integer, ForeignKey

# Import utility to parse and modify database connection URLs.
from sqlalchemy.engine import make_url
# Import SQLAlchemy ORM components to define database tables.
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

load_dotenv()
raw_url = os.getenv("DATABASE_URL")
if not raw_url:
    raise RuntimeError("Set DATABASE_URL in .env")

# Convert the database URL to use the synchronous psycopg driver.
url = make_url(raw_url).set(drivername="postgresql+psycopg")

# Create a synchronous SQLAlchemy database engine.
# pool_pre_ping=True checks connections before reusing them.
# This helps recover from stale or disconnected database connections.
engine = create_engine(
    url, 
    pool_pre_ping=True
    )


# Define the base class for RAG database models.
# SQLAlchemy uses this class to register ORM tables.
class RagBase(DeclarativeBase):
    pass

# Define the table used to store RAG document chunks.
class KnowledgeChunk(RagBase):
    __tablename__ = "rag_knowledge_chunks"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Vector embedding representing the meaning of the text.
    # 1536 dimensions are compatible with
    # OpenAI text-embedding-3-small default output.
    embedding: Mapped[list] = mapped_column(Vector(1536), nullable=False)


def initialize_database():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Create registered RAG tables if they do not exist.
        # Existing tables will not be recreated.
        RagBase.metadata.create_all(bind=conn)

class IngestedDocument(RagBase):
    __tablename__ = "rag_ingested_documents"

    # Relative document path.
    source: Mapped[str] = mapped_column(
        String(255),
        primary_key=True
    )

    # SHA-256 hash of document bytes.
    file_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )

    # Last successful ingestion timestamp.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )