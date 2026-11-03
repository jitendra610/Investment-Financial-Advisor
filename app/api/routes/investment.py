import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_user,
    require_customer_access,
)
from app.auth.database import get_auth_session
from app.models.api_user import APIUser
from app.schemas.investment_api import (
    InvestmentAnalysisRequest,
    InvestmentAnalysisResponse,
)
from app.workflows.investment_graph import investment_graph


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/investment",
    tags=["Investment Analysis"],
)


@router.post(
    "/analyze",
    response_model=InvestmentAnalysisResponse,
)
async def analyze_investment(
    request: InvestmentAnalysisRequest,
    user: APIUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_auth_session),
):
    # Authorization must happen before invoking any agent.
    await require_customer_access(
        request.customer_id,
        user,
        session,
    )

    try:
        result = await investment_graph.ainvoke(
            {
                "customer_id": request.customer_id,
                "query": request.query,
            },
            config={
                "run_name": "investment-analysis-api",
                "tags": ["fastapi", "investment-advisor"],
                "metadata": {
                    "environment": "development",
                },
            },
        )

    except Exception:
        logger.exception("Investment workflow failed")
        raise HTTPException(
            status_code=500,
            detail="Investment analysis could not be completed",
        )

    compliance = result.get("compliance") or {}

    if compliance.get("human_review_required", True):
        # Fail closed if the graph returns an inconsistent status.
        status_value = "needs_review"
        response_text = (
            "This request requires review by an appropriately "
            "qualified adviser or compliance reviewer before "
            "personalized investment guidance can be provided."
        )
    else:
        status_value = result.get("status", "needs_review")
        response_text = result.get("response")

    return InvestmentAnalysisResponse(
        customer_id=request.customer_id,
        status=status_value,
        response=response_text,
        compliance=compliance,
    )