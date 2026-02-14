"""Vector database operations using ChromaDB."""

import chromadb
from langchain_community.vectorstores import Chroma

from app.core.config import get_settings, load_yaml_config
from app.core.logging import get_logger
from src.retrieval.embeddings import get_embedding_model

logger = get_logger(__name__)


def get_vectorstore(collection_name: str = "default") -> Chroma:
    """Initialize or connect to a ChromaDB vector store.

    Args:
        collection_name: Name of the Chroma collection.

    Returns:
        LangChain Chroma vectorstore instance.
    """
    settings = get_settings()
    embedding_model = get_embedding_model()

    return Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=settings.chroma_persist_dir,
    )


async def similarity_search(query: str, top_k: int | None = None) -> list[str]:
    """Search the vector store for relevant documents.

    Args:
        query: Search query text.
        top_k: Number of results to return. Defaults to config value.

    Returns:
        List of relevant document texts.
    """
    config = load_yaml_config()
    if top_k is None:
        top_k = config["retrieval"].get("top_k", 5)

    vectorstore = get_vectorstore()
    results = await vectorstore.asimilarity_search(query, k=top_k)
    logger.info("similarity_search", query_length=len(query), results=len(results))
    return [doc.page_content for doc in results]
