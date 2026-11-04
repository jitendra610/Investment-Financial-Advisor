"""Local cross-encoder reranking; first run downloads a public model."""
from functools import lru_cache

@lru_cache(maxsize=1)
def get_reranker():
    from sentence_transformers import CrossEncoder
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank(query: str, chunks: list[dict], top_n: int = 3) -> list[dict]:
    if not chunks:
        return []
    
    scores = get_reranker().predict([(query, c["content"]) for c in chunks])
    
    ordered = sorted(zip(chunks, scores), key=lambda item: float(item[1]), reverse=True)
    
    return [{**chunk, "rerank_score": float(score)} for chunk, score in ordered[:top_n]]
