"""
RAG Document Ingestion Pipeline

PDF / Markdown / TXT
         ↓
Document Loading
        ↓
Text Chunking
        ↓
OpenAI Embeddings
        ↓
PostgreSQL + pgvector
"""

import hashlib # Import hashlib to generate unique IDs for document chunks.
from pathlib import Path # Import Path to read files from the knowledge base folder
from sqlalchemy import delete # Import SQLAlchemy delete operation.
from sqlalchemy.orm import Session # Import Session to perform database operations.
# Import PDF loader to extract text from PDF files
from langchain_community.document_loaders import PyPDFLoader
# Import Document class to represent text and metadata.
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
# Import text splitter to divide documents into smaller chunks.
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.database import engine, KnowledgeChunk, initialize_database

# OpenAI embedding model used to convert text into vectors.
# Default output dimension: 1536.
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensions

# Load PDF, Markdown, and TXT documents from a folder.
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

# Main function to ingest documents into PostgreSQL.
def ingest(folder: str = "knowledge_base") -> int:
    # Initialize PostgreSQL database and pgvector extension.
    # Creates the RAG table if it does not exist.
    initialize_database()
    docs = load_documents(folder)

    # Stop ingestion if no supported documents are found.
    if not docs:
        raise RuntimeError(f"No PDF, Markdown or text documents found in {folder}")

    
    # Configure RecursiveCharacterTextSplitter.
    # chunk_size=300: Maximum target chunk length in characters.
    # chunk_overlap=100: Repeat up to 100 characters between chunks
    # to preserve context across chunk boundaries.
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=150)

    # Split loaded documents into smaller text chunks.
    # Remove chunks containing only whitespace.
    chunks = [d for d in splitter.split_documents(docs) if d.page_content.strip()]

    # Initialize OpenAI embedding model.
    embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    # Convert each chunk into a numerical vector.
    # Each vector represents the semantic meaning of its text.
    vectors = embedder.embed_documents([d.page_content for d in chunks])

    # Collect unique source filenames from the chunks.
    sources = {d.metadata["source"] for d in chunks}

    # Open a synchronous PostgreSQL session.
    with Session(engine) as session:
        with session.begin():
            # Delete previously stored chunks from these source files.
            # This prevents duplicate chunks during re-ingestion.
            # Customer and other unrelated tables are not affected.
            session.execute(delete(KnowledgeChunk).where(KnowledgeChunk.source.in_(sources)))

            # Iterate through document chunks and their embeddings.
            for i, (doc, vector) in enumerate(zip(chunks, vectors)):
                # Get original document filename.
                source = doc.metadata["source"]

                # Generate a deterministic SHA-256 chunk ID.
                # ID is based on filename, chunk index, and content.
                key = hashlib.sha256(f"{source}:{i}:{doc.page_content}".encode()).hexdigest()

                # Create a new KnowledgeChunk database record.
                session.add(KnowledgeChunk(
                    id=key,  # Unique identifier for the chunk.
                    source=source, # Original document filename.
                    chunk_index=i,  # Chunk position in this ingestion batch                 
                    content=doc.page_content, # Actual text content.
                    embedding=vector))  # OpenAI embedding vector.
    
    return len(chunks) # Return total number of chunks stored.



"""
Note:
1. The ingestion process is idempotent. Re-ingesting the same documents will replace 
old chunks with new ones, preventing duplicates.
2. The ingestion pipeline supports PDF, Markdown, and TXT files.
3. The OpenAI embedding model used is "text-embedding-3-small" with 1536 dimensions, 
which is suitable for semantic search and retrieval tasks.
4. The PostgreSQL database must have the pgvector extension enabled to store 
vector embeddings.
5.For your portfolio knowledge-base subfolders, use rglob("*") if recursive ingestion is required.
6. Create a recursive text splitter using token counts.
from langchain_text_splitters import TokenTextSplitter

splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    model_name="text-embedding-3-small",
    chunk_size=400,
    chunk_overlap=60,
)

Document deletion: Implement a separate cleanup process if documents removed from the folder 
should also be removed from PostgreSQL.

"""
