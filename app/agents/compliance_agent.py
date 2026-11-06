"""
Check regulatory and business requirements for investment recommendations and guidance.

"""

# Import shared LangGraph state.
from app.agents.state import InvestmentState
# Import function to retrieve the active compliance system prompt.
from app.prompts.manager import get_prompt
from app.prompts import load_system_prompt
# Import asyncio for asynchronous execution.
import asyncio
import json
# Import configured LLM instance.
from app.agents.llm import llm
from app.agents.schemas import ComplianceAnalysis

# Load the active system prompt for the specified agent.
async def load_system_prompt(agent_name: str):
    # Execute synchronous get_prompt() in a separate thread
    # to avoid blocking the asyncio event loop.
    prompt = await asyncio.to_thread(
        get_prompt,
        agent_name,
    )
    return prompt

# Convert Python objects into JSON-formatted strings.
def as_json(value):
    return json.dumps(value, default=str)


# Compliance Agent checks investment guidance against
# regulatory instructions and business safety requirements.
async def compliance_agent(state):
    model = llm.with_structured_output(ComplianceAnalysis)
    prompt = await load_system_prompt("compliance")

     # Invoke LLM asynchronously using information
    # collected from previous agents.
    result = await model.ainvoke([
        ("system", prompt.content),
        (
            "human",
            as_json({
                "query": state["query"],
                "risk": state["risk"],
                "portfolio": state["portfolio"],
                "knowledge": state["knowledge"],
            }),
        ),
    ])

    review = result.model_dump()


    # --------------------------------------------------
    # DETERMINISTIC SAFETY CONTROLS
    # --------------------------------------------------
    # These checks are implemented using Python conditions,
    # rather than relying entirely on LLM decisions.
    recorded = state["customer"].get("risk_profile", {})
    tolerance = recorded.get("risk_tolerance")
    capacity = recorded.get("risk_capacity")

    # Rule 1: Check conflict between risk tolerance and capacity.
    # Example: Customer accepts aggressive risk,
    # but financial capacity supports only moderate risk.
    if tolerance == "aggressive" and capacity == "moderate":
        review["human_review_required"] = True
        review["compliant"] = False
        review["violations"].append(
            "Aggressive risk tolerance conflicts with "
            "moderate recorded risk capacity."
        )

    # Rule 2: Check whether the customer requests
    # personalized investment guidance.
    if state["intent"]["intent"] == "personal":
        review["human_review_required"] = True
        review["compliant"] = False
        review["violations"].append(
            "Personalized investment guidance requires "
            "qualified suitability and compliance review."
        )

    # Rule 3: Check whether Knowledge Agent retrieved
    # supporting investment or policy documents.
    if not state["knowledge"].get("sources"):
        review["human_review_required"] = True
        review["compliant"] = False
        review["violations"].append(
            "No retrieved policy evidence available."
        )

    return {"compliance": review}  # Return compliance results to LangGraph shared state.





