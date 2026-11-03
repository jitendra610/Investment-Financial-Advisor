from typing import TypedDict, NotRequired, Any


class InvestmentState(TypedDict):
    customer_id: str
    query: str

    intent: NotRequired[dict]
    customer: NotRequired[dict]
    knowledge: NotRequired[dict]
    risk: NotRequired[dict]
    portfolio: NotRequired[dict]
    compliance: NotRequired[dict]

    response: NotRequired[str]
    status: NotRequired[str]

    query_prompt_version: NotRequired[int]
    risk_prompt_version: NotRequired[int]
    portfolio_prompt_version: NotRequired[int]
    compliance_prompt_version: NotRequired[int]
    response_prompt_version: NotRequired[int]
