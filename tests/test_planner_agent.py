
"""
Test dynamic Planner Agent.

No OpenAI or PostgreSQL calls are required.
"""

import asyncio

from app.core.logging_config import setup_logging
from app.agents.planner_agent import planner_agent


async def main():

    # Initialize daily logging.
    setup_logging()

    # Test 1: Portfolio analysis with market research.
    state = {
        "query": "Analyze my portfolio based on market research",
        "customer_id": "CUST-003",
        "query_plan": {
            "intent": "portfolio_analysis",
            "is_complete": True,
            "requires_clarification": False,
            "required_information": [],
            "selected_agents": [
                "customer_agent",
                "knowledge_agent",
                "portfolio_agent",
            ],
        },
    }

    result = await planner_agent(state)

    print("\n========== PLANNER RESULT ==========")

    for step in result["execution_plan"]:
        print(step)

    assert result["requires_clarification"] is False
    assert result["requires_risk"] is True
    assert result["requires_portfolio"] is True
    assert result["requires_compliance"] is True

    # Verify parallel execution is planned.
    first_step = result["execution_plan"][0]

    assert first_step["execution"] == "parallel"

    assert set(first_step["agents"]) == {
        "customer_agent",
        "knowledge_agent",
    }

    print("\nTest 1 passed!")

    # Test 2: General educational query.
    state = {
        "query": "What is SIP?",
        "query_plan": {
            "intent": "education",
            "is_complete": True,
            "requires_clarification": False,
            "required_information": [],
            "selected_agents": ["response_agent"],
        },
    }

    result = await planner_agent(state)

    assert result["selected_agents"] == []
    assert result["requires_portfolio"] is False
    assert result["requires_compliance"] is False
    assert result["execution_plan"][0]["agents"] == [
        "response_agent"
    ]

    print("Test 2 passed!")

    # Test 3: Missing customer ID.
    state = {
        "query": "Show my financial profile",
        "query_plan": {
            "intent": "customer_profile",
            "is_complete": True,
            "requires_clarification": False,
            "required_information": [],
            "selected_agents": ["customer_agent"],
        },
    }

    result = await planner_agent(state)

    assert result["requires_clarification"] is True
    assert result["status"] == "needs_clarification"
    assert result["execution_plan"] == []

    print("Test 3 passed!")

    print("\nAll Planner Agent tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
