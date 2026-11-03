import asyncio
import json
from app.workflows.investment_graph import investment_graph


async def main():
    result = await investment_graph.ainvoke({
        "customer_id": "CUST-003",
        "query": (
            "I have 10000 euros and aggressive risk tolerance but "
            "moderate risk capacity. What investment "
            "options should I consider?"
        ),
    })

    for key in ["intent", "customer", "knowledge", "risk", "portfolio",
        "compliance", "status", "response",]:
        print(f"\n{'=' * 15} {key.upper()} {'=' * 15}")
        #print(result.get(key))
        print(json.dumps(result.get(key), indent=4, ensure_ascii=False, default=str))

    assert result["status"] == "needs_review"
    assert result["compliance"]["human_review_required"]

    print("\nTEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())