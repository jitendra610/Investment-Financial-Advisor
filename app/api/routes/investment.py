"""
Investment Analysis API Router

Purpose:
1. Receive investment analysis requests from users.
2. Authenticate users using JWT tokens.
3. Verify whether users can access the requested customer.
4. Execute the LangGraph multi-agent investment workflow.
5. Check compliance and human-review requirements.
6. Return a structured investment analysis response.
7. Handle workflow errors securely.
"""


import logging # Import logging to record application errors.
# Import FastAPI components.
# APIRouter: Defines API endpoints.
# Depends: Injects authentication and database dependencies.
# HTTPException: Returns HTTP errors.
from fastapi import APIRouter, Depends, HTTPException
# Import asynchronous SQLAlchemy session.
from sqlalchemy.ext.asyncio import AsyncSession

# Import authentication and authorization dependencies.
from app.api.dependencies import (
    get_current_user, # Validate JWT token and retrieve authenticated user.
    require_customer_access, # Verify whether user has access to requested customer.
)
# Import authentication database session dependency.
from app.auth.database import get_auth_session

# Import APIUser ORM model.
from app.models.api_user import APIUser
# Import Pydantic request and response schemas.
from app.schemas.investment_api import (
    InvestmentAnalysisRequest,
    InvestmentAnalysisResponse,
)
# Import compiled LangGraph investment analysis workflow.
from app.workflows.investment_graph import investment_graph


logger = logging.getLogger(__name__)

# Create API router for investment-related endpoints.
# All endpoints will start with /investment.
router = APIRouter(
    prefix="/investment",
    tags=["Investment Analysis"],
)

# Define POST /investment/analyze endpoint.
# Response will be validated using InvestmentAnalysisResponse.
@router.post(
    "/analyze",
    response_model=InvestmentAnalysisResponse,
)
async def analyze_investment(
    # Receive and validate investment analysis request.
    # Expected fields include customer_id and query.
    request: InvestmentAnalysisRequest,

    # Authenticate user using JWT Bearer token.
    # Invalid or expired tokens should be rejected.
    user: APIUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_auth_session),
):
    
     # --------------------------------------------------
    # STEP 1: CUSTOMER AUTHORIZATION
    # --------------------------------------------------

    # Verify authenticated user is authorized to access
    # the requested customer_id.
    #
    # Authorization must happen before executing any agent.
    # Unauthorized requests should raise an HTTP exception.
    await require_customer_access(
        request.customer_id,
        user,
        session,
    )
    # --------------------------------------------------
    # STEP 2: EXECUTE MULTI-AGENT WORKFLOW
    # --------------------------------------------------

    try:
        # Invoke the compiled LangGraph workflow asynchronously.
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

    # --------------------------------------------------
    # STEP 3: EXTRACT COMPLIANCE RESULT
    # --------------------------------------------------

    # Retrieve compliance analysis from workflow state.
    # Use empty dictionary if compliance is missing or None.

    compliance = result.get("compliance") or {}

      # --------------------------------------------------
    # STEP 4: CHECK HUMAN REVIEW REQUIREMENT
    # --------------------------------------------------

    # If human_review_required is True, block direct guidance.
    #
    # Default is True when the field is missing.
    # This is a fail-closed approach.

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


    # --------------------------------------------------
    # STEP 5: RETURN STRUCTURED API RESPONSE
    # --------------------------------------------------

    # Convert workflow output into the Pydantic response schema.
    return InvestmentAnalysisResponse(
        customer_id=request.customer_id,
        status=status_value,
        response=response_text,
        compliance=compliance,
    )