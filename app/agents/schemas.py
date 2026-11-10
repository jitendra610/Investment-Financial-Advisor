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


class QueryPlan(BaseModel):

    # Classification of the user's request.
    intent: Literal[
        "general",
        "education",
        "market_research",
        "customer_profile",
        "financial_analysis",
        "portfolio_analysis",
        "personal_advice",
        "unrelated",
    ]

    # Whether the question contains enough information.
    is_complete: bool = True

    # Whether the user needs to provide more details.
    requires_clarification: bool = False

    # Information needed to answer the question.
    required_information: list[str] = Field(
        default_factory=list
    )

    # Planner's proposed agents.
    selected_agents: list[
        Literal[
            "customer_agent",
            "knowledge_agent",
            "risk_agent",
            "portfolio_agent",
            "compliance_agent",
            "response_agent",
        ]
    ] = Field(default_factory=list)

    # Short explanation of routing decision.
    reasoning: str = ""