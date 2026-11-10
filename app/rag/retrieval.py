"""
Hybrid Retrieval System

Purpose:
1. Convert user query into an embedding.
2. Perform semantic search using pgvector.
3. Perform keyword search using PostgreSQL full-text search.
4. Combine search results using Reciprocal Rank Fusion (RRF).
5. Return the top-ranked knowledge chunks.
6. Record execution logs and LangSmith traces.
"""
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session
from langchain_openai import OpenAIEmbeddings
from app.rag.database import engine, KnowledgeChunk
from langsmith import traceable
import logging
import time

# Create logger for this module.
# Logs will be written to your daily file if setup_logging()
# has been initialized by the application or test runner.
logger = logging.getLogger(__name__)

# Capture retrieval execution in LangSmith.
@traceable(
    name="hybrid-retrieval",
    run_type="retriever",
)


def hybrid_search(query: str, top_k: int = 5, fetch_k: int = 12) -> list[dict]:

    # Record start time for performance monitoring.
    start_time = time.perf_counter()

    logger.info("Hybrid Retrieval started")

    try:
        logger.info("Query embedding generation started")

        # Initialize OpenAI embedding model.
        # STEP 1: Convert query text into a numerical vector.

        query_vector = OpenAIEmbeddings(model="text-embedding-3-small").embed_query(query)

        logger.info(
            "Query embedding generated | dimensions=%d",
            len(query_vector),
        )

        # ----------------------------------------
        # STEP 2: PERFORM DATABASE SEARCH
        # ----------------------------------------

        with Session(engine) as session:

            logger.info("Semantic vector search started")
            # STEP 2A: SEMANTIC VECTOR SEARCH
            # Calculate cosine distance between query
            # embedding and stored document embeddings.
            distance = KnowledgeChunk.embedding.cosine_distance(query_vector)

            # Retrieve nearest knowledge chunks.
            semantic = session.execute(
                select(KnowledgeChunk.id, KnowledgeChunk.source, KnowledgeChunk.content)
                .order_by(distance).limit(fetch_k)
            ).all()

            logger.info(
                "Semantic search completed | results=%d",
                len(semantic),
            )

            logger.info("Keyword search started")

            # # STEP 2B: POSTGRESQL KEYWORD SEARCH
            # Convert user query into PostgreSQL tsquery.
            # PostgreSQL built-in keyword ranking, no extra BM25 service needed.
            tsquery = func.plainto_tsquery("english", query)

            # Convert document content into searchable text.
            document = func.to_tsvector("english", KnowledgeChunk.content)

            # Calculate keyword relevance score.
            rank = func.ts_rank_cd(document, tsquery)

            # Retrieve matching documents ordered by relevance.
            lexical = session.execute(
                select(KnowledgeChunk.id, KnowledgeChunk.source, KnowledgeChunk.content)
                .where(document.op("@@")(tsquery))
                .order_by(desc(rank)).limit(fetch_k)
            ).all()

            logger.info(
                "Keyword search completed | results=%d",
                len(lexical),
            )

        # STEP 3: RECIPROCAL RANK FUSION (RRF)
        # Dictionary to combine and deduplicate results.
        fused = {}
        # Process semantic and keyword search results.
        for results in (semantic, lexical):
            # Assign a rank to each retrieved document.
            for position, row in enumerate(results, start=1):
                # Add document if not already present.
                if row.id not in fused:
                    fused[row.id] = {
                        "id": row.id, 
                        "source": row.source,
                        "content": row.content, 
                        "rrf_score": 0.0
                        }
                # Add Reciprocal Rank Fusion score.
                # Higher-ranked documents receive higher scores.
                # Documents found by both searches gain scores
                # from both result lists.
                fused[row.id]["rrf_score"] += 1.0 / (60 + position)

        logger.info(
        "RRF ranking completed | unique_documents=%d",
        len(fused),
        )

        #Step 4: RETURN TOP-K RESULTS

        # Sort documents by descending RRF score.
        # Return only the requested number of documents.

        # Sort documents by descending RRF score.
        # Return only the requested number of documents.
        final_results = sorted(
            fused.values(),
            key=lambda item: item["rrf_score"],
            reverse=True,
        )[:top_k]

        # Calculate total retrieval execution time.
        duration = time.perf_counter() - start_time

        logger.info(
            "Hybrid Retrieval completed | results=%d | duration=%.2fs",
            len(final_results),
            duration,
        )

        return final_results

    except Exception as e:
        # Record full error traceback in daily log file.
        logger.exception("Hybrid Retrieval failed")

        # Re-raise exception so the calling agent
        # can handle the failure appropriately.
        raise
    