# Import the asynchronous SQLAlchemy session factory.
# Used to create database sessions for PostgreSQL operations.
from app.db.database import AsyncSessionLocal
# Import CustomerRepository.
# Contains database queries related to customer information.
from app.repositories.customer_repository import CustomerRepository
import asyncio

import logging
logger = logging.getLogger(__name__)


# Customer Agent responsible for retrieving customer details,
# financial information, and investment risk profile.
async def customer_agent(state):
    logger.info("Customer Agent started")
    try:

        # Create a new asynchronous database session.
        # The session automatically closes when this block finishes.
        async with AsyncSessionLocal() as session:
            # Create repository object using the database session.
            repo = CustomerRepository(session) #Provides access to customer database operations
            # Retrieve complete customer profile from PostgreSQL.
            # state["customer_id"] contains the customer identifier.
            #
            # Expected customer information:
            # - Personal details
            # - Financial information
            # - Risk profiles
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

            logger.info("Customer Agent completed")
            return {
                "customer": {
                    "customer_id": customer.id,
                    "age": customer.age,
                    "occupation": customer.occupation,
                    "monthly_income": float(finance.monthly_income),
                    "monthly_expenses": float(finance.monthly_expenses),
                    "monthly_debt_payments": float(finance.monthly_debt_payments),

                    "monthly_surplus": float(
                        finance.monthly_income
                        - finance.monthly_expenses
                        - finance.monthly_debt_payments
                    ),

                    # Customer's available emergency savings.
                    "emergency_fund": float(finance.emergency_fund),

                    # Store customer's investment risk information.
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
    except Exception as e:
        logger.error(f"Customer Agent failed: {e}")
        raise