"""API endpoints for the Smart Agent Router."""

from pydantic import BaseModel, Field
from fastapi import APIRouter

from app.core.logging import get_logger, generate_correlation_id
from src.chains.pipeline import SmartRouterPipeline
from src.agents.agent import CostTracker

router = APIRouter()
logger = get_logger(__name__)
pipeline = SmartRouterPipeline()
cost_tracker = CostTracker()


class QueryRequest(BaseModel):
    """Incoming query request."""

    query: str = Field(..., min_length=1, max_length=10000)
    context: str | None = Field(default=None, description="Optional context for the query")
    force_model: str | None = Field(default=None, description="Force a specific model tier: 'large' or 'small'")


class QueryResponse(BaseModel):
    """Query response with cost metadata."""

    answer: str
    model_used: str
    complexity: str
    confidence: float
    tokens_used: int
    estimated_cost_usd: float
    correlation_id: str


class CostSummaryResponse(BaseModel):
    """Aggregated cost tracking summary."""

    total_requests: int
    total_tokens: int
    total_cost_usd: float
    routed_to_small: int
    routed_to_large: int
    cost_savings_pct: float


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest) -> QueryResponse:
    """Process a query through the smart routing pipeline.

    The router classifies query complexity and routes to the appropriate model:
    - SIMPLE/MODERATE queries -> lightweight model (Gemini Flash)
    - COMPLEX queries -> powerful model (Gemini Pro)
    """
    correlation_id = generate_correlation_id()
    logger.info("query_received", correlation_id=correlation_id, query_length=len(request.query))

    result = await pipeline.run(
        query=request.query,
        context=request.context,
        force_model=request.force_model,
        correlation_id=correlation_id,
    )

    cost_tracker.record(result)

    logger.info(
        "query_completed",
        correlation_id=correlation_id,
        model_used=result["model_used"],
        complexity=result["complexity"],
        tokens=result["tokens_used"],
        cost=result["estimated_cost_usd"],
    )

    return QueryResponse(correlation_id=correlation_id, **result)


@router.get("/costs", response_model=CostSummaryResponse)
async def get_cost_summary() -> CostSummaryResponse:
    """Get aggregated cost tracking summary with savings percentage."""
    return cost_tracker.get_summary()


@router.post("/costs/reset")
async def reset_costs():
    """Reset cost tracking counters."""
    cost_tracker.reset()
    return {"status": "reset"}
