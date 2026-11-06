"""
Check regulatory and business requirements for investment recommendations and guidance.
Portfolio Agent analyzes how different investments could be combined and explains the trade-offs.
"""


from app.agents.state import InvestmentState

from app.prompts.manager import get_prompt
from app.prompts import load_system_prompt
import asyncio
import json
from app.agents.llm import llm
from app.agents.schemas import (
    ComplianceAnalysis,
)

async def load_system_prompt(agent_name: str):
    prompt = await asyncio.to_thread(
        get_prompt,
        agent_name,
    )
    return prompt

def as_json(value):
    return json.dumps(value, default=str)

async def compliance_agent(state):
    model = llm.with_structured_output(ComplianceAnalysis)
    prompt = await load_system_prompt("compliance")
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

    # Deterministic safety controls:
    recorded = state["customer"].get("risk_profile", {})
    tolerance = recorded.get("risk_tolerance")
    capacity = recorded.get("risk_capacity")

    if tolerance == "aggressive" and capacity == "moderate":
        review["human_review_required"] = True
        review["compliant"] = False
        review["violations"].append(
            "Aggressive risk tolerance conflicts with "
            "moderate recorded risk capacity."
        )

    if state["intent"]["intent"] == "personal":
        review["human_review_required"] = True
        review["compliant"] = False
        review["violations"].append(
            "Personalized investment guidance requires "
            "qualified suitability and compliance review."
        )

    if not state["knowledge"].get("sources"):
        review["human_review_required"] = True
        review["compliant"] = False
        review["violations"].append(
            "No retrieved policy evidence available."
        )

    return {"compliance": review}




"""
6. Is a Portfolio Agent always required?
No. It depends on the user's question.
- "What is an ETF?" — Knowledge Agent and Response Agent may be sufficient.
- "What are the risks of stock investing?" — Knowledge Agent and Risk Agent may be useful.
- "Analyze my existing investment portfolio." — Portfolio Agent is important.
- "How should I invest £10,000?" — Portfolio Agent may help develop scenarios, 
but a regulated suitability process is necessary before providing a personal recommendation.
"""
