import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.models import Rule

SKIP_IF_NO_ANTHROPIC = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set"
)

SAMPLE_RULES = [
    Rule(
        rule_number="405.1",
        section_title="The Stack",
        rule_text="When a spell or ability is put onto the stack, it is put on top of the stack.",
        full_text="When a spell or ability is put onto the stack, it is put on top of the stack.",
    )
]


def _make_mock_response(answer_text: str, has_match: bool) -> MagicMock:
    block = MagicMock()
    block.type = "tool_use"
    block.input = {
        "answer_text": answer_text,
        "citations": [{"rule_number": "405.1", "quoted_text": "put on top of the stack"}],
        "has_exact_match": has_match,
    }
    response = MagicMock()
    response.content = [block]
    return response


@pytest.mark.asyncio
async def test_generate_answer_returns_answer_object():
    mock_response = _make_mock_response("The stack is a zone.", True)

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

        answer = await generate_answer("What is the stack?", SAMPLE_RULES)
        assert answer.answer_text == "The stack is a zone."
        assert answer.has_exact_match is True


@pytest.mark.asyncio
async def test_citations_include_rule_number_and_quoted_text():
    mock_response = _make_mock_response("The stack is a zone.", True)

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

        answer = await generate_answer("What is the stack?", SAMPLE_RULES)
        assert len(answer.citations) > 0
        for citation in answer.citations:
            assert citation.rule_number
            assert citation.quoted_text


@pytest.mark.asyncio
async def test_no_match_sets_disclaimer():
    block = MagicMock()
    block.type = "tool_use"
    block.input = {
        "answer_text": "No relevant rule found.",
        "citations": [],
        "has_exact_match": False,
    }
    response = MagicMock()
    response.content = [block]

    with (
        patch("backend.services.answer_service.settings") as mock_settings,
        patch("backend.services.answer_service.AsyncAnthropic") as mock_anthropic,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.CLAUDE_MODEL = "claude-sonnet-4-6"
        mock_settings.MAX_TOKENS = 1000
        instance = MagicMock()
        instance.messages.create = AsyncMock(return_value=response)
        mock_anthropic.return_value = instance

        from backend.services.answer_service import generate_answer

        answer = await generate_answer("What is my favorite color?", SAMPLE_RULES)
        assert answer.has_exact_match is False
        assert answer.disclaimer is not None


@pytest.mark.asyncio
async def test_missing_api_key_raises_error():
    with patch("backend.services.answer_service.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = ""

        from backend.services.answer_service import generate_answer

        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            await generate_answer("test?", SAMPLE_RULES)


@pytest.mark.asyncio
@SKIP_IF_NO_ANTHROPIC
async def test_generate_answer_live():
    from backend.services.answer_service import generate_answer

    answer = await generate_answer("What is the stack?", SAMPLE_RULES)
    assert answer.answer_text
    assert isinstance(answer.has_exact_match, bool)
