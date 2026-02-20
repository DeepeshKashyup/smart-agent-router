"""Custom tools for agent orchestration."""

from typing import Any

from src.retrieval.vectorstore import similarity_search
from app.core.logging import get_logger

logger = get_logger(__name__)


async def search_knowledge_base(query: str, top_k: int = 5) -> dict[str, Any]:
    """Search the vector store and return relevant context.

    Args:
        query: The search query.
        top_k: Number of results to retrieve.

    Returns:
        Dict with search results and metadata.
    """
    results = await similarity_search(query, top_k=top_k)
    return {
        "tool": "search_knowledge_base",
        "query": query,
        "results": results,
        "count": len(results),
    }


def calculate_cost_comparison(
    small_tokens: int,
    large_tokens: int,
    small_cost_per_1k: float = 0.000375,
    large_cost_per_1k: float = 0.00625,
) -> dict[str, Any]:
    """Calculate cost comparison between routing and always-large strategies.

    Args:
        small_tokens: Tokens processed by the small model.
        large_tokens: Tokens processed by the large model.
        small_cost_per_1k: Cost per 1K tokens for the small model.
        large_cost_per_1k: Cost per 1K tokens for the large model.

    Returns:
        Dict with cost breakdown and savings percentage.
    """
    total_tokens = small_tokens + large_tokens
    routed_cost = (small_tokens / 1000 * small_cost_per_1k) + (large_tokens / 1000 * large_cost_per_1k)
    naive_cost = total_tokens / 1000 * large_cost_per_1k
    savings = ((naive_cost - routed_cost) / naive_cost * 100) if naive_cost > 0 else 0

    return {
        "routed_cost_usd": round(routed_cost, 6),
        "naive_cost_usd": round(naive_cost, 6),
        "savings_usd": round(naive_cost - routed_cost, 6),
        "savings_pct": round(savings, 1),
    }
