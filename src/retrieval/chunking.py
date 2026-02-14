"""Document chunking strategies for RAG pipelines."""

from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.core.config import load_yaml_config
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """Create a text splitter with config-driven parameters."""
    config = load_yaml_config()
    retrieval = config.get("retrieval", {})

    return RecursiveCharacterTextSplitter(
        chunk_size=retrieval.get("chunk_size", 512),
        chunk_overlap=retrieval.get("chunk_overlap", 50),
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def chunk_documents(texts: list[str]) -> list[str]:
    """Split documents into chunks for embedding.

    Args:
        texts: List of full document texts.

    Returns:
        List of chunked text segments.
    """
    splitter = get_text_splitter()
    chunks = []
    for text in texts:
        chunks.extend(splitter.split_text(text))
    logger.info("chunking_complete", input_docs=len(texts), output_chunks=len(chunks))
    return chunks
