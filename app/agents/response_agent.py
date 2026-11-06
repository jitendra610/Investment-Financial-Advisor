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
# Import function to retrieve an agent-specific system prompt
from app.prompts.manager import get_prompt
import asyncio
import json
from app.agents.llm import llm # Import the configured LLM instance.
from app.prompts import load_system_prompt
import os
from langchain_openai import ChatOpenAI
# Import the LangGraph state schema.
# Defines data shared between different agents.
from app.agents.state import InvestmentState


async def load_system_prompt(agent_name: str):
    prompt = await asyncio.to_thread(
        get_prompt,
        agent_name,
    )
    return prompt

# Helper function to convert Python data into a JSON string.
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
        "response": result.content,  # Store the final LLM-generated response.
        "status": "completed",       # Mark the response generation process as completed.
        "response_prompt_version": prompt.version  # Record the system prompt version used.
    }
