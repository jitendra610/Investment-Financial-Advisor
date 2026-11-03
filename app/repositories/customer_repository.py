
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import asyncio

from app.models.customer import Customer


class CustomerRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
        self,
        customer_id: str,
    ) -> Customer | None:

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
            .where(Customer.id == customer_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def create(self, customer: Customer) -> Customer:
        self.session.add(customer)
        await self.session.flush()
        return customer

    async def exists(self, customer_id: str) -> bool:
        statement = select(Customer.id).where(
            Customer.id == customer_id
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none() is not None

    async def get_full_profile(self, customer_id: str):
        stmt = (
            select(Customer)
            .where(Customer.id == customer_id)
            .options(
                selectinload(Customer.finances),
                selectinload(Customer.risk_profiles),
            )
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
