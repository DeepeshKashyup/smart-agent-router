"""Custom evaluation metrics for the routing pipeline."""

from dataclasses import dataclass


@dataclass
class EvalResult:
    """Result of evaluating a single test case."""

    test_id: str
    query: str
    expected_tier: str
    actual_tier: str
    correct_routing: bool
    tokens_used: int
    latency_seconds: float
    estimated_cost_usd: float


def routing_accuracy(results: list[EvalResult]) -> float:
    """Calculate percentage of correctly routed queries."""
    if not results:
        return 0.0
    correct = sum(1 for r in results if r.correct_routing)
    return round(correct / len(results) * 100, 1)


def average_latency(results: list[EvalResult]) -> float:
    """Calculate average latency across all test cases."""
    if not results:
        return 0.0
    return round(sum(r.latency_seconds for r in results) / len(results), 3)


def total_cost(results: list[EvalResult]) -> float:
    """Calculate total cost across all test cases."""
    return round(sum(r.estimated_cost_usd for r in results), 6)


def cost_by_tier(results: list[EvalResult]) -> dict[str, float]:
    """Break down costs by model tier."""
    tiers: dict[str, float] = {}
    for r in results:
        tier = r.actual_tier
        tiers[tier] = tiers.get(tier, 0) + r.estimated_cost_usd
    return {k: round(v, 6) for k, v in tiers.items()}


def estimated_savings(results: list[EvalResult], large_cost_per_token: float = 0.00000625) -> dict[str, float]:
    """Estimate savings compared to routing everything to the large model."""
    total_tokens = sum(r.tokens_used for r in results)
    actual = total_cost(results)
    hypothetical = total_tokens * large_cost_per_token
    savings = hypothetical - actual
    pct = (savings / hypothetical * 100) if hypothetical > 0 else 0

    return {
        "actual_cost_usd": round(actual, 6),
        "hypothetical_cost_usd": round(hypothetical, 6),
        "savings_usd": round(savings, 6),
        "savings_pct": round(pct, 1),
    }
