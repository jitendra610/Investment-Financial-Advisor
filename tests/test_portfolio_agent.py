"""Integration test for the Portfolio Agent and its upstream dependencies.

Run from the project root:
    python -m tests.test_portfolio_agent

Requires configured database, prompts, RAG index, and LLM credentials.
"""

import asyncio
import json

from app.agents.query_agent import query_agent
from app.agents.customer_agent import customer_agent
from app.agents.knowledge_agent import knowledge_agent
from app.agents.risk_agent import risk_agent
from app.agents.portfolio_agent import portfolio_agent


def show(label: str, value: dict) -> None:
    """Print each agent's output in a readable format."""
    print(f"\n{label}")
    print(json.dumps(value, indent=4, default=str))


async def test_portfolio_agent():
    # Use a customer ID that exists in your development database.
    state = {
        "query": "I have £10,000 to invest for five years. What portfolio options should I consider?",
        "customer_id": "CUST-003",
    }

    # Step 1: Classify the customer's question.
    query_result = await query_agent(state)
    state.update(query_result)
    show("1. Query Agent", query_result)

    # Accept both the older nested intent format and the newer flat format.
    intent_data = state["intent"]
    intent = intent_data["intent"] if isinstance(intent_data, dict) else intent_data

    # Do not retrieve personal data or run downstream agents for unrelated queries.
    if intent == "unrelated":
        print("\nUnrelated query: skipping Customer, Knowledge, Risk, and Portfolio Agents.")
        state["status"] = "skipped_unrelated"
        return state

    if intent not in ("personal", "education"):
        raise ValueError(f"Unsupported query intent: {intent}")

    # Step 2: Fetch the customer profile and retrieve RAG evidence concurrently.
    customer_result, knowledge_result = await asyncio.gather(
        customer_agent(state),
        knowledge_agent(state),
    )
    state.update(customer_result)
    state.update(knowledge_result)
    show("2. Customer Agent", customer_result)
    show("3. Knowledge Agent", knowledge_result)

    # Step 3: Assess risk using the customer profile and retrieved knowledge.
    risk_result = await risk_agent(state)
    state.update(risk_result)
    show("4. Risk Agent", risk_result)

    # Step 4: Analyze portfolio options using query, customer, risk, and knowledge.
    portfolio_result = await portfolio_agent(state)
    state.update(portfolio_result)
    show("5. Portfolio Agent", portfolio_result)

    # Validate the final state and prompt-version metadata.
    assert isinstance(state["portfolio"], dict), "Portfolio output must be a dictionary"
    assert state["portfolio"], "Portfolio analysis must not be empty"
    assert "portfolio_prompt_version" in state, "Missing portfolio prompt metadata"
    assert "portfolio" in state["portfolio_prompt_version"], (
        "Expected portfolio prompt metadata under the 'portfolio' key"
    )

    print("\nPortfolio Agent integration test passed!")
    return state


if __name__ == "__main__":
    asyncio.run(test_portfolio_agent())