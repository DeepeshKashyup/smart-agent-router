"""Embedding generation using Vertex AI."""

from langchain_google_vertexai import VertexAIEmbeddings

from app.core.config import get_settings, load_yaml_config
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_embedding_model() -> VertexAIEmbeddings:
    """Create a Vertex AI embedding model instance."""
    settings = get_settings()
    config = load_yaml_config()
    model_name = config["retrieval"].get("embedding_model", "text-embedding-004")

    return VertexAIEmbeddings(
        model_name=model_name,
        project=settings.google_cloud_project,
        location=settings.vertex_ai_location,
    )


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors.
    """
    model = get_embedding_model()
    logger.info("generating_embeddings", count=len(texts))
    embeddings = await model.aembed_documents(texts)
    logger.info("embeddings_generated", count=len(embeddings))
    return embeddings
