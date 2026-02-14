"""Seed the vector store with sample documents for demo purposes."""

from src.retrieval.chunking import chunk_documents
from src.retrieval.vectorstore import get_vectorstore
from app.core.logging import setup_logging, get_logger

logger = get_logger(__name__)

SAMPLE_DOCS = [
    """Smart Agent Router is a cost-optimization framework for agentic AI systems.
    It routes queries to lightweight or powerful models based on complexity classification.
    Simple factual queries go to fast, cheap models while complex reasoning tasks
    go to more capable models. This approach can reduce token costs by up to 70%.""",

    """The routing strategy uses a three-tier approach:
    1. Router Model (Gemini Flash): Classifies query complexity in ~50 tokens
    2. Small Model (Gemini Flash): Handles SIMPLE and MODERATE queries
    3. Large Model (Gemini Pro): Handles COMPLEX queries requiring deep reasoning
    The router itself costs less than 1% of the total request cost.""",

    """Cost optimization best practices for LLM applications:
    - Cache frequently asked questions and their responses
    - Use prompt compression to reduce input tokens
    - Implement semantic caching with embedding similarity
    - Set token limits and timeout policies per model tier
    - Monitor cost per query and alert on anomalies
    - Use structured output formats to reduce output tokens""",
]


def seed() -> None:
    """Seed the vector store with sample documents."""
    setup_logging()

    chunks = chunk_documents(SAMPLE_DOCS)
    vectorstore = get_vectorstore()
    vectorstore.add_texts(chunks)

    print(f"Seeded vector store with {len(chunks)} chunks from {len(SAMPLE_DOCS)} documents.")
    logger.info("seed_complete", chunks=len(chunks))


if __name__ == "__main__":
    seed()
