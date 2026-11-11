
"""
Output guardrails for Investment Advisor.

Fail closed for personalized investment guidance
when required compliance evidence is missing.
"""

import logging
import re
from typing import Any

from app.guardrails.schemas import GuardrailResult

logger = logging.getLogger(__name__)

MAX_RESPONSE_LENGTH = 20000

SENSITIVE_OUTPUT_PATTERNS = {
    "email": re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.IGNORECASE,
    ),
    "aadhaar": re.compile(
        r"\b\d{4}[\s-]\d{4}[\s-]\d{4}\b"
    ),
    "pan": re.compile(
        r"\b[A-Z]{5}\d{4}[A-Z]\b"
    ),
    "uk_national_insurance": re.compile(
        r"\b[A-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b",
        re.IGNORECASE,
    ),
}

REVIEW_MESSAGE = (
    "This request requires review by an appropriately "
    "qualified adviser before personalized investment "
    "guidance can be provided."
)


def check_output(
    response: str | None,
    *,
    requires_compliance: bool = False,
    compliance: dict[str, Any] | None = None,
    status: str | None = None,
) -> GuardrailResult:
    """Validate a generated response before returning it."""

    compliance = compliance or {}

    # Preserve clarification as a legitimate workflow outcome.
    if status == "needs_clarification":
        if not response or not response.strip():
            return GuardrailResult(
                allowed=False,
                action="block",
                reason="Clarification response is empty.",
                violations=["empty_response"],
            )

    # Human review must never release generated advice.
    if status == "needs_review":
        return GuardrailResult(
            allowed=False,
            action="review",
            reason=REVIEW_MESSAGE,
            violations=["human_review_required"],
        )

    # Mandatory compliance check for advisory workflows.
    if requires_compliance:
        if (
            not compliance
            or compliance.get("human_review_required") is not False
            or compliance.get("compliant") is not True
        ):
            logger.warning(
                "Output guardrail: compliance approval missing"
            )
            return GuardrailResult(
                allowed=False,
                action="review",
                reason=REVIEW_MESSAGE,
                violations=["compliance_not_approved"],
            )

    if not isinstance(response, str) or not response.strip():
        return GuardrailResult(
            allowed=False,
            action="block",
            reason="The workflow produced an empty response.",
            violations=["empty_response"],
        )

    if len(response) > MAX_RESPONSE_LENGTH:
        return GuardrailResult(
            allowed=False,
            action="block",
            reason="The response exceeds the allowed length.",
            violations=["response_too_long"],
        )

    violations = [
        name
        for name, pattern in SENSITIVE_OUTPUT_PATTERNS.items()
        if pattern.search(response)
    ]

    if violations:
        logger.warning(
            "Output guardrail: possible sensitive-data leakage"
        )
        return GuardrailResult(
            allowed=False,
            action="block",
            reason="The response failed sensitive-data screening.",
            violations=violations,
        )

    return GuardrailResult(
        allowed=True,
        action="allow",
        reason="Output validation passed",
    )
