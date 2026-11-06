
"""
Customer Repository

Purpose:
1. Retrieve customer information from PostgreSQL.
2. Load customer-related records using relationships.
3. Create new customer records.
4. Check whether a customer exists.
5. Retrieve customer financial and risk profiles.

Uses asynchronous SQLAlchemy database operations.
"""
# Import select to retrieve records from PostgreSQL.
from sqlalchemy import select
# Import AsyncSession for asynchronous database operations.
from sqlalchemy.ext.asyncio import AsyncSession
# Import selectinload to efficiently load related customer records.
from sqlalchemy.orm import selectinload
import asyncio
# Import Customer ORM model representing the customer table.
from app.models.customer import Customer

# Repository class responsible for customer database operations.
class CustomerRepository:
     # Initialize repository with an existing database session.
    def __init__(self, session: AsyncSession):

        self.session = session # Store session for executing database queries.

    # Retrieve customer and related records using customer ID.
    async def get_by_id(
        self,
        customer_id: str,
    ) -> Customer | None:

        # Build SQLAlchemy SELECT query.
        statement = (
            select(Customer)
            .options(
                selectinload(Customer.employment),
                selectinload(Customer.finances),
                selectinload(Customer.preferences),
                selectinload(Customer.liabilities),
                selectinload(Customer.goals),
                selectinload(Customer.investments),
                selectinload(Customer.risk_profiles),
            )
            .where(Customer.id == customer_id) # Filter customer using unique customer ID.
        )

        result = await self.session.execute(statement) # Execute SELECT query asynchronously.

        return result.scalar_one_or_none()

    # Add a new Customer ORM object to the database session.
    async def create(self, customer: Customer) -> Customer:
        self.session.add(customer)
        await self.session.flush()
        return customer

    # Check if a customer exists using customer ID.
    async def exists(self, customer_id: str) -> bool:
        statement = select(Customer.id).where(
            Customer.id == customer_id
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none() is not None

    # Retrieve customer with financial and risk information.
    # Used by Customer Agent in the investment advisory workflow.
    async def get_full_profile(self, customer_id: str):
        stmt = (
            select(Customer)
            .where(Customer.id == customer_id)
            .options(## Load only the relationships required by Customer Agent.
                selectinload(Customer.finances),
                selectinload(Customer.risk_profiles),
            )
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
