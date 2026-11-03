from app.agents.state import InvestmentState

def risk_agent(state: InvestmentState) -> dict:
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
