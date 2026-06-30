import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import RuleORM
from backend.models import Rule

SKIP_IF_NO_KEYS = pytest.mark.skipif(
    not (os.getenv("VOYAGE_API_KEY") and os.getenv("ANTHROPIC_API_KEY")),
    reason="VOYAGE_API_KEY and ANTHROPIC_API_KEY required for integration tests",
)


SAMPLE_RULES = [
    Rule(
        rule_number="405.1",
        section_title="The Stack",
        rule_text=("The stack is a zone. A spell or ability on the stack is not a permanent."),
        full_text=("The stack is a zone. A spell or ability on the stack is not a permanent."),
    )
]


@pytest.mark.asyncio
async def test_full_pipeline_with_mocks(db_session: AsyncSession):
    """Test retrieve + answer with mocked external services."""
    rule_orm = RuleORM(
        rule_number="405.1t",
        section_title="The Stack",
        rule_text="The stack is a zone.",
        full_text="The stack is a zone.",
        embedding=[0.1] * 512,
    )
    db_session.add(rule_orm)
    await db_session.flush()

    fake_embed = [[0.1] * 512]
    block = MagicMock()
    block.type = "tool_use"
    block.input = {
        "answer_text": "The stack is a zone.",
        "citations": [{"rule_number": "405.1t", "quoted_text": "The stack is a zone."}],
        "has_exact_match": True,
    }
    mock_response = MagicMock()
    mock_response.content = [block]

    with (
        patch(
            "backend.services.retrieval_service.generate_embeddings",
            new=AsyncMock(return_value=fake_embed),
        ),
        patch("backend.services.answer_service.settings") as mock_settings,
        patch("backend.services.answer_service.AsyncAnthropic") as mock_anthropic,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.CLAUDE_MODEL = "claude-sonnet-4-6"
        mock_settings.MAX_TOKENS = 1000
        instance = MagicMock()
        instance.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.return_value = instance

        from backend.services.answer_service import generate_answer
        from backend.services.retrieval_service import retrieve_similar_rules

        retrieved = await retrieve_similar_rules("What is the stack?", limit=5, session=db_session)
        assert len(retrieved) >= 1

        answer = await generate_answer("What is the stack?", retrieved)
        assert answer.answer_text
        assert answer.has_exact_match is True
        for c in answer.citations:
            assert c.rule_number in {r.rule_number for r in retrieved}


@pytest.mark.asyncio
async def test_unanswerable_question_sets_disclaimer(db_session: AsyncSession):
    block = MagicMock()
    block.type = "tool_use"
    block.input = {
        "answer_text": "I cannot determine your favorite card color from the rules.",
        "citations": [],
        "has_exact_match": False,
    }
    mock_response = MagicMock()
    mock_response.content = [block]

    with (
        patch("backend.services.answer_service.settings") as mock_settings,
        patch("backend.services.answer_service.AsyncAnthropic") as mock_anthropic,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.CLAUDE_MODEL = "claude-sonnet-4-6"
        mock_settings.MAX_TOKENS = 1000
        instance = MagicMock()
        instance.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.return_value = instance

        from backend.services.answer_service import generate_answer

        answer = await generate_answer("What is the color of my favorite card?", SAMPLE_RULES)
        assert answer.has_exact_match is False
        assert answer.disclaimer is not None
