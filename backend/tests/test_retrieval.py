import os
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import RuleORM

SKIP_IF_NO_VOYAGE = pytest.mark.skipif(
    not os.getenv("VOYAGE_API_KEY"), reason="VOYAGE_API_KEY not set"
)


async def _seed_rule_with_embedding(session: AsyncSession, rule_number: str) -> RuleORM:
    rule = RuleORM(
        rule_number=rule_number,
        section_title="Test",
        rule_text="The stack is a zone. Players can respond to spells and abilities.",
        full_text="The stack is a zone. Players can respond to spells and abilities.",
        embedding=[0.1] * 512,
    )
    session.add(rule)
    await session.flush()
    return rule


@pytest.mark.asyncio
async def test_retrieve_similar_rules_returns_results(db_session: AsyncSession):
    await _seed_rule_with_embedding(db_session, "800.1t")

    fake_embedding = [[0.1] * 512]
    with patch(
        "backend.services.retrieval_service.generate_embeddings",
        new=AsyncMock(return_value=fake_embedding),
    ):
        from backend.services.retrieval_service import retrieve_similar_rules

        results = await retrieve_similar_rules("What is the stack?", limit=5, session=db_session)
        assert len(results) >= 1


@pytest.mark.asyncio
async def test_retrieve_respects_limit(db_session: AsyncSession):
    for i in range(3):
        await _seed_rule_with_embedding(db_session, f"801.{i}t")

    fake_embedding = [[0.1] * 512]
    with patch(
        "backend.services.retrieval_service.generate_embeddings",
        new=AsyncMock(return_value=fake_embedding),
    ):
        from backend.services.retrieval_service import retrieve_similar_rules

        results = await retrieve_similar_rules("test", limit=2, session=db_session)
        assert len(results) <= 2


@pytest.mark.asyncio
async def test_empty_query_returns_empty(db_session: AsyncSession):
    from backend.services.retrieval_service import retrieve_similar_rules

    results = await retrieve_similar_rules("   ", limit=5, session=db_session)
    assert results == []


@pytest.mark.asyncio
async def test_retrieve_requires_session():
    from backend.services.retrieval_service import retrieve_similar_rules

    with pytest.raises(ValueError, match="session"):
        await retrieve_similar_rules("test", session=None)
