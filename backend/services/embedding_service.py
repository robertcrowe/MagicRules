import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import RuleORM
from backend.embeddings import generate_embeddings

logger = logging.getLogger(__name__)

BATCH_SIZE = 10  # conservative for free tier (3 RPM, 10K TPM)
EMBEDDING_DIM = 512  # voyage-3-lite produces 512-dimensional embeddings
# Free tier: 3 RPM => wait at least 20s between requests.
# Add extra buffer so we don't drift into the next window.
BATCH_DELAY_SECONDS = 21.0
MAX_RETRIES = 3


async def _embed_batch_with_retry(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts, retrying on rate-limit errors with backoff."""
    delay = BATCH_DELAY_SECONDS
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await generate_embeddings(texts)
        except RuntimeError as exc:
            msg = str(exc).lower()
            is_rate_limit = "rate" in msg or "429" in msg or "payment" in msg
            if is_rate_limit and attempt < MAX_RETRIES:
                logger.warning(
                    "Rate-limited on attempt %d/%d — waiting %.0fs before retry",
                    attempt,
                    MAX_RETRIES,
                    delay,
                )
                await asyncio.sleep(delay)
                delay *= 2  # exponential backoff
            else:
                raise
    # unreachable, but satisfies type-checker
    raise RuntimeError("Max retries exceeded")  # pragma: no cover


async def embed_all_rules(session: AsyncSession) -> int:
    """Embed all rules that have no embedding. Returns count of newly embedded rules."""
    result = await session.execute(select(RuleORM).where(RuleORM.embedding.is_(None)))
    rules = list(result.scalars().all())

    if not rules:
        logger.info("All rules already embedded")
        return 0

    logger.info(
        "Embedding %d rules in batches of %d (delay %.0fs between batches)",
        len(rules),
        BATCH_SIZE,
        BATCH_DELAY_SECONDS,
    )
    embedded_count = 0

    for i in range(0, len(rules), BATCH_SIZE):
        batch = rules[i : i + BATCH_SIZE]
        texts = [r.full_text for r in batch]

        embeddings = await _embed_batch_with_retry(texts)

        if embeddings and len(embeddings[0]) != EMBEDDING_DIM:
            raise RuntimeError(
                f"Expected embedding dimension {EMBEDDING_DIM}, got {len(embeddings[0])}"
            )

        for rule, embedding in zip(batch, embeddings, strict=True):
            rule.embedding = embedding

        await session.commit()
        embedded_count += len(batch)
        logger.info("Embedded %d/%d rules", embedded_count, len(rules))

        # Respect Voyage AI free-tier rate limit between batches
        if i + BATCH_SIZE < len(rules):
            await asyncio.sleep(BATCH_DELAY_SECONDS)

    return embedded_count
