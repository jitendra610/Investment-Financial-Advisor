from app.agents.state import InvestmentState

def compliance_agent(state: InvestmentState) -> dict:
    reasons = list(state['risk']['reasons'])
    if state['intent'] == 'personal':
        reasons.append('Personalized investment request requires qualified human review')
    if not state['knowledge']['chunks']:
        reasons.append('No supporting knowledge retrieved')
    review = bool(reasons)
    return {'compliance': {'approved_for_education': not review,
                           'human_review_required': review, 'reasons': reasons}}
