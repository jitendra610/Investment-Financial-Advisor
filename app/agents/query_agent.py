from app.agents.state import InvestmentState

def query_agent(state: InvestmentState) -> dict:
    question = state['query'].lower()
    personal = any(term in question for term in ('my ', 'me ', 'i ', 'recommend', 'should i', 'portfolio', 'allocate', 'invest for'))
    return {'intent': 'personal' if personal else 'education'}
