"""
Dynamic Planner / Router Agent

Purpose:
1. Validate Query Analyzer output.
2. Select agents based on user intent.
3. Support parallel Customer and Knowledge execution.
4. Enforce Risk, Portfolio and Compliance dependencies.
5. Request clarification when essential data is missing.
6. Generate an explicit execution plan.
7. Log planning decisions.
"""


import logging
import time
from langsmith import traceable

logger = logging.getLogger(__name__)

# Define required context agents for each intent.
# These are trusted application routing rules.
INTENT_AGENTS = {
    "general": [],
    "education": [],
    "market_research": ["knowledge_agent"],
    "customer_profile": ["customer_agent"],
    "financial_analysis": ["customer_agent"],
    "portfolio_analysis": ["customer_agent"],
    "personal_advice": [
        "customer_agent",
        "knowledge_agent",
    ],
    "unrelated": [],
}

# These intents require the Risk Agent.
RISK_INTENTS = {
    "portfolio_analysis",
    "personal_advice",
}

# These intents require the Portfolio Agent.
PORTFOLIO_INTENTS = {
    "portfolio_analysis",
    "personal_advice",
}

# These intents require compliance checks.
COMPLIANCE_INTENTS = {
    "portfolio_analysis",
    "personal_advice",
}


# ----------------------------------------
# 2. BUILD EXECUTION PLAN
# ----------------------------------------

def build_execution_plan(
    context_agents: list[str],
    requires_risk: bool,
    requires_portfolio: bool,
    requires_compliance: bool,
) -> list[dict]:

    """
    Generate ordered execution steps.

    Customer and Knowledge Agents execute in parallel
    when both are required.
    """

    execution_plan = []
    step = 1

    # First stage: collect required context.
    if context_agents:

        execution_plan.append({
            "step": step,
            "agents": context_agents,
            "execution": (
                "parallel"
                if len(context_agents) > 1
                else "sequential"
            ),
        })

        step += 1

    # Risk analysis must finish before portfolio planning.
    if requires_risk:

        execution_plan.append({
            "step": step,
            "agents": ["risk_agent"],
            "execution": "sequential",
        })

        step += 1

    # Portfolio planning uses the risk analysis result.
    if requires_portfolio:

        execution_plan.append({
            "step": step,
            "agents": ["portfolio_agent"],
            "execution": "sequential",
        })

        step += 1

    # Compliance checks occur before final response.
    if requires_compliance:

        execution_plan.append({
            "step": step,
            "agents": ["compliance_agent"],
            "execution": "sequential",
        })

        step += 1

    # Every completed workflow generates a response.
    execution_plan.append({
        "step": step,
        "agents": ["response_agent"],
        "execution": "sequential",
    })

    return execution_plan

"""
async def planner_agent(state):

    plan = state["query_plan"]
    intent = plan["intent"]


    logger.info(
        "Planner started | intent=%s",
        intent,
    )

    # Select permitted context agents.
    selected = INTENT_AGENTS[intent].copy()

    # Portfolio analysis may need knowledge retrieval
    # when the question explicitly asks for market research.
    if intent == "portfolio_analysis":
        proposed = plan.get("selected_agents", [])

        if "knowledge_agent" in proposed:
            selected.append("knowledge_agent")

    # Check for missing customer identifier.
    needs_customer = "customer_agent" in selected

    missing_customer = (
        needs_customer
        and not state.get("customer_id")
    )

    # Determine whether clarification is required.
    needs_clarification = (
        missing_customer
        or plan.get("requires_clarification", False)
        or not plan.get("is_complete", True)
    )

    # Collect clarification questions.
    questions = list(
        plan.get("required_information", [])
    )

    if missing_customer:
        questions.append(
            "Please provide your customer ID."
        )

    if needs_clarification and not questions:
        questions.append(
            "Could you provide more details about your request?"
        )

    # Risk and portfolio dependencies.
    requires_portfolio = intent in {
        "portfolio_analysis",
        "personal_advice",
    }

    requires_risk = requires_portfolio

    # Personal advice requires compliance review.
    requires_compliance = intent in {
        "personal_advice",
        "portfolio_analysis",
    }

    logger.info(
        "Planner completed | agents=%s | clarification=%s",
        selected,
        needs_clarification,
    )

    return {
        "selected_agents": selected,
        "requires_clarification": needs_clarification,
        "clarification_questions": questions,
        "requires_risk": requires_risk,
        "requires_portfolio": requires_portfolio,
        "requires_compliance": requires_compliance,
    }
"""
async def planner_agent(state):

    plan = state["query_plan"]
    intent = plan["intent"]

    logger.info("Planner started | intent=%s", intent)

    # 1. Select permitted agents
    selected = INTENT_AGENTS[intent].copy()

    if intent == "portfolio_analysis":
        proposed = plan.get("selected_agents", [])

        if "knowledge_agent" in proposed:
            selected.append("knowledge_agent")

    selected = list(dict.fromkeys(selected))

    # 2. Customer information availability
    customer_id = state.get("customer_id")

    needs_customer = "customer_agent" in selected
    missing_customer = needs_customer and not customer_id

    # 3. Query Agent clarification questions
    questions = list(
        plan.get("required_information") or []
    )

    # Remove ONLY customer-ID requests already satisfied
    # by the workflow state.
    if customer_id:
        customer_id_phrases = {
            "customer id",
            "customer identifier",
        }

        questions = [
            q for q in questions
            if not any(
                phrase in q.lower()
                for phrase in customer_id_phrases
            )
        ]

    # 4. Add missing customer ID question
    if missing_customer:
        questions.append(
            "Please provide your customer ID."
        )

    # 5. Determine clarification
    # Recalculate from unresolved requirements.
    needs_clarification = bool(questions)

    # Preserve an explicit incomplete decision if the
    # Query Agent has not supplied a specific question.
    if (
        not needs_clarification
        and (
            plan.get("requires_clarification", False)
            or not plan.get("is_complete", True)
        )
        and not customer_id
    ):
        needs_clarification = True
        questions.append(
            "Could you provide more details about your request?"
        )

    # 6. Agent dependencies
    requires_portfolio = intent in {
        "portfolio_analysis",
        "personal_advice",
    }

    requires_risk = requires_portfolio

    requires_compliance = intent in {
        "personal_advice",
        "portfolio_analysis",
    }

    logger.info(
        "Planner completed | agents=%s | clarification=%s",
        selected,
        needs_clarification,
    )

    return {
        "selected_agents": selected,
        "requires_clarification": needs_clarification,
        "clarification_questions": questions,
        "requires_risk": requires_risk,
        "requires_portfolio": requires_portfolio,
        "requires_compliance": requires_compliance,
    }

# ----------------------------------------
# 3. PLANNER AGENT
# ----------------------------------------

@traceable(
    name="dynamic-planner",
    run_type="chain",
)
async def planner_agent(state):

    start_time = time.perf_counter()

    logger.info("Planner Agent started")

    plan = state["query_plan"]
    intent = plan["intent"]

    print("\n========== PLANNER DEBUG ==========")
    print("Customer ID:", state.get("customer_id"))
    print("Customer Access Verified:",
          state.get("customer_access_verified"))
    print("Intent:", intent)
    print("Query Plan:", plan)
    print("Required Information:",
          plan.get("required_information"))
    print("Is Complete:", plan.get("is_complete"))
    print("Requires Clarification:",
          plan.get("requires_clarification"))


    try:

        # Read structured Query Analyzer output.
        query_plan = state["query_plan"]

        intent = query_plan["intent"]

        logger.info(
            "Planner received intent=%s",
            intent,
        )

        # ----------------------------------------
        # STEP 1: VALIDATE INTENT
        # ----------------------------------------

        if intent not in INTENT_AGENTS:
            raise ValueError(
                f"Unsupported query intent: {intent}"
            )

        # ----------------------------------------
        # STEP 2: SELECT CONTEXT AGENTS
        # ----------------------------------------

        # Start with deterministic intent-based routing.
        selected_agents = INTENT_AGENTS[intent].copy()

        # Query Analyzer may request knowledge retrieval
        # for financial or portfolio analysis.
        proposed_agents = query_plan.get(
            "selected_agents", []
        )

        if intent in {
            "financial_analysis",
            "portfolio_analysis",
        }:
            if "knowledge_agent" in proposed_agents:
                selected_agents.append("knowledge_agent")

        # Remove duplicates while preserving order.
        selected_agents = list(
            dict.fromkeys(selected_agents)
        )

        # ----------------------------------------
        # STEP 3: CHECK CLARIFICATION
        # ----------------------------------------

        requires_customer = (
            "customer_agent" in selected_agents
        )

        missing_customer_id = (
            requires_customer
            and not state.get("customer_id")
        )

        requires_clarification = (
            missing_customer_id
            or query_plan.get(
                "requires_clarification", False
            )
            or not query_plan.get("is_complete", True)
        )

        clarification_questions = list(
            query_plan.get("required_information", [])
        )

        if missing_customer_id:
            clarification_questions.append(
                "Please provide your customer ID."
            )

        if requires_clarification:

            if not clarification_questions:
                clarification_questions.append(
                    "Could you provide more details "
                    "about your request?"
                )

            logger.warning(
                "Planner requires clarification | questions=%d",
                len(clarification_questions),
            )

            return {
                "selected_agents": [],
                "requires_clarification": True,
                "clarification_questions": (
                    clarification_questions
                ),
                "requires_risk": False,
                "requires_portfolio": False,
                "requires_compliance": False,
                "execution_plan": [],
                "status": "needs_clarification",
            }

        # ----------------------------------------
        # STEP 4: DETERMINE REQUIRED ANALYSIS
        # ----------------------------------------

        requires_risk = intent in RISK_INTENTS

        requires_portfolio = (
            intent in PORTFOLIO_INTENTS
        )

        requires_compliance = (
            intent in COMPLIANCE_INTENTS
        )

        # ----------------------------------------
        # STEP 5: GENERATE EXECUTION PLAN
        # ----------------------------------------

        execution_plan = build_execution_plan(
            context_agents=selected_agents,
            requires_risk=requires_risk,
            requires_portfolio=requires_portfolio,
            requires_compliance=requires_compliance,
        )

        # ----------------------------------------
        # STEP 6: LOG PLANNER OUTPUT
        # ----------------------------------------

        duration = time.perf_counter() - start_time

        logger.info("QUERY PLAN: %s", query_plan)
        logger.info("INTENT: %s", intent)
        logger.info("CUSTOMER ID: %s", state.get("customer_id"))
        logger.info("SELECTED AGENTS: %s", selected_agents)
        logger.info("MISSING CUSTOMER ID: %s", missing_customer_id)
        logger.info(
            "LLM REQUIRES CLARIFICATION: %s",
            query_plan.get("requires_clarification")
        )
        logger.info(
            "QUERY COMPLETE: %s",
            query_plan.get("is_complete")
        )

        logger.info(
            "Planner completed | duration=%.3fs", duration,
        )

        logger.info(
            "Execution plan: %s",
            execution_plan,
        )

        # ----------------------------------------
        # STEP 7: RETURN STATE UPDATES
        # ----------------------------------------

        return {
            "selected_agents": selected_agents,
            "requires_clarification": False,
            "clarification_questions": [],
            "requires_risk": requires_risk,
            "requires_portfolio": requires_portfolio,
            "requires_compliance": requires_compliance,
            "execution_plan": execution_plan,
            "status": "in_progress",
        }

    except Exception:
        logger.exception("Planner Agent failed")
        raise
