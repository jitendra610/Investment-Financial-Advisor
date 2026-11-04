from app.db.database import AsyncSessionLocal
from app.repositories.customer_repository import CustomerRepository
import asyncio


async def customer_agent(state):
    async with AsyncSessionLocal() as session:
        repo = CustomerRepository(session)
        customer = await repo.get_full_profile(
            state["customer_id"]
        )

        if customer is None:
            raise ValueError("Customer not found")

        finance = customer.finances
        risk = next(
            (r for r in customer.risk_profiles if r.is_current),
            None
        )

        return {
            "customer": {
                "customer_id": customer.id,
                "age": customer.age,
                "occupation": customer.occupation,
                "monthly_income": float(finance.monthly_income),
                "monthly_expenses": float(finance.monthly_expenses),
                "monthly_debt_payments": float(
                    finance.monthly_debt_payments
                ),
                "monthly_surplus": float(
                    finance.monthly_income
                    - finance.monthly_expenses
                    - finance.monthly_debt_payments
                ),
                "emergency_fund": float(finance.emergency_fund),
                "risk_profile": {
                    "risk_tolerance": (
                        risk.risk_tolerance if risk else None
                    ),
                    "risk_capacity": (
                        risk.risk_capacity if risk else None
                    ),
                },
            }
        }

from app.rag.retrieval import hybrid_search
async def knowledge_agent(state):
    # Adapt this import to the retriever from Lesson 3.
    # Execute synchronous retrieval in a separate thread
    results = await asyncio.to_thread(
        hybrid_search,
        state["query"],
        top_k=5,
    )

    return {
        "knowledge": {
            "context": "\n\n".join(
                item["content"] for item in results
            ),
            "sources": [
                item["source"] for item in results
            ],
        }
    }