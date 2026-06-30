import logging
import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import AskResponse
from backend.services.answer_service import generate_answer
from backend.services.retrieval_service import retrieve_similar_rules

logger = logging.getLogger(__name__)


async def ask(question: str, session: AsyncSession) -> AskResponse:
    """Orchestrate retrieval + answer generation for a user question."""
    request_id = str(uuid.uuid4())[:8]
    logger.info("request_id=%s question=%.80s", request_id, question)
    start = time.perf_counter()

    retrieved_rules = await retrieve_similar_rules(question, limit=5, session=session)
    answer = await generate_answer(question, retrieved_rules)

    latency_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request_id=%s has_match=%s citations=%d latency_ms=%.0f",
        request_id,
        answer.has_exact_match,
        len(answer.citations),
        latency_ms,
    )

    return AskResponse(
        question=question,
        answer_text=answer.answer_text,
        citations=answer.citations,
        has_exact_match=answer.has_exact_match,
        disclaimer=answer.disclaimer,
        latency_ms=latency_ms,
    )
