
"""
Input guardrails for the Investment Advisor.

Run before LangGraph and before passing the query
to an LLM or retrieval system.

This file performs four checks:
- Reject empty or excessively long queries.
- Reject obvious attempts to override agent instructions.
- Reject queries containing selected sensitive identifiers.
- Allow ordinary financial questions to reach the Query Analyzer.

"""

import logging
import re

from app.guardrails.schemas import GuardrailResult

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 4000

# Deliberately narrow patterns.
# These detect common explicit instruction attacks,
# not every possible prompt-injection technique.
INJECTION_PATTERNS = [
    re.compile(
        r"\bignore (all )?(previous|prior|system|developer)"
        r" (instructions|prompts|rules)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(disable|bypass|skip) (all )?"
        r"(safety|compliance|guardrails|authorization)"
        r"( checks| rules)?\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\breveal (your )?(system|developer) prompt\b",
        re.IGNORECASE,
    ),
]

# Explicitly labeled sensitive identifiers.
# Do not reject every number: investment queries
# frequently contain amounts, percentages and dates.
SENSITIVE_PATTERNS = {
    "aadhaar": re.compile(
        r"\b(?:aadhaar|aadhar)\s*(?:number|no\.?|:)?"
        r"\s*\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        re.IGNORECASE,
    ),
    "pan": re.compile(
        r"\b(?:PAN\s*(?:number|no\.?|:)\s*)"
        r"[A-Z]{5}\d{4}[A-Z]\b",
        re.IGNORECASE,
    ),
    "uk_national_insurance": re.compile(
        r"\b(?:NI|NINO|national insurance)"
        r"\s*(?:number|no\.?|:)?\s*"
        r"[A-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b",
        re.IGNORECASE,
    ),
}

# Customer identifiers such as CUST-003 are allowed.
# They must still be checked by the authorization layer.


def check_input(query: str) -> GuardrailResult:
    """Validate the user's query before workflow execution."""

    if not isinstance(query, str) or not query.strip():
        return GuardrailResult(
            allowed=False,
            action="block",
            reason="Please enter a question.",
            violations=["empty_query"],
        )

    if len(query) > MAX_QUERY_LENGTH:
        return GuardrailResult(
            allowed=False,
            action="block",
            reason="Your question exceeds the maximum length.",
            violations=["query_too_long"],
        )

    for pattern in INJECTION_PATTERNS:
        if pattern.search(query):
            logger.warning("Input guardrail: injection pattern")
            return GuardrailResult(
                allowed=False,
                action="block",
                reason=(
                    "The request contains instructions "
                    "that cannot be processed."
                ),
                violations=["prompt_injection_pattern"],
            )

    detected = [
        name
        for name, pattern in SENSITIVE_PATTERNS.items()
        if pattern.search(query)
    ]

    if detected:
        logger.warning(
            "Input guardrail: sensitive identifier detected"
        )
        return GuardrailResult(
            allowed=False,
            action="block",
            reason=(
                "Please remove sensitive identity numbers "
                "from your question."
            ),
            violations=detected,
        )

    return GuardrailResult(
        allowed=True,
        action="allow",
        reason="Input validation passed",
    )
