import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

SKIP_IF_NO_KEY = pytest.mark.skipif(
    not os.getenv("VOYAGE_API_KEY"), reason="VOYAGE_API_KEY not set"
)


@pytest.mark.asyncio
@SKIP_IF_NO_KEY
async def test_generate_embeddings_returns_correct_dimension():
    from backend.embeddings import generate_embeddings

    embeddings = await generate_embeddings(["What is the stack?"])
    assert len(embeddings) == 1
    assert len(embeddings[0]) == 512


@pytest.mark.asyncio
@SKIP_IF_NO_KEY
async def test_embedding_count_matches_input():
    from backend.embeddings import generate_embeddings

    texts = ["Rule 1 text.", "Rule 2 text.", "Rule 3 text."]
    embeddings = await generate_embeddings(texts)
    assert len(embeddings) == len(texts)


@pytest.mark.asyncio
async def test_missing_api_key_raises_error():
    with patch("backend.embeddings.settings") as mock_settings:
        mock_settings.VOYAGE_API_KEY = ""
        from backend.embeddings import generate_embeddings

        with pytest.raises(RuntimeError, match="VOYAGE_API_KEY"):
            await generate_embeddings(["test"])


@pytest.mark.asyncio
async def test_generate_embeddings_mocked():
    fake_embeddings = [[0.1] * 512]
    mock_result = MagicMock()
    mock_result.embeddings = fake_embeddings
    mock_client = MagicMock()
    mock_client.embed = AsyncMock(return_value=mock_result)

    with (
        patch("backend.embeddings.settings") as mock_settings,
        patch("backend.embeddings.voyageai.AsyncClient", return_value=mock_client),
    ):
        mock_settings.VOYAGE_API_KEY = "test-key"
        mock_settings.EMBEDDING_MODEL = "voyage-3-lite"
        from backend.embeddings import generate_embeddings

        result = await generate_embeddings(["test text"])
        assert len(result) == 1
        assert len(result[0]) == 512
