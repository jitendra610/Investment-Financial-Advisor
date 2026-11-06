import os
import time

from app.rag.retrieval import hybrid_search
from app.evaluation.rag_dataset import RAG_TEST_CASES


def normalize_source(value):
    return os.path.basename(str(value).replace("\\", "/"))


# Evaluate the retrieval performance of the RAG system.
#
# top_k: Maximum number of documents to retrieve per query.
#
# Returns:
# List of dictionaries containing evaluation metrics.

def evaluate_rag(top_k=5):
    scores = []

    for case in RAG_TEST_CASES:
        start = time.perf_counter()

        # Your existing hybrid_search is synchronous.
        documents = hybrid_search(case["query"], top_k=top_k)

        latency = time.perf_counter() - start

        retrieved = [
            normalize_source(doc["source"])
            for doc in documents
        ]

        relevant = {
            normalize_source(source)
            for source in case["relevant_sources"]
        }

        hits = sum(source in relevant for source in retrieved)

        precision = hits / len(retrieved) if retrieved else 0
        recall = len(set(retrieved) & relevant) / len(relevant)

        first_rank = next(
            (
                rank for rank, source in enumerate(retrieved, 1)
                if source in relevant
            ),
            None,
        )

        # Calculate Reciprocal Rank.
        # Measures how early the first relevant result appears.
        reciprocal_rank = 1 / first_rank if first_rank else 0

        scores.append({
            "test_id": case["id"],
            "precision_at_k": round(precision, 3),
            "recall_at_k": round(recall, 3),
            "reciprocal_rank": round(reciprocal_rank, 3),
            "latency_seconds": round(latency, 3),
        })

    return scores


if __name__ == "__main__":
    import json

    results = evaluate_rag()


    # Print evaluation results in formatted JSON.
    # indent=4 improves readability.
    print(json.dumps(results, indent=4))

    for metric in (
        "precision_at_k",
        "recall_at_k",
        "reciprocal_rank",
        "latency_seconds",
    ):
        average = sum(row[metric] for row in results) / len(results)
        print(f"{metric}: {average:.3f}")