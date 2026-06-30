import asyncio
import logging
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import AsyncSessionLocal, RuleORM, create_tables, get_session
from backend.log_config import configure_logging
from backend.models import AskRequest, AskResponse
from backend.parser import parse_rules_file

configure_logging()
logger = logging.getLogger(__name__)

if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)
    logger.info("Sentry initialized")
else:
    logger.warning("SENTRY_DSN not configured; error tracking disabled")


async def _run_embeddings_background() -> None:
    """Background task: embed all rules with rate-limit-aware batching."""
    from backend.services.embedding_service import embed_all_rules

    try:
        async with AsyncSessionLocal() as session:
            embedded = await embed_all_rules(session)
        logger.info("Background embedding complete: %d rules embedded", embedded)
    except Exception as exc:
        logger.error("Background embedding failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await create_tables()

    async with AsyncSessionLocal() as session:
        count_result = await session.execute(select(func.count()).select_from(RuleORM))
        count = count_result.scalar_one()

        if count == 0:
            try:
                logger.info("Rules table is empty — parsing rules file")
                rules = parse_rules_file()
                for rule in rules:
                    session.add(
                        RuleORM(
                            rule_number=rule.rule_number,
                            section_title=rule.section_title,
                            rule_text=rule.rule_text,
                            full_text=rule.full_text,
                        )
                    )
                await session.commit()
                logger.info("Parsed %d rules and inserted into database", len(rules))
            except Exception as exc:
                raise RuntimeError(f"Failed to parse and insert rules: {exc}") from exc
        else:
            logger.info("Rules table already has %d rules — skipping parse", count)

        if settings.VOYAGE_API_KEY:
            null_result = await session.execute(
                select(func.count()).select_from(RuleORM).where(RuleORM.embedding.is_(None))
            )
            null_count = null_result.scalar_one()
            if null_count > 0:
                logger.info(
                    "%d rules need embeddings — starting background embedding task", null_count
                )
                asyncio.get_event_loop().create_task(_run_embeddings_background())
            else:
                logger.info("All rules already embedded")
        else:
            logger.warning("VOYAGE_API_KEY not set — skipping embedding generation")

    yield


app = FastAPI(title="MagicRules", description="Magic: The Gathering Rules QA", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next: object) -> Response:
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()
    response: Response = await call_next(request)  # type: ignore[operator]
    latency = (time.perf_counter() - start) * 1000
    logger.info(
        "request_id=%s method=%s path=%s status=%s latency_ms=%.0f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        latency,
    )
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/rules")
async def list_rules(
    limit: int = 10,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, str]]:
    result = await session.execute(select(RuleORM).limit(limit).offset(offset))
    rules = result.scalars().all()
    return [
        {
            "rule_number": r.rule_number,
            "section_title": r.section_title,
            "rule_text": r.rule_text,
        }
        for r in rules
    ]


@app.get("/search")
async def search_rules(
    q: str,
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, str]]:
    from backend.services.retrieval_service import retrieve_similar_rules

    rules = await retrieve_similar_rules(q, limit=5, session=session)
    return [
        {
            "rule_number": r.rule_number,
            "section_title": r.section_title,
            "rule_text": r.rule_text,
        }
        for r in rules
    ]


@app.post("/answer")
async def answer_question(
    request: AskRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    from backend.services.answer_service import generate_answer
    from backend.services.retrieval_service import retrieve_similar_rules

    retrieved = await retrieve_similar_rules(request.question, limit=5, session=session)
    answer = await generate_answer(request.question, retrieved)
    return answer.model_dump()


@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(
    request: AskRequest,
    session: AsyncSession = Depends(get_session),
) -> AskResponse:
    from backend.services.qa_service import ask

    try:
        return await ask(request.question, session)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unhandled error: %s", exc)
        sentry_sdk.capture_exception(exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# --- Serve built frontend (production) ---
# Mount the Vite build output so `uvicorn backend.main:app` serves the full app
# at http://localhost:8000. During development, use `npm run dev` instead and
# browse to http://localhost:5173.
_FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.is_dir():
    # Serve Vite's hashed asset bundles
    app.mount(
        "/assets",
        StaticFiles(directory=_FRONTEND_DIST / "assets"),
        name="frontend-assets",
    )
    # Serve other static files (favicon.svg, icons.svg, …)
    app.mount(
        "/static",
        StaticFiles(directory=_FRONTEND_DIST),
        name="frontend-static",
    )

    _INDEX = _FRONTEND_DIST / "index.html"

    @app.get("/", include_in_schema=False)
    async def serve_root() -> FileResponse:
        return FileResponse(_INDEX)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:
        """Return index.html for any unmatched path so the React SPA handles routing."""
        return FileResponse(_INDEX)
else:
    logger.warning(
        "frontend/dist not found — run `npm run build` inside the frontend/ directory "
        "to enable single-server mode. For development use `npm run dev` on port 5173."
    )
