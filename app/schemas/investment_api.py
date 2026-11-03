from typing import Any
from pydantic import BaseModel, Field


class InvestmentAnalysisRequest(BaseModel):
    customer_id: str = Field(min_length=1, max_length=50)
    query: str = Field(min_length=5, max_length=4000)


class InvestmentAnalysisResponse(BaseModel):
    customer_id: str
    status: str
    response: str | None = None
    compliance: dict[str, Any] | None = None