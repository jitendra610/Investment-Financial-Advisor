"""
Investment Analysis API Router

Supports:
1. JWT authentication.
2. Customer-level authorization.
3. Dynamic LangGraph routing.
4. General and educational questions.
5. Customer-specific financial analysis.
6. Clarification requests.
7. Mandatory compliance checks for regulated advice.
8. Secure error handling.
"""

from app.guardrails.input_guardrail import check_input
from app.guardrails.output_guardrail import (
    check_output,
    REVIEW_MESSAGE,
)

from app.guardrails.pii_masker import mask_pii

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
from app.workflows.investment_graph1 import investment_graph


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


    logger.info("Investment API request received")
    # --------------------------------------------------
    # STEP 1: CUSTOMER AUTHORIZATION
    # --------------------------------------------------

    # Verify authenticated user is authorized to access
    # the requested customer_id.
    #
    # Authorization must happen before executing any agent.
    # Unauthorized requests should raise an HTTP exception.
    if request.customer_id is not None:
        await require_customer_access(
            request.customer_id,
            user,
            session,
        )

        logger.info(
            "Customer authorization successful"
        )

    # --------------------------------------------
    # STEP 2: INPUT GUARDRAIL
    # --------------------------------------------

    # Validate the user's query before executing
    # the LangGraph multi-agent workflow.
    input_result = check_input(request.query)

    # Reject requests that fail input validation.
    if not input_result.allowed:

        logger.warning(
            "Input guardrail blocked request | violations=%s",
            input_result.violations,
        )

        raise HTTPException(
            status_code=400,
            detail=input_result.reason,
        )

    logger.info("Input guardrail validation passed")
    # Mask PII before passing text to LangGraph.
    pii_result = mask_pii(request.query)

    safe_query = pii_result["masked_text"]

    logger.info(
        "PII masking completed | entities=%d",
        len(pii_result["entities"]),
    )

    

    # --------------------------------------------
    # STEP 3: EXECUTE LANGGRAPH WORKFLOW
    # --------------------------------------------

    try:

        result = await investment_graph.ainvoke(
            {
                "query": safe_query,
                "customer_id": request.customer_id,
            },
            config={
                "run_name": "investment-analysis-api",
                "tags": [
                    "fastapi",
                    "investment-advisor",
                ],
                "metadata": {
                    "environment": "development",
                },
            },
        )

    except Exception:

        logger.exception(
            "Investment workflow execution failed"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Investment analysis could not "
                "be completed"
            ),
        )

    # --------------------------------------------
    # STEP 4: EXTRACT WORKFLOW RESULT
    # --------------------------------------------

    status_value = result.get("status")
    response_text = result.get("response")
    compliance = result.get("compliance") or {}

    requires_compliance = result.get(
        "requires_compliance",
        False,
    )

    logger.info(
        "Workflow completed | status=%s | compliance_required=%s",
        status_value,
        requires_compliance,
    )

    # --------------------------------------------
    # STEP 5: HANDLE CLARIFICATION
    # --------------------------------------------

    if result.get("requires_clarification"):

        questions = result.get(
            "clarification_questions",
            [],
        )

        status_value = "needs_clarification"

        response_text = (
            "\n".join(questions)
            or "Please provide additional information."
        )

        logger.info(
            "Clarification required | questions=%d",
            len(questions),
        )

    # --------------------------------------------
    # STEP 6: HANDLE COMPLIANCE
    # --------------------------------------------
    elif requires_compliance:

        # Compliance approval must be explicit.
        compliance_approved = (
            bool(compliance)
            and compliance.get("compliant") is True
            and compliance.get("human_review_required") is False
            )

        # Return the generated response only when:
        # 1. Compliance explicitly approves it.
        # 2. The workflow status is completed.
        if not compliance_approved or status_value != "completed":

            status_value = "needs_review"
            response_text = REVIEW_MESSAGE

            logger.warning(
                "Investment response held for review"
            )

        else:
            logger.info(
                "Investment response passed compliance checks"
            )

            """
            elif requires_compliance:

                # Compliance is mandatory for this request.
                # Missing or incomplete compliance results
                # must not permit personalized guidance.

                if (not compliance or compliance.get(
                        "human_review_required"
                    ) is not False
                    or compliance.get("compliant") is not True
                ):

                    status_value = "needs_review"

                    response_text = (
                        "This request requires review by "
                        "an appropriately qualified adviser "
                        "before personalized investment "
                        "guidance can be provided."
                    )

                    logger.warning(
                        "Investment response held for review"
                    )
                elif status_value != "completed":
                    status_value = "needs_review"
                
                    response_text = REVIEW_MESSAGE

                
                elif status_value not in {
                    "completed",
                    "needs_review",
                }:

                    # Unexpected workflow status.
                    status_value = "needs_review"
                    response_text = (
                        "The investment analysis requires "
                        "additional review."
                    )
                """
            
            # --------------------------------------------
            # STEP 7: HANDLE NON-ADVISORY RESPONSES
            # --------------------------------------------

    else:
    

        # Do not automatically require compliance
        # for ordinary educational questions.

        if status_value != "completed":

            logger.error(
                "Unexpected workflow status: %s",
                status_value,
            )

            raise HTTPException(
                status_code=500,
                detail="Workflow returned an invalid status",
            )

        if not response_text:

            raise HTTPException(
                status_code=500,
                detail="Workflow returned an empty response",
            )

    # --------------------------------------------
    # STEP 8: OUTPUT GUARDRAIL
    # --------------------------------------------

    output_result = check_output(
        response=response_text,
        requires_compliance=requires_compliance,
        compliance=compliance,
        status=status_value,
    )

    logger.info(
        "Output guardrail | action=%s | violations=%s",
        output_result.action,
        output_result.violations,
    )

    # CASE 1: Human review is required.
    if output_result.action == "review":

        status_value = "needs_review"

        # Never return the original generated
        # investment recommendation.
        response_text = REVIEW_MESSAGE

        logger.warning(
            "Output guardrail held response for review"
        )

    # CASE 2: Output contains sensitive information
    # or fails validation.
    elif not output_result.allowed:

        logger.error(
            "Output guardrail blocked response | violations=%s",
            output_result.violations,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "The generated response failed "
                "output validation."
            ),
        )

    # CASE 3: Output is safe.
    else:

        logger.info(
            "Output guardrail validation passed"
        )

    pii_result = mask_pii(response_text)

    response_text = pii_result["masked_text"]

    # --------------------------------------------
    # STEP 9: RETURN STRUCTURED RESPONSE
    # --------------------------------------------

    return InvestmentAnalysisResponse(
        customer_id=request.customer_id,
        status=status_value,
        response=response_text,
        compliance=compliance,
    )
