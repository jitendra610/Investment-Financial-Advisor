
import asyncio
from datetime import date

from app.db.database import AsyncSessionLocal, engine
from app.models.customer import (
    Customer,
    CustomerEmployment,
    CustomerFinance,
    CustomerGoal,
    CustomerInvestment,
    CustomerLiability,
    CustomerPreference,
    CustomerRiskProfile,
)
from app.repositories.customer_repository import CustomerRepository


CUSTOMERS = [
    {
        "id": "CUST-001",
        "full_name": "Alice Morgan",
        "age": 35,
        "occupation": "Software Engineer",
        "income": "5000.00",
        "expenses": "2500.00",
        "savings": "20000.00",
        "emergency": "10000.00",
        "debt_payment": "500.00",
        "risk": "moderate",
        "capacity": "moderate",
        "horizon": 10,
        "experience": "intermediate",
    },
    {
        "id": "CUST-002",
        "full_name": "Ben Carter",
        "age": 52,
        "occupation": "Teacher",
        "income": "3000.00",
        "expenses": "2200.00",
        "savings": "8000.00",
        "emergency": "6000.00",
        "debt_payment": "300.00",
        "risk": "conservative",
        "capacity": "conservative",
        "horizon": 5,
        "experience": "beginner",
    },
    {
        "id": "CUST-003",
        "full_name": "Charlotte Reed",
        "age": 40,
        "occupation": "Business Owner",
        "income": "12000.00",
        "expenses": "4500.00",
        "savings": "100000.00",
        "emergency": "30000.00",
        "debt_payment": "1000.00",
        "risk": "aggressive",
        "capacity": "moderate",
        "horizon": 15,
        "experience": "advanced",
    },
]


def build_customer(data: dict) -> Customer:
    customer = Customer(
        id=data["id"],
        full_name=data["full_name"],
        age=data["age"],
        occupation=data["occupation"],
        marital_status="married",
        dependents=1,
        classification="retail",
        tax_residency="GB",
        currency="GBP",
    )

    customer.employment = CustomerEmployment(
        employment_type="full_time",
        employer_type="private",
        years_experience=10,
    )

    customer.finances = CustomerFinance(
        monthly_income=data["income"],
        monthly_expenses=data["expenses"],
        bank_savings=data["savings"],
        emergency_fund=data["emergency"],
        monthly_debt_payments=data["debt_payment"],
    )

    customer.preferences = CustomerPreference(
        investment_horizon_years=data["horizon"],
        liquidity_need="medium",
        investment_experience=data["experience"],
        restrictions=None,
    )

    customer.risk_profiles.append(
        CustomerRiskProfile(
            risk_tolerance=data["risk"],
            risk_capacity=data["capacity"],
            is_current=True,
        )
    )

    customer.goals.append(
        CustomerGoal(
            goal_type="retirement",
            target_amount="250000.00",
            target_date=date(2045, 12, 31),
            priority="high",
        )
    )

    customer.investments.append(
        CustomerInvestment(
            asset_class="equity",
            product_name="Fictional Diversified Equity Fund",
            current_value="5000.00",
        )
    )

    customer.liabilities.append(
        CustomerLiability(
            liability_type="personal_loan",
            outstanding_amount="10000.00",
            monthly_payment=data["debt_payment"],
        )
    )

    return customer


async def seed():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            repository = CustomerRepository(session)

            for data in CUSTOMERS:
                if await repository.exists(data["id"]):
                    print(f"Skipping existing: {data['id']}")
                    continue

                customer = build_customer(data)
                await repository.create(customer)

                print(f"Created: {customer.id}")

    print("Customer seeding completed")


async def main():
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
