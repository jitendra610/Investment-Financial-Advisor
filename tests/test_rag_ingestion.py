

from app.rag.ingestion import ingest


if __name__ == "__main__":
    total_chunks = ingest("knowledge_base")
    print(f"Successfully ingested {total_chunks} chunks into PostgreSQL.")