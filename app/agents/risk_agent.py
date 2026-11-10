from app.agents.state import InvestmentState
# Import function to retrieve agent-specific system prompts.
from app.prompts.manager import get_prompt
from app.prompts import load_system_prompt
# Import asyncio to execute synchronous functions
# without blocking the asynchronous event loop.
import asyncio
import json
from app.agents.llm import llm

# Import Pydantic schema for structured risk analysis.
# Ensures the LLM response follows the RiskAnalysis model.
from app.agents.schemas import RiskAnalysis

import logging

logger = logging.getLogger(__name__)


# Load the active system prompt for a specific agent.
async def load_system_prompt(agent_name: str):
    prompt = await asyncio.to_thread(
        get_prompt,
        agent_name,
    )
    return prompt

# Convert Python objects into JSON-formatted strings.
def as_json(value):
    return json.dumps(value, default=str)


# Risk Agent responsible for evaluating customer investment risk.
async def risk_agent(state):
    logger.info("Risk Agent started")
    try:
        model = llm.with_structured_output(RiskAnalysis)
        prompt = await load_system_prompt("risk")

        # Invoke the LLM asynchronously.
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
        logger.info("Risk Agent completed")
        # Return the Risk Agent's output to LangGraph state.
        return {
            # Convert Pydantic RiskAnalysis object into dictionary.
            # Stores the structured investment risk assessment.
            "risk": result.model_dump(),
            "risk_prompt_version": {
                "risk": {
                    "id": prompt.id,
                    "version": prompt.version,
                    }
                    },
                }

    except Exception as e:
        logger.error(f"Risk Agent failed: {e}")
        raise