from app.agents.state import InvestmentState

'''
def compliance_agent(state: InvestmentState) -> dict:
    reasons = list(state['risk']['reasons'])
    if state['intent'] == 'personal':
        reasons.append('Personalized investment request requires qualified human review')
    if not state['knowledge']['chunks']:
        reasons.append('No supporting knowledge retrieved')
    review = bool(reasons)
    return {'compliance': {'approved_for_education': not review,
                           'human_review_required': review, 'reasons': reasons}}
'''

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

