from sqlalchemy import text
from app.rag.database import engine
from app.agents.state import InvestmentState

# Reuse the Lesson 3 SQLAlchemy connection; read only, never modify customer data.
def customer_agent(state: InvestmentState) -> dict:
    with engine.connect() as conn:
        row = conn.execute(text('''
            SELECT c.id, c.full_name, c.age, c.occupation,
                   f.monthly_income, f.monthly_expenses, f.monthly_debt_payments,
                   f.emergency_fund
            FROM customers c
            LEFT JOIN customer_finances f ON f.customer_id = c.id
            WHERE c.id = :customer_id
        '''), {'customer_id': state['customer_id']}).mappings().first()
        if row is None:
            return {'customer': {'found': False}}
        risk = conn.execute(text('''
            SELECT risk_tolerance, risk_capacity
            FROM customer_risk_profiles
            WHERE customer_id = :customer_id AND is_current = true
            ORDER BY assessed_at DESC LIMIT 1
        '''), {'customer_id': state['customer_id']}).mappings().first()
    result = dict(row)
    result['found'] = True
    result['risk_tolerance'] = risk['risk_tolerance'] if risk else None
    result['risk_capacity'] = risk['risk_capacity'] if risk else None
    # Decimal -> float for convenient JSON output; not used for financial accounting.
    for key in ('monthly_income','monthly_expenses','monthly_debt_payments','emergency_fund'):
        result[key] = float(result[key]) if result[key] is not None else None
    return {'customer': result}
