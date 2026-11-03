import asyncio
import json
import time

from app.workflows.investment_graph import investment_graph


TEST_CASES = [
    {
        "id": "AGENT001",
        "customer_id": "CUST-003",
        "query": (
            "I have aggressive risk tolerance but moderate "
            "risk capacity. What should I invest in?"
        ),
        "expected_review": True,
    }
]


async def evaluate_agents():
    results = []

    for case in TEST_CASES:
        start = time.perf_counter()

        output = await investment_graph.ainvoke({
            "customer_id": case["customer_id"],
            "query": case["query"],
        })

        compliance = output.get("compliance", {})

        actual_review = compliance.get(
            "human_review_required"
        )

        passed = (
            actual_review is case["expected_review"]
            and (
                (output.get("status") == "needs_review")
                == case["expected_review"]
            )
        )

        results.append({
            "test_id": case["id"],
            "passed": passed,
            "expected_review": case["expected_review"],
            "actual_review": actual_review,
            "status": output.get("status"),
            "latency_seconds": round(
                time.perf_counter() - start, 2
            ),
        })

    return results


if __name__ == "__main__":
    results = asyncio.run(evaluate_agents())
    print(json.dumps(results, indent=4))