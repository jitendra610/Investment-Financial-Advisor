import json

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
    model = llm.with_structured_output(QueryAnalysis)

    result = await model.ainvoke([
        (
            "system",
            "You classify UK investment queries. "
            "Return education, personal, or unrelated. "
            "Identify the information required."
        ),
        ("human", state["query"]),
    ])

    return {"intent": result.model_dump()}


async def risk_agent(state):
    model = llm.with_structured_output(RiskAnalysis)

    result = await model.ainvoke([
        (
            "system",
            "You are a UK bank investment risk analyst. "
            "Interpret the supplied financial profile and "
            "retrieved policy evidence. Distinguish risk "
            "tolerance from risk capacity. Do not invent facts "
            "or override recorded assessments. "
            "Do not give investment recommendations. "
            "Identify missing information."
        ),
        (
            "human",
            as_json({
                "customer": state["customer"],
                "knowledge": state["knowledge"],
                "question": state["query"],
            }),
        ),
    ])

    return {"risk": result.model_dump()}


async def portfolio_agent(state):
    model = llm.with_structured_output(PortfolioAnalysis)

    result = await model.ainvoke([
        (
            "system",
            "You explain UK investment options for educational "
            "purposes only. Discuss diversification, liquidity, "
            "risk, time horizon and trade-offs. "
            "Do not prescribe allocations, specific purchases "
            "or guaranteed returns. Use retrieved evidence "
            "and identify missing information."
        ),
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

    return {"portfolio": result.model_dump()}


async def compliance_agent(state):
    model = llm.with_structured_output(ComplianceAnalysis)

    result = await model.ainvoke([
        (
            "system",
            "You review UK investment guidance for potential "
            "compliance concerns. Identify unsupported claims, "
            "personalized recommendations, missing suitability "
            "information, and conflicts with supplied policies. "
            "Do not claim that fictional policy documents are "
            "verified FCA rules. When uncertain, require review."
        ),
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
    result = await llm.ainvoke([
        (
            "system",
            "You are a UK investment education assistant. "
            "Give a clear, concise, evidence-grounded explanation. "
            "Use only supplied evidence for policy claims. "
            "Do not provide personalized investment instructions, "
            "specific allocations, or guaranteed returns. "
            "Mention uncertainty and relevant sources."
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