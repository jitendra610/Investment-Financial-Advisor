"""Independent sync SQLAlchemy engine for Lesson 3; existing async DB untouched."""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, String, Text, Integer, ForeignKey
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

load_dotenv()
raw_url = os.getenv("DATABASE_URL")
if not raw_url:
    raise RuntimeError("Set DATABASE_URL in .env")
url = make_url(raw_url).set(drivername="postgresql+psycopg")
engine = create_engine(url, pool_pre_ping=True)

class RagBase(DeclarativeBase):
    pass

class KnowledgeChunk(RagBase):
    __tablename__ = "rag_knowledge_chunks"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list] = mapped_column(Vector(1536), nullable=False)


def initialize_database():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        RagBase.metadata.create_all(bind=conn)
