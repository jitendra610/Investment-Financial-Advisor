import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

from app.workflows.investment_graph import investment_graph


async def main():
    result = await investment_graph.ainvoke(
        {
            "customer_id": "CUST-003",
            "query": (
                "I have aggressive risk tolerance but "
                "moderate risk capacity. "
                "What investment options should I consider?"
            ),
        },
        config={
            "run_name": "investment-advisor-evaluation",
            "tags": [
                "investment-advisor",
                "evaluation",
            ],
            "metadata": {
                "environment": "development",
                "test_case": "risk_mismatch",
            },
        },
    )

    for key, value in result.items():
        print(f"\n{'=' * 15} {key.upper()} {'=' * 15}")
        print(json.dumps(value, indent=4, default=str))

    assert result["status"] == "needs_review"

    print("\nTEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())