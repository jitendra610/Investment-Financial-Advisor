from pydantic import BaseModel, Field


class QueryAnalysis(BaseModel):
    intent: str = Field(
        description="education, personal, or unrelated"
    )
    required_information: list[str]
    reasoning: str


class RiskAnalysis(BaseModel):
    risk_level: str
    risk_capacity: str
    key_risks: list[str]
    explanation: str


class PortfolioAnalysis(BaseModel):
    investment_options: list[str]
    diversification_strategy: str
    key_tradeoffs: list[str]
    explanation: str


class ComplianceAnalysis(BaseModel):
    compliant: bool
    human_review_required: bool
    violations: list[str]
    explanation: str