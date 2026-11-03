from langgraph.graph import StateGraph, START, END

from app.agents.state import InvestmentState
from app.agents.data_agents import (
    customer_agent,
    knowledge_agent,
)
from app.agents.llm_agents import (
    query_agent,
    risk_agent,
    portfolio_agent,
    compliance_agent,
    response_agent,
    human_review_agent,
)


def compliance_router(state):
    compliance = state["compliance"]

    if (
        compliance["human_review_required"]
        or not compliance["compliant"]
    ):
        return "human_review"

    return "response"


def build_graph():
    graph = StateGraph(InvestmentState)

    graph.add_node("query", query_agent)
    graph.add_node("customer", customer_agent)
    graph.add_node("knowledge", knowledge_agent)
    graph.add_node("risk", risk_agent)
    graph.add_node("portfolio", portfolio_agent)
    graph.add_node("compliance", compliance_agent)
    graph.add_node("response", response_agent)
    graph.add_node("human_review", human_review_agent)

    graph.add_edge(START, "query")

    # Parallel customer and knowledge retrieval
    graph.add_edge("query", "customer")
    graph.add_edge("query", "knowledge")

    # Risk analysis needs both customer and policy evidence
    graph.add_edge(["customer", "knowledge"], "risk")

    graph.add_edge("risk", "portfolio")
    graph.add_edge("portfolio", "compliance")

    graph.add_conditional_edges(
        "compliance",
        compliance_router,
        {
            "response": "response",
            "human_review": "human_review",
        },
    )

    graph.add_edge("response", END)
    graph.add_edge("human_review", END)

    return graph.compile()


investment_graph = build_graph()