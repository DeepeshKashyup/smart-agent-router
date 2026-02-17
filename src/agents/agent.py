"""AI agent orchestration with cost tracking."""

import json
from dataclasses import dataclass, field
from typing import Any

from app.core.config import load_yaml_config
from app.core.logging import get_logger
from src.utils.llm_client import LLMClient, LLMResponse
from src.utils.helpers import safe_json_parse

logger = get_logger(__name__)


@dataclass
class RoutingDecision:
    """Result of the complexity classification step."""

    complexity: str  # SIMPLE, MODERATE, COMPLEX
    confidence: float
    reason: str
    routed_to: str  # 'small' or 'large'


class QueryRouter:
    """Routes queries to the appropriate model tier based on complexity.

    Uses a lightweight model to classify query complexity, then routes
    to either a small (cheap) or large (powerful) model accordingly.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.config = load_yaml_config()
        self.threshold = self.config["routing"]["complexity_threshold"]
        self.confidence_threshold = self.config["routing"]["confidence_threshold"]

    async def classify(self, query: str) -> tuple[RoutingDecision, LLMResponse]:
        """Classify query complexity and decide which model to use.

        Returns:
            Tuple of (routing decision, LLM response from router).
        """
        from app.core.config import load_prompts

        prompts = load_prompts()
        system_prompt = prompts["router"]["system"]

        router_response = await self.llm.invoke(
            tier="router",
            prompt=query,
            system_prompt=system_prompt,
        )

        parsed = safe_json_parse(router_response.content)

        if parsed is None:
            # Default to large model on parse failure for safety
            decision = RoutingDecision(
                complexity="COMPLEX",
                confidence=0.5,
                reason="router parse failure - defaulting to large model",
                routed_to="large",
            )
        else:
            complexity = parsed.get("complexity", "COMPLEX")
            confidence = float(parsed.get("confidence", 0.5))

            # Route based on complexity and confidence
            if complexity == "COMPLEX" or confidence < self.confidence_threshold:
                routed_to = "large"
            else:
                routed_to = "small"

            decision = RoutingDecision(
                complexity=complexity,
                confidence=confidence,
                reason=parsed.get("reason", ""),
                routed_to=routed_to,
            )

        logger.info(
            "routing_decision",
            complexity=decision.complexity,
            confidence=decision.confidence,
            routed_to=decision.routed_to,
            reason=decision.reason,
        )

        return decision, router_response


@dataclass
class CostRecord:
    """Single request cost record."""

    model_used: str
    tokens_used: int
    estimated_cost_usd: float
    complexity: str


class CostTracker:
    """Tracks cumulative costs and computes savings vs always using the large model."""

    def __init__(self):
        self._records: list[CostRecord] = []
        self._config = load_yaml_config()

    def record(self, result: dict[str, Any]) -> None:
        """Record a completed request's cost data."""
        self._records.append(
            CostRecord(
                model_used=result["model_used"],
                tokens_used=result["tokens_used"],
                estimated_cost_usd=result["estimated_cost_usd"],
                complexity=result["complexity"],
            )
        )

    def get_summary(self) -> dict[str, Any]:
        """Calculate aggregate cost metrics and savings percentage."""
        if not self._records:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "routed_to_small": 0,
                "routed_to_large": 0,
                "cost_savings_pct": 0.0,
            }

        total_tokens = sum(r.tokens_used for r in self._records)
        actual_cost = sum(r.estimated_cost_usd for r in self._records)
        routed_small = sum(1 for r in self._records if "flash" in r.model_used.lower())
        routed_large = len(self._records) - routed_small

        # Calculate hypothetical cost if all queries used the large model
        large_config = self._config["models"]["large"]
        hypothetical_cost = (total_tokens / 1000) * (
            large_config.get("cost_per_1k_input", 0) + large_config.get("cost_per_1k_output", 0)
        ) / 2  # Average of input/output rates

        savings_pct = 0.0
        if hypothetical_cost > 0:
            savings_pct = round(((hypothetical_cost - actual_cost) / hypothetical_cost) * 100, 1)

        return {
            "total_requests": len(self._records),
            "total_tokens": total_tokens,
            "total_cost_usd": round(actual_cost, 6),
            "routed_to_small": routed_small,
            "routed_to_large": routed_large,
            "cost_savings_pct": max(savings_pct, 0.0),
        }

    def reset(self) -> None:
        """Reset all tracking records."""
        self._records.clear()
