"""PDF/MD/TXT -> split -> OpenAI embedding -> PostgreSQL pgvector."""
import hashlib
from pathlib import Path
from sqlalchemy import delete
from sqlalchemy.orm import Session
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.rag.database import engine, KnowledgeChunk, initialize_database

EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensions


def load_documents(folder: str = "knowledge_base") -> list[Document]:
    docs = []
    for path in sorted(Path(folder).glob("*")):
        if path.suffix.lower() == ".pdf":
            for doc in PyPDFLoader(str(path)).load():
                doc.metadata["source"] = path.name
                docs.append(doc)
        elif path.suffix.lower() in {".md", ".txt"}:
            docs.append(Document(page_content=path.read_text(encoding="utf-8"), metadata={"source": path.name}))
    return docs


def ingest(folder: str = "knowledge_base") -> int:
    initialize_database()
    docs = load_documents(folder)
    if not docs:
        raise RuntimeError(f"No PDF, Markdown or text documents found in {folder}")
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=100)
    chunks = [d for d in splitter.split_documents(docs) if d.page_content.strip()]
    
    embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vectors = embedder.embed_documents([d.page_content for d in chunks])
    sources = {d.metadata["source"] for d in chunks}
    # Replace chunks from these source files only; never touch customer tables.
    with Session(engine) as session:
        with session.begin():
            session.execute(delete(KnowledgeChunk).where(KnowledgeChunk.source.in_(sources)))
            for i, (doc, vector) in enumerate(zip(chunks, vectors)):
                source = doc.metadata["source"]
                key = hashlib.sha256(f"{source}:{i}:{doc.page_content}".encode()).hexdigest()
                session.add(KnowledgeChunk(id=key, source=source, chunk_index=i,
                                           content=doc.page_content, embedding=vector))
    return len(chunks)
