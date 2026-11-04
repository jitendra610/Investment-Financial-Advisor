#from app.agents.state import InvestmentState
'''
def query_agent(state: InvestmentState) -> dict:
    question = state['query'].lower()
    personal = any(term in question for term in ('my ', 'me ', 'i ', 'recommend', 'should i', 'portfolio', 'allocate', 'invest for'))
    return {'intent': 'personal' if personal else 'education'}
'''

from app.prompts.manager import get_prompt
import asyncio
from app.agents.llm import llm
from app.agents.schemas import QueryAnalysis
from app.prompts import load_system_prompt

async def load_system_prompt(agent_name: str):
    prompt = await asyncio.to_thread(
        get_prompt,
        agent_name,
    )
    return prompt

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
