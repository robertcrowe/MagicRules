from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from backend.models import Answer, AskResponse


def _make_ask_response() -> AskResponse:
    return AskResponse(
        question="What is the stack?",
        answer_text="The stack is a zone.",
        citations=[],
        has_exact_match=True,
        disclaimer=None,
        latency_ms=100.0,
    )


@pytest.mark.asyncio
async def test_ask_valid_question(client: AsyncClient):
    with patch(
        "backend.services.qa_service.retrieve_similar_rules", new=AsyncMock(return_value=[])
    ):
        with patch(
            "backend.services.qa_service.generate_answer",
            new=AsyncMock(
                return_value=Answer(
                    answer_text="The stack is a zone.",
                    citations=[],
                    has_exact_match=True,
                )
            ),
        ):
            response = await client.post("/ask", json={"question": "What is the stack?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer_text" in data
    assert "has_exact_match" in data
    assert "latency_ms" in data
    assert data["latency_ms"] >= 0


@pytest.mark.asyncio
async def test_ask_empty_question_returns_422(client: AsyncClient):
    response = await client.post("/ask", json={"question": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ask_too_long_question_returns_422(client: AsyncClient):
    response = await client.post("/ask", json={"question": "x" * 501})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_ask_server_error_returns_500(client: AsyncClient):
    with patch(
        "backend.services.qa_service.retrieve_similar_rules",
        new=AsyncMock(side_effect=RuntimeError("DB down")),
    ):
        response = await client.post("/ask", json={"question": "What is trample?"})
    assert response.status_code == 500
