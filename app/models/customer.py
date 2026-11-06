
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    String, Integer, Numeric, Date, DateTime,
    ForeignKey, Boolean, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now():
    return datetime.now(timezone.utc)


class Customer(Base):
    # Database table name.
    __tablename__ = "customers"

    # Primary key column.
    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))
    age: Mapped[int] = mapped_column(Integer)
    occupation: Mapped[str | None] = mapped_column(String(100))
    marital_status: Mapped[str | None] = mapped_column(String(30))
    dependents: Mapped[int] = mapped_column(Integer, default=0)
    classification: Mapped[str] = mapped_column(
        String(30), default="retail"
    )
    tax_residency: Mapped[str] = mapped_column(
        String(2), default="GB"
    )
    currency: Mapped[str] = mapped_column(
        String(3), default="GBP"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    employment: Mapped["CustomerEmployment | None"] = relationship(
        back_populates="customer", uselist=False
    )
    finances: Mapped["CustomerFinance | None"] = relationship(
        back_populates="customer", uselist=False
    )
    preferences: Mapped["CustomerPreference | None"] = relationship(
        back_populates="customer", uselist=False
    )
    liabilities: Mapped[list["CustomerLiability"]] = relationship(
        back_populates="customer"
    )
    goals: Mapped[list["CustomerGoal"]] = relationship(
        back_populates="customer"
    )
    investments: Mapped[list["CustomerInvestment"]] = relationship(
        back_populates="customer"
    )
    risk_profiles: Mapped[list["CustomerRiskProfile"]] = relationship(
        back_populates="customer"
    )

    __table_args__ = (
        CheckConstraint("age >= 18 AND age <= 120"),
        CheckConstraint("dependents >= 0"),
    )


class CustomerEmployment(Base):
    __tablename__ = "customer_employment"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id"), unique=True, index=True
    )
    employment_type: Mapped[str] = mapped_column(String(50))
    employer_type: Mapped[str | None] = mapped_column(String(50))
    years_experience: Mapped[int] = mapped_column(default=0)

    customer: Mapped["Customer"] = relationship(
        back_populates="employment"
    )


class CustomerFinance(Base):
    __tablename__ = "customer_finances"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id"), unique=True, index=True
    )
    monthly_income: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    monthly_expenses: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    bank_savings: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    emergency_fund: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    monthly_debt_payments: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=0
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="finances"
    )

    __table_args__ = (
        CheckConstraint("monthly_income >= 0"),
        CheckConstraint("monthly_expenses >= 0"),
        CheckConstraint("bank_savings >= 0"),
        CheckConstraint("emergency_fund >= 0"),
        CheckConstraint("monthly_debt_payments >= 0"),
    )


class CustomerLiability(Base):
    __tablename__ = "customer_liabilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id"), index=True
    )
    liability_type: Mapped[str] = mapped_column(String(50))
    outstanding_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    monthly_payment: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    customer: Mapped["Customer"] = relationship(
        back_populates="liabilities"
    )

    __table_args__ = (
        CheckConstraint("outstanding_amount >= 0"),
        CheckConstraint("monthly_payment >= 0"),
    )


class CustomerGoal(Base):
    __tablename__ = "customer_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id"), index=True
    )
    goal_type: Mapped[str] = mapped_column(String(50))
    target_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    target_date: Mapped[date] = mapped_column(Date)
    priority: Mapped[str] = mapped_column(
        String(20), default="medium"
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="goals"
    )

    __table_args__ = (
        CheckConstraint("target_amount > 0"),
    )


class CustomerInvestment(Base):
    __tablename__ = "customer_investments"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id"), index=True
    )
    asset_class: Mapped[str] = mapped_column(String(50))
    product_name: Mapped[str] = mapped_column(String(150))
    current_value: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    customer: Mapped["Customer"] = relationship(
        back_populates="investments"
    )

    __table_args__ = (
        CheckConstraint("current_value >= 0"),
    )


class CustomerPreference(Base):
    __tablename__ = "customer_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id"), unique=True, index=True
    )
    investment_horizon_years: Mapped[int] = mapped_column(Integer)
    liquidity_need: Mapped[str] = mapped_column(String(30))
    investment_experience: Mapped[str] = mapped_column(String(30))
    restrictions: Mapped[str | None] = mapped_column(String(500))

    customer: Mapped["Customer"] = relationship(
        back_populates="preferences"
    )

    __table_args__ = (
        CheckConstraint("investment_horizon_years >= 0"),
    )


class CustomerRiskProfile(Base):
    __tablename__ = "customer_risk_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id"), index=True
    )
    risk_tolerance: Mapped[str] = mapped_column(String(30))
    risk_capacity: Mapped[str] = mapped_column(String(30))
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)

    customer: Mapped["Customer"] = relationship(
        back_populates="risk_profiles"
    )
