import logging

import voyageai  # type: ignore[import-untyped]  # noqa: PGH003

from backend.config import settings

logger = logging.getLogger(__name__)


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using Voyage AI."""
    if not settings.VOYAGE_API_KEY:
        raise RuntimeError("VOYAGE_API_KEY is not configured")

    client = voyageai.AsyncClient(api_key=settings.VOYAGE_API_KEY)
    try:
        result = await client.embed(texts, model=settings.EMBEDDING_MODEL)
        # voyageai returns list[list[float]] | list[list[int]]
        return [[float(v) for v in vec] for vec in result.embeddings]
    except Exception as exc:
        logger.error("Voyage AI embedding failed: %s", exc)
        raise RuntimeError(f"Failed to generate embeddings: {exc}") from exc
