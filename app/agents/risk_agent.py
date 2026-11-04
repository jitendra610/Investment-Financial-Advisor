from app.agents.state import InvestmentState

'''def risk_agent(state: InvestmentState) -> dict:
    c = state['customer']
    if not c.get('found'):
        return {'risk': {'review_required': True, 'reasons': ['Customer not found']}}
    reasons = []
    amounts = [c.get(x) for x in ('monthly_income','monthly_expenses','monthly_debt_payments')]
    if any(x is None for x in amounts):
        reasons.append('Missing financial information')
        surplus = None
    else:
        surplus = amounts[0] - amounts[1] - amounts[2]
        if surplus <= 0:
            reasons.append('No positive monthly surplus')
    if not c.get('risk_capacity') or not c.get('risk_tolerance'):
        reasons.append('Missing risk assessment')
    elif c['risk_tolerance'].lower() == 'aggressive' and c['risk_capacity'].lower() != 'aggressive':
        reasons.append('Risk tolerance exceeds assessed capacity')
    if c.get('emergency_fund') is None:
        reasons.append('Emergency fund not assessed')
    return {'risk': {'monthly_surplus': surplus, 'reasons': reasons,
                     'review_required': bool(reasons)}}
'''

from app.prompts.manager import get_prompt
from app.prompts import load_system_prompt
import asyncio
import json
from app.agents.llm import llm
from app.agents.schemas import (
    RiskAnalysis, 
)

async def load_system_prompt(agent_name: str):
    prompt = await asyncio.to_thread(
        get_prompt,
        agent_name,
    )
    return prompt

def as_json(value):
    return json.dumps(value, default=str)

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
