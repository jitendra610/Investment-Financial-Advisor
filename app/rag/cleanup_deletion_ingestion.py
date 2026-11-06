
from pathlib import Path
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.rag.database import (
    engine,
    KnowledgeChunk,
    IngestedDocument,
)


def cleanup_deleted_documents(
    folder: str = "knowledge_base",
    dry_run: bool = True,
) -> dict:
    """
    Remove RAG records for documents no longer present on disk.

    dry_run=True  -> Only show which documents would be deleted.
    dry_run=False -> Delete chunks and document tracking records.
    """

    # Identify the knowledge base directory.
    root = Path(folder).resolve()

    # Prevent accidental deletion if the folder is missing.
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(
            f"Knowledge base folder not found: {root}"
        )

    # Find all supported documents currently present on disk.
    # Use relative paths to match incremental ingestion source IDs.
    existing_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".pdf", ".md", ".txt"}
    }

    # Open PostgreSQL session.
    with Session(engine) as session:

        # Read document source IDs from the ingestion registry.
        registered_files = set(
            session.scalars(
                select(IngestedDocument.source)
            ).all()
        )

        # Identify documents that exist in DB but not on disk.
        deleted_files = sorted(
            registered_files - existing_files
        )

        # Return without modifying the database in dry-run mode.
        if dry_run:
            return {
                "dry_run": True,
                "deleted_count": 0,
                "would_delete": deleted_files,
            }

        # Begin transaction to keep both tables consistent.
        with session.begin_nested():

            for source in deleted_files:

                # Delete all vector chunks belonging to the document.
                session.execute(
                    delete(KnowledgeChunk).where(
                        KnowledgeChunk.source == source
                    )
                )

                # Delete the document's ingestion tracking record.
                session.execute(
                    delete(IngestedDocument).where(
                        IngestedDocument.source == source
                    )
                )

        # Commit all deletions together.
        session.commit()

    return {
        "dry_run": False,
        "deleted_count": len(deleted_files),
        "deleted_sources": deleted_files,
    }
