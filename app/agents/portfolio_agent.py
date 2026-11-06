"""
Analyze investment allocation and diversification strategies based on the customer's risk profile
and investment goals.
"""


from app.agents.state import InvestmentState

import json
import asyncio
import asyncio
from app.agents.llm import llm
# Import Pydantic schema for structured portfolio analysis.
from app.agents.schemas import PortfolioAnalysis

# Import function to retrieve the active agent system prompt.
from app.prompts.manager import get_prompt

# Load the active system prompt for a given agent.
from app.prompts import load_system_prompt


async def load_system_prompt(agent_name: str):
    # Run synchronous get_prompt() in a separate thread
    # to avoid blocking the asyncio event loop.
    prompt = await asyncio.to_thread(
        get_prompt,
        agent_name,
    )
    return prompt

# Convert Python objects into JSON-formatted strings.
def as_json(value):
    return json.dumps(value, default=str)


# Portfolio Agent responsible for analyzing investment portfolios.
async def portfolio_agent(state):
    model = llm.with_structured_output(PortfolioAnalysis)

    # Retrieve the active Portfolio Agent system prompt.
    prompt = await load_system_prompt("portfolio")

    # Invoke the LLM asynchronously.
    result = await model.ainvoke([
        (       "system", prompt.content),
        (
            "human",
            as_json({
                "portfolio": state["query"],
                "customer": state["customer"],
                "risk": state["risk"],
                "knowledge": state["knowledge"],
            }),
        ),
    ])

    return {"portfolio": result.model_dump(),
            "portfolio_prompt_version": {
                        "portfolio": {
                            "id": prompt.id,
                            "version": prompt.version,
                        }
                    },
            }
