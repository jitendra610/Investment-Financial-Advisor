
"""
Response Agent

Purpose:
1. Generate the final answer based on the user query.
2. Support dynamic agent routing.
3. Handle missing optional agent outputs.
4. Use available customer, knowledge, risk, and portfolio data.
5. Respect compliance and human-review decisions.
6. Record execution logs and LangSmith traces.
"""

import asyncio
import json
import logging
import time

from langsmith import traceable

from app.agents.llm import llm
from app.prompts.manager import get_prompt


# Initialize module logger.
logger = logging.getLogger(__name__)


# Load active system prompt from PostgreSQL.
async def load_system_prompt(agent_name: str):
    return await asyncio.to_thread(
        get_prompt,
        agent_name,
    )


@traceable(
    name="response-agent",
    run_type="chain",
)
async def response_agent(state):

    start_time = time.perf_counter()

    logger.info("Response Agent started")

    try:

        # ----------------------------------------
        # STEP 1: GET USER QUERY
        # ----------------------------------------

        query = state["query"]

        # ----------------------------------------
        # STEP 2: GET OPTIONAL AGENT OUTPUTS
        # ----------------------------------------

        # These agents may have been skipped by the Planner.
        customer = state.get("customer")
        knowledge = state.get("knowledge")
        risk = state.get("risk")
        portfolio = state.get("portfolio")
        compliance = state.get("compliance")

        intent = state.get("intent", "general")

        # ----------------------------------------
        # STEP 3: CHECK COMPLIANCE REQUIREMENTS
        # ----------------------------------------

        # Fail closed for requests that require compliance.
        requires_compliance = state.get(
            "requires_compliance",
            False,
        )

        if requires_compliance:

            # Compliance Agent must have executed successfully.
            if not compliance:
                logger.warning(
                    "Response blocked: compliance result missing"
                )

                return {
                    "response": (
                        "The requested financial analysis "
                        "cannot be provided until compliance "
                        "checks have been completed."
                    ),
                    "status": "needs_review",
                }

            # Human review required: do not release advice.
            if (
                compliance.get("human_review_required", True)
                or compliance.get("compliant") is not True
            ):
                logger.warning(
                    "Response requires human review"
                )

                return {
                    "response": (
                        "Your request requires review by "
                        "an appropriately qualified adviser "
                        "before personalized investment "
                        "guidance can be provided."
                    ),
                    "status": "needs_review",
                }

        # ----------------------------------------
        # STEP 4: LOAD RESPONSE AGENT PROMPT
        # ----------------------------------------

        prompt = await load_system_prompt("response")

        logger.info(
            "Response prompt loaded | version=%s",
            prompt.version,
        )

        # ----------------------------------------
        # STEP 5: BUILD AVAILABLE CONTEXT
        # ----------------------------------------

        context = {
            "intent": intent,
        }

        # Include only data that is available.
        if customer is not None:
            context["customer"] = customer

        if knowledge is not None:
            context["knowledge"] = knowledge

        if risk is not None:
            context["risk"] = risk

        if portfolio is not None:
            context["portfolio"] = portfolio

        if compliance is not None:
            context["compliance"] = compliance

        # Convert available context to JSON.
        context_text = json.dumps(
            context,
            default=str,
        )

        logger.info(
            "Response context prepared | sections=%s",
            list(context.keys()),
        )

        # ----------------------------------------
        # STEP 6: EXECUTE LLM
        # ----------------------------------------

        system_prompt = f"""{prompt.content}"""

        human_message = f"""
        User query:{query}

        Available agent outputs:{context_text}
        """

        logger.info("Response LLM execution started")

        result = await llm.ainvoke([
            ("system", system_prompt),
            ("human", human_message),
        ])

        # Extract text from LLM response.
        response_text = result.content

        if not isinstance(response_text, str):
            response_text = str(response_text)

        # ----------------------------------------
        # STEP 7: RETURN FINAL RESPONSE
        # ----------------------------------------

        duration = time.perf_counter() - start_time

        logger.info(
            "Response Agent completed | intent=%s | duration=%.2fs",
            intent,
            duration,
        )

        return {
            "response": response_text,
            "status": "completed",
            "response_prompt_version": {
                "response": {
                    "id": prompt.id,
                    "version": prompt.version,
                }
            },
        }

    except Exception:

        # Record full exception traceback.
        logger.exception("Response Agent failed")
        raise
