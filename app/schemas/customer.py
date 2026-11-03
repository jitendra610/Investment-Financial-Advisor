
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


RiskLevel = Literal["conservative", "moderate", "aggressive"]


class EmploymentSchema(SchemaBase):
    employment_type: str
    employer_type: str | None = None
    years_experience: int = Field(ge=0)


class FinanceSchema(SchemaBase):
    monthly_income: Decimal = Field(ge=0)
    monthly_expenses: Decimal = Field(ge=0)
    bank_savings: Decimal = Field(ge=0)
    emergency_fund: Decimal = Field(ge=0)
    monthly_debt_payments: Decimal = Field(ge=0)

    @property
    def monthly_surplus(self) -> Decimal:
        return (
            self.monthly_income
            - self.monthly_expenses
            - self.monthly_debt_payments
        )


class LiabilitySchema(SchemaBase):
    liability_type: str
    outstanding_amount: Decimal = Field(ge=0)
    monthly_payment: Decimal = Field(ge=0)


class GoalSchema(SchemaBase):
    goal_type: str
    target_amount: Decimal = Field(gt=0)
    target_date: date
    priority: Literal["low", "medium", "high"]


class InvestmentSchema(SchemaBase):
    asset_class: str
    product_name: str
    current_value: Decimal = Field(ge=0)


class PreferenceSchema(SchemaBase):
    investment_horizon_years: int = Field(ge=0)
    liquidity_need: str
    investment_experience: str
    restrictions: str | None = None


class RiskProfileSchema(SchemaBase):
    risk_tolerance: RiskLevel
    risk_capacity: RiskLevel
    assessed_at: datetime
    is_current: bool


class CustomerProfileSchema(SchemaBase):
    id: str
    full_name: str
    age: int = Field(ge=18, le=120)
    occupation: str | None = None
    marital_status: str | None = None
    dependents: int = Field(ge=0)
    classification: str
    tax_residency: str
    currency: str

    employment: EmploymentSchema | None = None
    finances: FinanceSchema | None = None
    preferences: PreferenceSchema | None = None

    liabilities: list[LiabilitySchema] = Field(default_factory=list)
    goals: list[GoalSchema] = Field(default_factory=list)
    investments: list[InvestmentSchema] = Field(default_factory=list)
    risk_profiles: list[RiskProfileSchema] = Field(default_factory=list)
