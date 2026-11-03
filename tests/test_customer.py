
import asyncio
from decimal import Decimal

from app.db.database import AsyncSessionLocal, engine
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerProfileSchema


async def test_customer(customer_id: str):
    async with AsyncSessionLocal() as session:
        repository = CustomerRepository(session)

        customer = await repository.get_by_id(customer_id)

        assert customer is not None, (
            f"Customer {customer_id} not found"
        )

        profile = CustomerProfileSchema.model_validate(customer)

        assert profile.id == customer_id
        assert profile.finances is not None
        assert profile.preferences is not None
        assert len(profile.risk_profiles) > 0

        finance = profile.finances

        monthly_surplus = finance.monthly_surplus

        savings_rate = (
            monthly_surplus / finance.monthly_income * 100
            if finance.monthly_income > 0
            else Decimal("0")
        )

        current_risk = next(
            (
                risk for risk in profile.risk_profiles
                if risk.is_current
            ),
            None,
        )

        assert current_risk is not None

        print("\nCUSTOMER FINANCIAL PROFILE")
        print("--------------------------")
        print("Customer ID:", profile.id)
        print("Name:", profile.full_name)
        print("Age:", profile.age)
        print("Occupation:", profile.occupation)

        print("\nFINANCIAL DETAILS")
        print("Monthly Income:", finance.monthly_income)
        print("Monthly Expenses:", finance.monthly_expenses)
        print("Monthly Debt Payments:", finance.monthly_debt_payments)
        print("Monthly Surplus:", monthly_surplus)
        print("Savings Rate:", round(savings_rate, 2), "%")
        print("Emergency Fund:", finance.emergency_fund)

        print("\nRISK PROFILE")
        print("Risk Tolerance:", current_risk.risk_tolerance)
        print("Risk Capacity:", current_risk.risk_capacity)

        print("\nINVESTMENT DETAILS")
        print("Investment Horizon:",
              profile.preferences.investment_horizon_years)
        print("Number of Goals:", len(profile.goals))
        print("Number of Investments:", len(profile.investments))
        print("Number of Liabilities:", len(profile.liabilities))

        print("\nTEST PASSED")


async def main():
    try:
        for customer_id in [
            "CUST-001",
            "CUST-002",
            "CUST-003",
        ]:
            await test_customer(customer_id)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
