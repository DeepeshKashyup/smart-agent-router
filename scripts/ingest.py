"""Data ingestion pipeline - loads documents, chunks, and stores embeddings."""

import asyncio
from pathlib import Path

from src.retrieval.chunking import chunk_documents
from src.retrieval.vectorstore import get_vectorstore
from app.core.logging import setup_logging, get_logger

logger = get_logger(__name__)

RAW_DIR = Path("data/raw")


async def ingest() -> None:
    """Load all .txt and .md files from data/raw, chunk, and store in vector DB."""
    setup_logging()

    files = list(RAW_DIR.glob("*.txt")) + list(RAW_DIR.glob("*.md"))
    if not files:
        logger.warning("no_files_found", directory=str(RAW_DIR))
        print(f"No .txt or .md files found in {RAW_DIR}. Add documents and retry.")
        return

    print(f"Found {len(files)} files to ingest.")
    texts = []
    for f in files:
        content = f.read_text(encoding="utf-8")
        texts.append(content)
        print(f"  Loaded: {f.name} ({len(content)} chars)")

    chunks = chunk_documents(texts)
    print(f"Created {len(chunks)} chunks.")

    vectorstore = get_vectorstore()
    vectorstore.add_texts(chunks)
    print(f"Stored {len(chunks)} chunks in vector store.")
    logger.info("ingestion_complete", files=len(files), chunks=len(chunks))


if __name__ == "__main__":
    asyncio.run(ingest())
