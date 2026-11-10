"""
Agent Prompt Management System

Purpose:
1. Store agent-specific system prompts in PostgreSQL.
2. Maintain multiple versions of each agent prompt.
3. Activate or deactivate prompt versions.
4. Retrieve active or specific prompt versions.
5. Prevent multiple active prompts for the same agent.
6. Support prompt version tracking and auditing.


create_prompt_table()	Creates prompt table and unique active-prompt index
add_prompt()	Inserts a new inactive prompt version
get_prompt()	Retrieves active or specified prompt
activate_prompt()	Activates one version and deactivates the previous version
list_prompts()	Lists all prompt versions for an agent
"""


import os
# Import dataclass to define a structured prompt object.
from dataclasses import dataclass
from datetime import datetime, timezone

from dotenv import load_dotenv
# Import SQLAlchemy engine and text for executing SQL queries.
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

# Create synchronous PostgreSQL database engine.
# pool_pre_ping=True checks database connections before reuse.
engine = create_engine(db_url, pool_pre_ping=True)

# Define immutable data structure for storing prompt details.
@dataclass(frozen=True)
class PromptVersion:
    id: int
    agent: str
    version: int
    content: str
    is_active: bool

# Create PostgreSQL table for storing agent prompts.
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

# Insert a new prompt version for a particular agent.
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

#GET ACTIVE OR SPECIFIC PROMPT
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

# Activate a specific prompt version for an agent.
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