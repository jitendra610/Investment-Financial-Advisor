"""
Purpose:    The evaluate_rag() function measures how accurately and efficiently the Knowledge Agent 
            retrieves relevant documents from the RAG knowledge base.

Working:    It executes the Knowledge Agent for each test query, compares retrieved document sources 
            with expected relevant sources, and calculates evaluation metrics.

            Metric	Description
Precision@K	Proportion of retrieved documents that are relevant.
Recall@K	Proportion of expected relevant documents successfully retrieved.
F1@K	    Balance between precision and recall.
Hit Rate@K	Checks whether at least one relevant document was retrieved.
MRR	        Measures how early the first relevant document appears in search results.
NDCG@K	    Measures ranking quality, rewarding relevant documents appearing earlier.
Latency	    Time taken by the Knowledge Agent to retrieve documents.
"""

import asyncio
import json
import logging
import math
import os
import statistics
import time

from app.agents.knowledge_agent import knowledge_agent
from app.evaluation.rag_dataset import RAG_TEST_CASES

logger = logging.getLogger(__name__)


def normalize_source(value):
    """Normalize source filenames for comparison."""
    return os.path.basename(
        str(value).replace("\\", "/")
    ).lower()


def extract_sources(knowledge_result):
    """
    Extract ranked source filenames from Knowledge Agent.

    Expected result:
    {
        "knowledge": {
            "context": "...",
            "sources": [...]
        }
    }
    """

    knowledge = knowledge_result.get("knowledge") or {}
    sources = knowledge.get("sources") or []

    retrieved = []

    for source in sources:
        if isinstance(source, str):
            retrieved.append(normalize_source(source))

        elif isinstance(source, dict):
            filename = (
                source.get("source")
                or source.get("filename")
            )
            if filename:
                retrieved.append(normalize_source(filename))

    return retrieved


def calculate_ndcg(retrieved, relevant):
    """Calculate binary-relevance NDCG."""

    dcg = 0.0
    seen = set()

    for rank, source in enumerate(retrieved, start=1):
        if source in relevant and source not in seen:
            dcg += 1 / math.log2(rank + 1)
            seen.add(source)

    ideal_count = min(len(relevant), len(retrieved))

    idcg = sum(
        1 / math.log2(rank + 1)
        for rank in range(1, ideal_count + 1)
    )

    return dcg / idcg if idcg else 0.0


async def evaluate_rag(top_k=5):
    """
    Evaluate retrieval using the actual Knowledge Agent.

    Note:
    top_k is applied to returned sources.
    The Knowledge Agent must also retrieve at least top_k
    results for a genuine Recall@K evaluation.
    """

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    scores = []

    for case in RAG_TEST_CASES:

        query = case["query"]

        # State required by the Knowledge Agent.
        state = {
            "query": query,
            "intent": "education",
            "customer_id": None,
            "query_plan": {
                "intent": "education",
                "is_complete": True,
                "requires_clarification": False,
            },
        }

        start = time.perf_counter()

        # Execute actual Knowledge Agent.
        result = await knowledge_agent(state)

        knowledge = result.get("knowledge") or {}

        print("\nQUESTION:", query)

        print("\nRETRIEVED SOURCES:")
        for source in knowledge.get("sources", []):
            print("-", source)

        print("\nRETRIEVED CONTEXT:")
        print(str(knowledge.get("context", ""))[:3000])

        latency = time.perf_counter() - start

        # Preserve source order while removing duplicates.
        retrieved_chunks = extract_sources(result)[:top_k]

        retrieved = list(dict.fromkeys(retrieved_chunks))

        relevant = {
            normalize_source(source)
            for source in case["relevant_sources"]
        }

        if not relevant:
            raise ValueError(
                f"No relevant sources defined for {case['id']}"
            )

        # Deduplicate filenames, preserving retrieval order.
        unique_retrieved = list(dict.fromkeys(retrieved))

        matched = set(unique_retrieved) & relevant
        hits = len(matched)

        # Document-source-level precision.
        precision = (
            hits / len(unique_retrieved)
            if unique_retrieved else 0.0
        )

        recall = hits / len(relevant)

        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall else 0.0
        )

        hit_rate = 1.0 if hits else 0.0

        first_rank = next(
            (
                rank
                for rank, source in enumerate(
                    retrieved, start=1
                )
                if source in relevant
            ),
            None,
        )

        reciprocal_rank = (
            1 / first_rank if first_rank else 0.0
        )

        ndcg = calculate_ndcg(retrieved, relevant)

        scores.append({
            "test_id": case["id"],
            "query": query,
            "retrieved_sources": retrieved,
            "relevant_sources": sorted(relevant),
            "precision_at_k": round(precision, 3),
            "recall_at_k": round(recall, 3),
            "f1_at_k": round(f1, 3),
            "hit_rate_at_k": round(hit_rate, 3),
            "reciprocal_rank": round(
                reciprocal_rank, 3
            ),
            "ndcg_at_k": round(ndcg, 3),
            "latency_seconds": round(latency, 3),
        })

        logger.info(
            "Knowledge Agent evaluation completed | "
            "test_id=%s | precision=%.3f | recall=%.3f",
            case["id"],
            precision,
            recall,
        )

    return scores


def summarize_results(results):

    if not results:
        raise ValueError("No evaluation results.")

    metrics = [
        "precision_at_k",
        "recall_at_k",
        "f1_at_k",
        "hit_rate_at_k",
        "reciprocal_rank",
        "ndcg_at_k",
        "latency_seconds",
    ]

    summary = {
        metric: round(
            statistics.mean(
                row[metric] for row in results
            ),
            3,
        )
        for metric in metrics
    }

    summary["mrr"] = summary["reciprocal_rank"]

    latencies = sorted(
        row["latency_seconds"]
        for row in results
    )

    index = math.ceil(0.95 * len(latencies)) - 1

    summary["p95_latency_seconds"] = round(
        latencies[index], 3
    )

    return summary


async def main():

    results = await evaluate_rag(top_k=5)

    print("\nKNOWLEDGE AGENT RETRIEVAL RESULTS")
    print(json.dumps(results, indent=4))

    print("\nAVERAGE METRICS")
    print(
        json.dumps(
            summarize_results(results),
            indent=4,
        )
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
