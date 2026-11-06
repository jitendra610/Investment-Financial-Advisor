'''
def knowledge_agent(state: InvestmentState) -> dict:
    candidates = hybrid_search(state['query'], top_k=8)
    selected = rerank(state['query'], candidates, top_n=3)
    return {'knowledge': {'chunks': [{'source': x['source'], 'content': x['content']} for x in selected],
                          'sources': sorted({x['source'] for x in selected})}}
'''

# Import hybrid search function from the RAG retrieval module.
from app.rag.retrieval import hybrid_search

#from app.rag.reranker import rerank
from app.agents.state import InvestmentState
import asyncio


async def knowledge_agent(state):
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