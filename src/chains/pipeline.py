"""Smart routing pipeline - core orchestration logic.

Routes queries to lightweight or powerful models based on complexity,
tracking costs to demonstrate the 70% savings.
"""

from typing import Any

from app.core.config import load_prompts
from app.core.logging import get_logger
from src.agents.agent import QueryRouter
from src.guardrails.input_guard import InputGuard
from src.guardrails.output_guard import OutputGuard
from src.utils.llm_client import LLMClient
from src.utils.helpers import timer

logger = get_logger(__name__)


class SmartRouterPipeline:
    """End-to-end pipeline: guard -> route -> invoke -> guard -> respond.

    This is the core component that demonstrates cost-effective agent design.
    Instead of sending every query to an expensive model, it:
    1. Validates input with guardrails
    2. Classifies complexity with a cheap router model (~0.01x cost)
    3. Routes to the appropriate model tier
    4. Validates output with guardrails
    5. Returns the response with full cost metadata
    """

    def __init__(self):
        self.llm = LLMClient()
        self.router = QueryRouter(self.llm)
        self.input_guard = InputGuard()
        self.output_guard = OutputGuard()
        self.prompts = load_prompts()

    async def run(
        self,
        query: str,
        context: str | None = None,
        force_model: str | None = None,
        correlation_id: str = "",
    ) -> dict[str, Any]:
        """Execute the full routing pipeline.

        Args:
            query: The user's question or task.
            context: Optional additional context.
            force_model: Override routing with 'large' or 'small'.
            correlation_id: Request tracing ID.

        Returns:
            Dict with answer, model_used, complexity, cost metadata.
        """
        with timer(f"pipeline_{correlation_id}"):
            # Step 1: Input guardrails
            self.input_guard.validate(query)

            # Step 2: Route the query
            if force_model in ("large", "small"):
                tier = force_model
                complexity = "FORCED"
                confidence = 1.0
                routing_tokens = 0
                routing_cost = 0.0
            else:
                decision, router_response = await self.router.classify(query)
                tier = decision.routed_to
                complexity = decision.complexity
                confidence = decision.confidence
                routing_tokens = router_response.total_tokens
                routing_cost = router_response.estimated_cost_usd

            # Step 3: Build prompt and invoke the selected model
            system_prompt = self.prompts["agent"]["system"]
            full_prompt = query
            if context:
                full_prompt = f"Context:\n{context}\n\nQuestion:\n{query}"

            response = await self.llm.invoke(
                tier=tier,
                prompt=full_prompt,
                system_prompt=system_prompt,
            )

            # Step 4: Output guardrails
            answer = self.output_guard.sanitize(response.content)

            total_tokens = routing_tokens + response.total_tokens
            total_cost = routing_cost + response.estimated_cost_usd

            return {
                "answer": answer,
                "model_used": response.model_name,
                "complexity": complexity,
                "confidence": confidence,
                "tokens_used": total_tokens,
                "estimated_cost_usd": round(total_cost, 6),
            }


if __name__ == "__main__":
    import asyncio

    async def demo():
        """Run a demo showing routing decisions for different query types."""
        pipeline = SmartRouterPipeline()

        test_queries = [
            ("What is Python?", "SIMPLE - should route to small model"),
            ("Summarize the key benefits of microservices", "MODERATE - should route to small model"),
            (
                "Design a distributed caching system that handles 1M QPS with "
                "strong consistency guarantees across 5 regions",
                "COMPLEX - should route to large model",
            ),
        ]

        print("\n" + "=" * 70)
        print("SMART AGENT ROUTER - Cost Optimization Demo")
        print("=" * 70)

        for query, expected in test_queries:
            print(f"\nQuery: {query[:80]}...")
            print(f"Expected: {expected}")
            result = await pipeline.run(query=query, correlation_id="demo")
            print(f"Routed to: {result['model_used']}")
            print(f"Complexity: {result['complexity']} (confidence: {result['confidence']})")
            print(f"Tokens: {result['tokens_used']} | Cost: ${result['estimated_cost_usd']:.6f}")
            print("-" * 40)

    asyncio.run(demo())
