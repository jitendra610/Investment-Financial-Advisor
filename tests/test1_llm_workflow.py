import asyncio
import json
from dotenv import load_dotenv
import time
load_dotenv()

from app.workflows.investment_graph import investment_graph


async def main():
    result = await investment_graph.ainvoke(
        {
            "customer_id": "CUST-003",
            "query": (
                "hey I want do study on my investmnt can you suggest best portfolio"
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
    #calculate time taken to run the test
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f"\nTest completed in {end_time - start_time:.2f} seconds")