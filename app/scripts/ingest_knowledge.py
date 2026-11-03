from app.rag.ingestion import ingest

if __name__ == "__main__":
    count = ingest()
    print(f"Ingested {count} knowledge chunks into rag_knowledge_chunks")
