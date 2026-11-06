
import asyncio
import json

# Import Customer Agent.
from app.agents.customer_agent import customer_agent


async def test_customer_agent():

    # Prepare sample LangGraph state.
    # Replace CUST-003 with an existing customer ID.
    state = {
        "customer_id": "CUST-001"
    }

    # Execute Customer Agent asynchronously.
    result = await customer_agent(state)

    # Print complete Customer Agent response.
    print("\nCustomer Agent Result:")
    print(json.dumps(result, indent=4, default=str))

    # Extract customer information.
    customer = result["customer"]

    # Display customer details.
    print("\nCustomer Details:")
    print("Customer ID:", customer["customer_id"])
    print("Age:", customer["age"])
    print("Occupation:", customer["occupation"])

    # Display financial information.
    print("\nFinancial Information:")
    print("Monthly Income:", customer["monthly_income"])
    print("Monthly Expenses:", customer["monthly_expenses"])
    print("Monthly Debt:", customer["monthly_debt_payments"])
    print("Monthly Surplus:", customer["monthly_surplus"])
    print("Emergency Fund:", customer["emergency_fund"])

    # Display risk profile.
    print("\nRisk Profile:")
    risk = customer["risk_profile"]

    print("Risk Tolerance:", risk["risk_tolerance"])
    print("Risk Capacity:", risk["risk_capacity"])

    # Validate Customer Agent output.
    assert "customer" in result
    assert customer["customer_id"] == state["customer_id"]

    # Verify monthly surplus calculation.
    expected_surplus = (
        customer["monthly_income"]
        - customer["monthly_expenses"]
        - customer["monthly_debt_payments"]
    )

    assert abs(
        customer["monthly_surplus"] - expected_surplus
    ) < 0.01

    print("\nCustomer Agent test passed!")


# Run asynchronous test.
if __name__ == "__main__":
    asyncio.run(test_customer_agent())
