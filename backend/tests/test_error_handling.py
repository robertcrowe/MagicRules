from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_missing_voyage_key_raises_on_embed():
    with patch("backend.embeddings.settings") as mock_settings:
        mock_settings.VOYAGE_API_KEY = ""
        from backend.embeddings import generate_embeddings

        with pytest.raises(RuntimeError, match="VOYAGE_API_KEY"):
            await generate_embeddings(["test"])


@pytest.mark.asyncio
async def test_missing_anthropic_key_raises_on_answer():
    from backend.models import Rule

    with patch("backend.services.answer_service.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = ""
        from backend.services.answer_service import generate_answer

        rules = [
            Rule(
                rule_number="100.1",
                section_title="Test",
                rule_text="Test text.",
                full_text="Test text.",
            )
        ]
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            await generate_answer("test?", rules)


@pytest.mark.asyncio
async def test_ask_question_too_long(client: AsyncClient):
    response = await client.post("/ask", json={"question": "a" * 600})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_voyage_api_error_propagates():
    with (
        patch("backend.embeddings.settings") as mock_settings,
        patch("backend.embeddings.voyageai.AsyncClient") as mock_client_cls,
    ):
        mock_settings.VOYAGE_API_KEY = "bad-key"
        mock_settings.EMBEDDING_MODEL = "voyage-3-lite"
        instance = mock_client_cls.return_value
        instance.embed = AsyncMock(side_effect=Exception("API error"))

        from backend.embeddings import generate_embeddings

        with pytest.raises(RuntimeError, match="Failed to generate embeddings"):
            await generate_embeddings(["test"])
