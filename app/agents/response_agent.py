import os
from langchain_openai import ChatOpenAI
from app.agents.state import InvestmentState
from app.prompts import load_system_prompt

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
