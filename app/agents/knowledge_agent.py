from app.rag.retrieval import hybrid_search
from app.rag.reranker import rerank
from app.agents.state import InvestmentState
'''
def knowledge_agent(state: InvestmentState) -> dict:
    candidates = hybrid_search(state['query'], top_k=8)
    selected = rerank(state['query'], candidates, top_n=3)
    return {'knowledge': {'chunks': [{'source': x['source'], 'content': x['content']} for x in selected],
                          'sources': sorted({x['source'] for x in selected})}}
'''