
import hashlib
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.database import (
    engine,
    KnowledgeChunk,
    IngestedDocument,
    initialize_database,
)


EMBEDDING_MODEL = "text-embedding-3-small"


# Calculate file hash to detect content changes.
def calculate_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Load a single document.
def load_file(path: Path) -> list[Document]:

    if path.suffix.lower() == ".pdf":
        docs = PyPDFLoader(str(path)).load()

    elif path.suffix.lower() in {".txt", ".md"}:
        docs = [
            Document(
                page_content=path.read_text(encoding="utf-8")
            )
        ]

    else:
        return []

    # Preserve source path for retrieval and updates.
    for doc in docs:
        doc.metadata["source"] = str(path)

    return docs


# Incrementally ingest new or modified documents.
def incremental_ingest(folder: str = "knowledge_base"):

    initialize_database()

    # Use recursive scanning to include subfolders.
    root = Path(folder)
    files = sorted(
        p for p in root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in {".pdf", ".txt", ".md"}
    )

    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name=EMBEDDING_MODEL,
        chunk_size=400,
        chunk_overlap=60,
    )

    embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    stats = {
        "new": 0,
        "updated": 0,
        "skipped": 0,
        "chunks": 0,
    }

    for path in files:

        # Store relative path, avoiding filename collisions.
        source = path.relative_to(root).as_posix()

        # Hash the raw file content.
        new_hash = calculate_hash(path)

        # Check previously ingested document.
        with Session(engine) as session:
            existing = session.get(IngestedDocument, source)

            if existing and existing.file_hash == new_hash:
                stats["skipped"] += 1
                print(f"SKIPPED: {source}")
                continue

            is_update = existing is not None

        # Load and split only new/changed documents.
        docs = load_file(path)

        # Use the same source identifier everywhere.
        for doc in docs:
            doc.metadata["source"] = source

        chunks = [
            d for d in splitter.split_documents(docs)
            if d.page_content.strip()
        ]

        # Generate embeddings outside the DB transaction.
        vectors = (
            embedder.embed_documents(
                [d.page_content for d in chunks]
            )
            if chunks else []
        )

        # Atomically replace this document's chunks and hash.
        with Session(engine) as session:
            with session.begin():

                # Delete old chunks for this document only.
                session.execute(
                    delete(KnowledgeChunk).where(
                        KnowledgeChunk.source == source
                    )
                )

                # Insert new chunks.
                for i, (doc, vector) in enumerate(
                    zip(chunks, vectors)
                ):
                    chunk_id = hashlib.sha256(
                        f"{source}:{i}:{doc.page_content}".encode()
                    ).hexdigest()

                    session.add(
                        KnowledgeChunk(
                            id=chunk_id,
                            source=source,
                            chunk_index=i,
                            content=doc.page_content,
                            embedding=vector,
                        )
                    )

                # Record successfully ingested file version.
                session.merge(
                    IngestedDocument(
                        source=source,
                        file_hash=new_hash,
                    )
                )

        if is_update:
            stats["updated"] += 1
            print(f"UPDATED: {source}")
        else:
            stats["new"] += 1
            print(f"NEW: {source}")

        stats["chunks"] += len(chunks)

    return stats


if __name__ == "__main__":
    print(incremental_ingest())
