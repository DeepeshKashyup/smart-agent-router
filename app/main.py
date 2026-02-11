"""FastAPI application entrypoint for Smart Agent Router."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.middleware.error_handler import ErrorHandlerMiddleware

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    setup_logging(settings.log_level)
    logger.info(
        "app_starting",
        large_model=settings.large_model_name,
        small_model=settings.small_model_name,
    )
    yield
    logger.info("app_shutting_down")


app = FastAPI(
    title="Smart Agent Router",
    description="Cost-effective agentic AI with intelligent model routing. "
    "Routes queries to lightweight or powerful models based on complexity, "
    "demonstrating up to 70% token cost reduction.",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ErrorHandlerMiddleware)

# Routes
app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "models": {
            "large": settings.large_model_name,
            "small": settings.small_model_name,
            "router": settings.routing_model_name,
        },
    }
