import os
from dataclasses import dataclass
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import (
    create_engine, text, bindparam
)

load_dotenv()

# Prompt administration uses a synchronous connection.
# Your existing customer/RAG async connections remain unchanged.
db_url = os.environ["DATABASE_URL"].replace(
    "postgresql+asyncpg://",
    "postgresql+psycopg://",
)

engine = create_engine(db_url, pool_pre_ping=True)


@dataclass(frozen=True)
class PromptVersion:
    id: int
    agent: str
    version: int
    content: str
    is_active: bool


def create_prompt_table():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS agent_prompts (
                id BIGSERIAL PRIMARY KEY,
                agent VARCHAR(100) NOT NULL,
                version INTEGER NOT NULL CHECK (version > 0),
                content TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(agent, version)
            )
        """))

        # Enforce one active prompt per agent.
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS
                uq_active_agent_prompt
            ON agent_prompts(agent)
            WHERE is_active = TRUE
        """))


def add_prompt(agent: str, version: int, content: str):
    if not agent or not content.strip() or version < 1:
        raise ValueError("Invalid prompt details")

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO agent_prompts
                    (agent, version, content, is_active)
                VALUES
                    (:agent, :version, :content, FALSE)
                ON CONFLICT (agent, version) DO NOTHING
            """),
            {
                "agent": agent,
                "version": version,
                "content": content,
            },
        )


def get_prompt(agent: str, version: int | None = None):
    if version is None:
        sql = """
            SELECT id, agent, version, content, is_active
            FROM agent_prompts
            WHERE agent = :agent AND is_active = TRUE
        """
        params = {"agent": agent}
    else:
        sql = """
            SELECT id, agent, version, content, is_active
            FROM agent_prompts
            WHERE agent = :agent AND version = :version
        """
        params = {"agent": agent, "version": version}

    with engine.connect() as conn:
        row = conn.execute(text(sql), params).mappings().first()

    if row is None:
        raise LookupError(
            f"No matching prompt for {agent}, version={version}"
        )

    return PromptVersion(**dict(row))


def activate_prompt(agent: str, version: int):
    # Atomic activation with a per-agent transaction lock.
    # Prevents concurrent activations for the same agent.
    with engine.begin() as conn:
        conn.execute(
            text("""
                SELECT pg_advisory_xact_lock(
                    hashtext(:agent)::bigint
                )
            """),
            {"agent": agent},
        )

        exists = conn.execute(
            text("""
                SELECT id FROM agent_prompts
                WHERE agent = :agent AND version = :version
            """),
            {"agent": agent, "version": version},
        ).first()

        if exists is None:
            raise ValueError(
                f"Prompt not found: {agent} v{version}"
            )

        conn.execute(
            text("""
                UPDATE agent_prompts
                SET is_active = FALSE
                WHERE agent = :agent AND is_active = TRUE
            """),
            {"agent": agent},
        )

        conn.execute(
            text("""
                UPDATE agent_prompts
                SET is_active = TRUE
                WHERE agent = :agent AND version = :version
            """),
            {"agent": agent, "version": version},
        )


def list_prompts(agent: str):
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, agent, version, is_active, created_at
                FROM agent_prompts
                WHERE agent = :agent
                ORDER BY version
            """),
            {"agent": agent},
        ).mappings().all()

    return [dict(row) for row in rows]