from app.rag.retrieval import hybrid_search
from app.rag.reranker import rerank
from app.rag.agent import answer


def main():
    question = "How should a bank handle aggressive risk tolerance but moderate risk capacity?"
    print("QUESTION:", question)
    hits = hybrid_search(question, top_k=8)
    assert hits, "No retrieved chunks. Run python -m scripts.ingest_knowledge first."
    print("\nHYBRID SEARCH:")
    for hit in hits[:5]:
        print(f"- {hit['source']} (RRF {hit['rrf_score']:.4f})")
    best = rerank(question, hits, top_n=3)
    print("\nRERANKED:")
    for hit in best:
        print(f"- {hit['source']} (score {hit['rerank_score']:.3f})")
    result = answer(question)
    print("\nGROUNDED ANSWER:\n", result["answer"])
    print("\nSOURCES:", ", ".join(result["sources"]))
    assert result["sources"]
    print("\nTEST PASSED")


if __name__ == "__main__":
    main()
