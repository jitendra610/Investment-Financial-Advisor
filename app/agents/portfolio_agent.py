from app.agents.state import InvestmentState
'''
def portfolio_agent(state: InvestmentState) -> dict:
    # Educational discussion only. No personal allocation or trade recommendation.
    return {'portfolio': {'topics': ['Cash and liquidity', 'Diversification',
                                    'Equity and bond fund risk', 'Fees and time horizon'],
                          'recommendation': None}}
'''
import json
import asyncio
import asyncio
from app.agents.llm import llm
from app.agents.schemas import (
    PortfolioAnalysis,
)
from app.prompts.manager import get_prompt
from app.prompts import load_system_prompt


async def load_system_prompt(agent_name: str):
    prompt = await asyncio.to_thread(
        get_prompt,
        agent_name,
    )
    return prompt

def as_json(value):
    return json.dumps(value, default=str)

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
                    },
            }
