import json
import asyncio
import asyncio

from app.prompts.manager import get_prompt


async def load_system_prompt(agent_name: str):
    prompt = await asyncio.to_thread(
        get_prompt,
        agent_name,
    )
    return prompt

from app.agents.llm import llm
from app.agents.schemas import (
    QueryAnalysis,
    RiskAnalysis,
    PortfolioAnalysis,
    ComplianceAnalysis,
)


def as_json(value):
    return json.dumps(value, default=str)


async def query_agent(state):
    prompt = await load_system_prompt("query")

    model = llm.with_structured_output(QueryAnalysis)

    result = await model.ainvoke([
        ("system", prompt.content),
        ("human", state["query"]),
    ])

    return {
        "intent": result.model_dump(),
        "query_prompt_version": {
            "query": {
                "id": prompt.id,
                "version": prompt.version,
            }
        },
    }


async def risk_agent(state):
    model = llm.with_structured_output(RiskAnalysis)
    prompt = await load_system_prompt("risk")
    result = await model.ainvoke([
        ("system", prompt.content),
        ("human",
            as_json({
                "customer": state["customer"],
                "knowledge": state["knowledge"],
                "question": state["query"],
            }),
        ),
    ])

    return {"risk": result.model_dump(),
            "risk_prompt_version": {
                        "query": {
                            "id": prompt.id,
                            "version": prompt.version,
                        }
                    },
            }


async def portfolio_agent(state):
    model = llm.with_structured_output(PortfolioAnalysis)
    prompt = await load_system_prompt("portfolio")
    result = await model.ainvoke([
        (       "system", prompt.content),
        (
            "human",
            as_json({
                "query": state["query"],
                "customer": state["customer"],
                "risk": state["risk"],
                "knowledge": state["knowledge"],
            }),
        ),
    ])

    return {"portfolio": result.model_dump(),
            "portfolio_prompt_version": {
                        "query": {
                            "id": prompt.id,
                            "version": prompt.version,
                        }
                    },}


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


async def response_agent(state):
    prompt = await load_system_prompt("response")
    result = await llm.ainvoke([
        (
            "system",
            prompt.content
        ),
        (
            "human",
            as_json({
                "query": state["query"],
                "knowledge": state["knowledge"],
                "portfolio": state["portfolio"],
                "compliance": state["compliance"],
            }),
        ),
    ])

    return {
        "response": result.content,
        "status": "completed",
        "response_prompt_version": prompt.version
    }


async def human_review_agent(state):
    return {
        "status": "needs_review",
        "response": (
            "This request requires review by an appropriately "
            "qualified adviser or compliance reviewer before "
            "personalized investment guidance can be provided."
        ),
    }