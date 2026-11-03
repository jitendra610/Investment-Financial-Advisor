import pytest


def requires_human_review(risk_tolerance, risk_capacity):
    """Example conservative business rule."""
    risk_levels = {
        "conservative": 1,
        "moderate": 2,
        "aggressive": 3,
    }

    return (
        risk_levels[risk_tolerance]
        > risk_levels[risk_capacity]
    )


@pytest.mark.parametrize(
    "tolerance,capacity,expected",
    [
        ("aggressive", "moderate", True),
        ("aggressive", "conservative", True),
        ("moderate", "moderate", False),
        ("conservative", "aggressive", False),
    ],
)
def test_risk_capacity_rule(tolerance, capacity, expected):
    assert requires_human_review(tolerance, capacity) == expected


def test_no_guaranteed_returns():
    response = (
        "Investment returns are not guaranteed "
        "and capital may be at risk."
    )

    prohibited_phrases = [
        "guaranteed 20% return",
        "risk-free investment",
        "guaranteed profit",
    ]

    assert not any(
        phrase in response.lower()
        for phrase in prohibited_phrases
    )