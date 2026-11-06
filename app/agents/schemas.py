from pydantic import BaseModel, Field
from typing import Literal

"""
class QueryAnalysis(BaseModel):
    intent: str = Field(
        description="education, personal, or unrelated"
    )
    required_information: list[str]
    reasoning: str

"""

class QueryAnalysis(BaseModel):

    # Restrict intent to three valid categories.
    intent: Literal[
        "education",
        "personal",
        "unrelated"
    ] = Field(
        description="Classification of the investment query"
    )

    # Information needed to process the query.
    required_information: list[str] = Field(
        default_factory=list,
        description="Additional information required from the user"
    )

    # Brief explanation of the classification.
    reasoning: str = Field(
        description="Short explanation for the selected intent"
    )

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