"""Hybrid retrieval: vector search + PostgreSQL full-text search + RRF."""
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session
from langchain_openai import OpenAIEmbeddings
from app.rag.database import engine, KnowledgeChunk


def hybrid_search(query: str, top_k: int = 5, fetch_k: int = 12) -> list[dict]:
    query_vector = OpenAIEmbeddings(model="text-embedding-3-small").embed_query(query)
    with Session(engine) as session:
        distance = KnowledgeChunk.embedding.cosine_distance(query_vector)
        semantic = session.execute(
            select(KnowledgeChunk.id, KnowledgeChunk.source, KnowledgeChunk.content)
            .order_by(distance).limit(fetch_k)
        ).all()

        # PostgreSQL built-in keyword ranking, no extra BM25 service needed.
        tsquery = func.plainto_tsquery("english", query)
        document = func.to_tsvector("english", KnowledgeChunk.content)
        rank = func.ts_rank_cd(document, tsquery)
        lexical = session.execute(
            select(KnowledgeChunk.id, KnowledgeChunk.source, KnowledgeChunk.content)
            .where(document.op("@@")(tsquery))
            .order_by(desc(rank)).limit(fetch_k)
        ).all()

    fused = {}
    for results in (semantic, lexical):
        for position, row in enumerate(results, start=1):
            if row.id not in fused:
                fused[row.id] = {"id": row.id, "source": row.source,
                                 "content": row.content, "rrf_score": 0.0}
            fused[row.id]["rrf_score"] += 1.0 / (60 + position)
    return sorted(fused.values(), key=lambda item: item["rrf_score"], reverse=True)[:top_k]
