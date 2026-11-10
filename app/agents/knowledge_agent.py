# Import hybrid search function from the RAG retrieval module.
from app.rag.retrieval import hybrid_search

#from app.rag.reranker import rerank
from app.agents.state import InvestmentState
import asyncio
import logging


logger = logging.getLogger(__name__)
async def knowledge_agent(state):
    logger.info("knowledge Agent started")
    try:

        # Execute the synchronous hybrid_search() function
        # in a separate thread to avoid blocking the event loop.
        results = await asyncio.to_thread(
            hybrid_search,
            state["query"],
            top_k=5,
        )

        return {
            "knowledge": {
                "context": "\n\n".join(
                    item["content"] for item in results
                ),
                "sources": [
                    item["source"] for item in results
                ],
            }
        }
    
    except Exception as e:
        logger.error(f"Knowledge Agent failed: {e}")
        raise