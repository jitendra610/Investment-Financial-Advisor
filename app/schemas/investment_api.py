from typing import Any, Literal
from pydantic import BaseModel, Field


class InvestmentAnalysisRequest(BaseModel):
    customer_id: str | None = None
    query: str = Field(min_length=1, max_length=4000)


class InvestmentAnalysisResponse(BaseModel):
    customer_id: str
    status: Literal[
        "completed",
        "needs_review",
        "needs_clarification",
    ]
    response: str | None = None
    compliance: dict[str, Any] = Field(
        default_factory=dict
    )