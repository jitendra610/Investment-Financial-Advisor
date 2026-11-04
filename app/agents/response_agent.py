import os
from langchain_openai import ChatOpenAI
from app.agents.state import InvestmentState
from app.prompts import load_system_prompt

'''

def response_agent(state: InvestmentState) -> dict:
    excerpts = '\n\n'.join(f"[{x['source']}] {x['content']}" for x in state['knowledge']['chunks'])
    if not excerpts:
        return {'response': 'Insufficient verified knowledge to answer. Please consult a qualified adviser.', 'status': 'needs_review'}
    llm = ChatOpenAI(model=os.getenv('OPENAI_CHAT_MODEL', 'gpt-4o-mini'), temperature=0)
    prompt = load_system_prompt("response")
    answer = llm.invoke([
        ('system', prompt.content),
        ('human', f"Question: {state['query']}\n\nEvidence:\n{excerpts}\n\n"
         'Explain general principles and uncertainties. Do not personalize your answer.')
    ])
    return {'response': str(answer.content), 'status': 'education_only'}

def review_response(state: InvestmentState) -> dict:
    reasons = '; '.join(state['compliance']['reasons'])
    return {'response': 'Human review required. No personalized recommendation generated. Reasons: ' + reasons,
            'status': 'needs_review'}

'''
from app.prompts.manager import get_prompt
from app.prompts.manager import get_prompt
import asyncio
import json
from app.agents.llm import llm
from app.prompts import load_system_prompt

async def load_system_prompt(agent_name: str):
    prompt = await asyncio.to_thread(
        get_prompt,
        agent_name,
    )
    return prompt

def as_json(value):
    return json.dumps(value, default=str)

async def response_agent(state):
    prompt = await load_system_prompt("response")
    result = await llm.ainvoke([
        (
            "system",
            prompt.content
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
        "response_prompt_version": prompt.version
    }
