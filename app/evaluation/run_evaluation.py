
import asyncio
import json
import re

from dotenv import load_dotenv

load_dotenv()

from app.workflows.investment_graph import investment_graph


def get_contexts(knowledge: dict) -> list[str]:
    """Extract retrieved passages for RAGAS evaluation."""

    if not isinstance(knowledge, dict):
        return []

    # Prefer original retrieved chunks when available.
    chunks = knowledge.get("chunks")
    if isinstance(chunks, list):
        contexts = [
            chunk["content"] if isinstance(chunk, dict)
            else str(chunk)
            for chunk in chunks
        ]
        return [c for c in contexts if c.strip()]

    context = knowledge.get("context", "")

    if not isinstance(context, str):
        return []

    return [
        item.strip()
        for item in re.split(r"\n\s*\n", context)
        if item.strip()
    ]


async def main():

    query = "Explain diversification in investment portfolios."

    print("\n========== STARTING EVALUATION ==========")

    # LangSmith tracing is enabled using environment variables.
    result = await investment_graph.ainvoke(
        {
            "customer_id": "CUST-003",
            "query": query,
        },
        config={
            "run_name": "investment-advisor-ragas-evaluation",
            "tags": [
                "investment-advisor",
                "ragas-evaluation",
            ],
            "metadata": {
                "environment": "development",
                "evaluation_type": "ragas",
            },
        },
    )

    print("\n========== WORKFLOW ==========")
    print("Status:", result.get("status"))

    print("\n========== COMPLIANCE ==========")
    print(json.dumps(
        result.get("compliance", {}),
        indent=4,
        default=str,
    ))

    print("\n========== RETRIEVAL ==========")

    contexts = get_contexts(result.get("knowledge", {}))

    print("Retrieved passages:", len(contexts))

    for i, context in enumerate(contexts, start=1):
        print(f"\nPassage {i}:")
        print(context[:300])

    # Evaluate only substantive approved responses.
    compliance = result.get("compliance") or {}

    review_required = compliance.get(
        "human_review_required", True
    )

    if (
        result.get("status") != "needs_review"
        and review_required is False
    ):

        response = result.get("response", "")

        if contexts and isinstance(response, str) and response.strip():

            # Import only when needed, so a RAGAS dependency
            # error does not prevent LangGraph execution.
            from app.evaluation.ragas_evaluator import evaluate_answer

            scores = await asyncio.to_thread(
                evaluate_answer,
                query,
                contexts,
                response,
            )

            print("\n========== RAGAS SCORES ==========")
            print(json.dumps(
                scores,
                indent=4,
                default=str,
            ))

        else:
            print("\nRAGAS skipped: missing context or response.")

    else:
        print(
            "\nRAGAS final-answer evaluation skipped: "
            "human review required."
        )

    print("\n========== FINAL RESPONSE ==========")
    print(result.get("response", ""))

    print("\nEvaluation workflow completed.")


if __name__ == "__main__":
    asyncio.run(main())
