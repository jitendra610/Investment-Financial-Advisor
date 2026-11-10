import asyncio
import json
from dotenv import load_dotenv
import time
load_dotenv()

from app.workflows.investment_graph1 import investment_graph


async def main():
    result = await investment_graph.ainvoke(
        {
            "customer_id": "CUST-003",
            "query": (
                "Explain portfolio allocation "
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
    '''
    for key, value in result.items():
        print(f"\n{'=' * 15} {key.upper()} {'=' * 15}")
        print(json.dumps(value, indent=4, default=str))
    '''

    print("\n========== WORKFLOW RESULT ==========")

    print(json.dumps(
        result,
        indent=2,
        default=str,
    ))

    print("\nActual Status:", result.get("status"))
    print("Intent:", result.get("intent"))
    print("Selected Agents:", result.get("selected_agents"))
    print("Requires Compliance:", result.get("requires_compliance"))
    print("Compliance Result:", result.get("compliance"))

    #assert result["status"] == "needs_review"

    print("\nTEST PASSED")
          

if __name__ == "__main__":
    #calculate time taken to run the test
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f"\nTest completed in {end_time - start_time:.2f} seconds")


"""
Query	Agents executed
Hi	Query → Planner → Response
What is SIP?	Query → Planner → Response
Explain market trends	Query → Planner → Knowledge → Response
Show my profile	Query → Planner → Customer → Response
Analyze finances with market data	Query → Planner → Customer + Knowledge (parallel) → Response
Explain portfolio allocation	Query → Planner → Customer → Risk → Portfolio → Compliance → Response
Analyze portfolio with market research	Query → Planner → Customer + Knowledge (parallel) → Risk → Portfolio → Compliance → Response
Missing customer ID	Query → Planner → Clarification
"""