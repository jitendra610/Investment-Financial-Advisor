
"""
Dynamic Investment Advisor Workflow

Features:
- Query analysis and planning
- Conditional agent execution
- Parallel Customer and Knowledge Agents
- Optional Risk, Portfolio and Compliance Agents
- Clarification handling
- LangSmith tracing and local logging
"""

import logging

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from app.agents.state1 import InvestmentState

from app.agents.query_agent1 import query_agent
from app.agents.planner_agent import planner_agent
from app.agents.customer_agent import customer_agent
from app.agents.knowledge_agent import knowledge_agent
from app.agents.risk_agent import risk_agent
from app.agents.portfolio_agent import portfolio_agent
from app.agents.compliance_agent import compliance_agent
from app.agents.response_agent_1 import response_agent


# Initialize module logger.
logger = logging.getLogger(__name__)


# ----------------------------------------
# 1. CLARIFICATION NODE
# ----------------------------------------

async def clarification_node(state: InvestmentState):

    logger.info("Clarification required")

    questions = state.get(
        "clarification_questions", []
    )

    return {
        "response": "\n".join(questions),
        "status": "needs_clarification",
    }


# ----------------------------------------
# 2. CONTEXT JOIN NODE
# ----------------------------------------

async def context_join(state: InvestmentState):

    # Executed after selected context branches finish.
    logger.info("Context collection completed")

    return {}


# ----------------------------------------
# 3. PLANNER ROUTING
# ----------------------------------------

def route_after_planner(state: InvestmentState):

    # Stop for missing information.
    if state.get("requires_clarification"):
        logger.info("Routing to clarification")
        return "clarification"

    selected = state.get("selected_agents", [])

    logger.info(
        "Planner selected agents: %s",
        selected,
    )

    # No context agents required.
    if not selected:
        logger.info("Routing directly to response")
        return "context_join"

    # Create one branch for each selected context agent.
    branches = []

    if "customer_agent" in selected:
        branches.append(
            Send("customer", state)
        )

    if "knowledge_agent" in selected:
        branches.append(
            Send("knowledge", state)
        )

    # Planner should select only context agents here.
    if not branches:
        return "context_join"

    return branches


# ----------------------------------------
# 4. ROUTE AFTER CONTEXT
# ----------------------------------------

def route_after_context(state: InvestmentState):

    # Risk analysis required.
    if state.get("requires_risk"):
        logger.info("Routing to Risk Agent")
        return "risk"

    # Compliance-only analysis.
    if state.get("requires_compliance"):
        logger.info("Routing to Compliance Agent")
        return "compliance"

    # Otherwise generate response directly.
    logger.info("Routing to Response Agent")
    return "response"


# ----------------------------------------
# 5. ROUTE AFTER RISK
# ----------------------------------------

def route_after_risk(state: InvestmentState):

    if state.get("requires_portfolio"):
        logger.info("Routing to Portfolio Agent")
        return "portfolio"

    if state.get("requires_compliance"):
        return "compliance"

    return "response"


# ----------------------------------------
# 6. ROUTE AFTER PORTFOLIO
# ----------------------------------------

def route_after_portfolio(state: InvestmentState):

    if state.get("requires_compliance"):
        logger.info("Routing to Compliance Agent")
        return "compliance"

    return "response"


# ----------------------------------------
# 7. BUILD LANGGRAPH
# ----------------------------------------

workflow = StateGraph(InvestmentState)

# Register existing agents.
workflow.add_node("query", query_agent)
workflow.add_node("planner", planner_agent)

workflow.add_node("customer", customer_agent)
workflow.add_node("knowledge", knowledge_agent)

# Defer join until other active work has completed.
workflow.add_node(
    "context_join",
    context_join,
    defer=True,
)

workflow.add_node(
    "clarification",
    clarification_node,
)

workflow.add_node("risk", risk_agent)
workflow.add_node("portfolio", portfolio_agent)
workflow.add_node("compliance", compliance_agent)
workflow.add_node("response", response_agent)


# ----------------------------------------
# 8. CONNECT WORKFLOW
# ----------------------------------------

# Start with Query Analyzer.
workflow.add_edge(START, "query")

# Query Analyzer -> Planner.
workflow.add_edge("query", "planner")

# Planner selects required branches.
workflow.add_conditional_edges(
    "planner",
    route_after_planner,
)

# Customer and Knowledge converge at join.
workflow.add_edge("customer", "context_join")
workflow.add_edge("knowledge", "context_join")

# Select downstream analysis.
workflow.add_conditional_edges(
    "context_join",
    route_after_context,
)

# Risk -> Portfolio / Compliance / Response.
workflow.add_conditional_edges(
    "risk",
    route_after_risk,
)

# Portfolio -> Compliance / Response.
workflow.add_conditional_edges(
    "portfolio",
    route_after_portfolio,
)

# Compliance -> Response.
workflow.add_edge("compliance", "response")

# Finish workflow.
workflow.add_edge("clarification", END)
workflow.add_edge("response", END)


# ----------------------------------------
# 9. COMPILE GRAPH
# ----------------------------------------

investment_graph = workflow.compile()

logger.info(
    "Dynamic Investment Advisor graph compiled"
)
