import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.embeddings import generate_embeddings
from backend.models import Rule

logger = logging.getLogger(__name__)


async def retrieve_similar_rules(
    query: str,
    limit: int = 5,
    session: AsyncSession | None = None,
) -> list[Rule]:
    """Retrieve the top-k rules most similar to the query using pgvector."""
    if session is None:
        raise ValueError("session is required")

    if not query.strip():
        logger.warning("Empty query received; returning empty list")
        return []

    query_embeddings = await generate_embeddings([query])
    query_vec = query_embeddings[0]

    # Format vector for pgvector: [0.1,0.2,...]
    vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

    stmt = text(
        "SELECT id, rule_number, section_title, rule_text, full_text, created_at "
        "FROM rules "
        "ORDER BY embedding <-> :vec "
        "LIMIT :limit"
    )
    result = await session.execute(stmt, {"vec": vec_str, "limit": limit})
    rows = result.mappings().all()

    rules = [
        Rule(
            id=row["id"],
            rule_number=row["rule_number"],
            section_title=row["section_title"],
            rule_text=row["rule_text"],
            full_text=row["full_text"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
    logger.info("Retrieved %d rules for query: %.60s...", len(rules), query)
    return rules
