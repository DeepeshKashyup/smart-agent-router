"""Evaluation runner for the smart routing pipeline.

Loads test cases, runs each through the pipeline, and prints
a summary table with accuracy, latency, and cost metrics.
"""

import asyncio
import json
import time
from pathlib import Path

from src.chains.pipeline import SmartRouterPipeline
from eval.metrics import EvalResult, routing_accuracy, average_latency, total_cost, cost_by_tier, estimated_savings


async def run_evaluation() -> None:
    """Run the full evaluation suite against test cases."""
    # Load test cases
    test_cases_path = Path(__file__).parent / "test_cases.json"
    with open(test_cases_path) as f:
        test_cases = json.load(f)

    pipeline = SmartRouterPipeline()
    results: list[EvalResult] = []

    print("\n" + "=" * 80)
    print("SMART AGENT ROUTER - Evaluation Suite")
    print("=" * 80)
    print(f"\nRunning {len(test_cases)} test cases...\n")

    for i, tc in enumerate(test_cases, 1):
        query = tc["query"]
        expected_tier = tc["expected_model_tier"]

        print(f"[{i}/{len(test_cases)}] {tc['id']}: {query[:60]}...")

        start = time.perf_counter()
        try:
            result = await pipeline.run(query=query, correlation_id=f"eval_{tc['id']}")
            latency = time.perf_counter() - start

            actual_tier = "small" if "flash" in result["model_used"].lower() else "large"
            correct = actual_tier == expected_tier

            eval_result = EvalResult(
                test_id=tc["id"],
                query=query,
                expected_tier=expected_tier,
                actual_tier=actual_tier,
                correct_routing=correct,
                tokens_used=result["tokens_used"],
                latency_seconds=latency,
                estimated_cost_usd=result["estimated_cost_usd"],
            )
            results.append(eval_result)

            status = "PASS" if correct else "FAIL"
            print(f"  {status} | Expected: {expected_tier} | Got: {actual_tier} | "
                  f"{result['tokens_used']} tokens | ${result['estimated_cost_usd']:.6f} | "
                  f"{latency:.2f}s")

        except Exception as e:
            print(f"  ERROR: {e}")

    # Print summary
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    print(f"  Routing Accuracy:   {routing_accuracy(results)}%")
    print(f"  Average Latency:    {average_latency(results)}s")
    print(f"  Total Cost:         ${total_cost(results):.6f}")
    print(f"  Cost by Tier:       {cost_by_tier(results)}")

    savings = estimated_savings(results)
    print(f"\n  COST SAVINGS vs ALL-LARGE:")
    print(f"    Actual cost:      ${savings['actual_cost_usd']:.6f}")
    print(f"    Hypothetical:     ${savings['hypothetical_cost_usd']:.6f}")
    print(f"    Savings:          ${savings['savings_usd']:.6f} ({savings['savings_pct']}%)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_evaluation())
