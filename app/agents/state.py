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
