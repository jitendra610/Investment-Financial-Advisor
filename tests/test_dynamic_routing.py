import asyncio

from app.agents.planner_agent import planner_agent


async def test_planner():

    state = {
        "query": "Analyze my portfolio using market research",
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

    assert "customer_agent" in result["selected_agents"]
    assert "knowledge_agent" in result["selected_agents"]
    assert result["requires_portfolio"] is True
    assert result["requires_risk"] is True
    assert result["requires_compliance"] is True

    print("Dynamic Planner test passed!")


if __name__ == "__main__":
    asyncio.run(test_planner())