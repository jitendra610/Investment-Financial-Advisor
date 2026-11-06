
import asyncio
import json

from typer.cli import state

# Import all required agents.
from app.agents.query_agent import query_agent
from app.agents.customer_agent import customer_agent
from app.agents.knowledge_agent import knowledge_agent
from app.agents.risk_agent import risk_agent


async def test_risk_agent():

    # Initial LangGraph state.
    state = {
        "query": "Can I invest £10,000 in stocks for five years?",
        "customer_id": "CUST-003"
    }

    # ----------------------------------------
    # STEP 1: Execute Query Agent
    # ----------------------------------------

    print("\n1. Executing Query Agent...")

    query_result = await query_agent(state)

    # Update shared state with query analysis.
    state.update(query_result)

    print(json.dumps(query_result, indent=4, default=str))

    # ----------------------------------------
    # STEP 2: Validate Query Intent
    # ----------------------------------------

    # Extract the actual intent string from nested query analysis.
    intent = state["intent"]["intent"]

    # Stop execution if query is unrelated.
    if intent == "unrelated":

        print("\nQuery is unrelated to investment.")
        print("Skipping Customer, Knowledge and Risk Agents.")

        state["status"] = "skipped_unrelated"
        return state

    # Allow investment-related queries.
    if intent not in ("education", "personal"):
        raise ValueError(f"Unsupported query intent: {intent}")

    print(f"\nQuery intent: {intent}")

    # ----------------------------------------
    # STEP 3: Execute Customer and Knowledge
    # Agents concurrently
    # ----------------------------------------

    print("\n2. Executing Customer and Knowledge Agents...")

    customer_result, knowledge_result = await asyncio.gather(
        customer_agent(state),
        knowledge_agent(state)
    )

    # Merge outputs into shared state.
    state.update(customer_result)
    state.update(knowledge_result)

    print("\nCustomer Agent Result:")
    print(json.dumps(customer_result, indent=4, default=str))

    print("\nKnowledge Agent Result:")
    print(json.dumps(knowledge_result, indent=4, default=str))

    # ----------------------------------------
    # STEP 4: Execute Risk Agent
    # ----------------------------------------

    print("\n3. Executing Risk Agent...")

    risk_result = await risk_agent(state)

    # Update shared state with risk analysis.
    state.update(risk_result)

    print("\nRisk Agent Result:")
    print(json.dumps(risk_result, indent=4, default=str))

    # ----------------------------------------
    # STEP 5: Validate Results
    # ----------------------------------------

    assert "intent" in state
    assert "customer" in state
    assert "knowledge" in state
    assert "risk" in state
    assert isinstance(state["risk"], dict)
    assert len(state["risk"]) > 0

    print("\nAll agents executed successfully!")

    return state


# Execute test.
if __name__ == "__main__":
    asyncio.run(test_risk_agent())
