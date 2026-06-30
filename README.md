<a href="https://spec4.ai">
  <img src="BWS4-white-100.png" alt="Built with Spec4" align="right" style="margin-left: 10px;" />
</a>
# MagicRules

A rules-question assistant for Magic: The Gathering that grounds answers in the official Comprehensive Rules document. Players type natural-language rules questions and receive clear, accurate answers that cite and quote the exact rule(s) used, enabling verification and settling disputes with authoritative, citable evidence.

MagicRules combines a React frontend with a FastAPI backend, PostgreSQL vector search, and Claude AI to deliver a seamless experience for rules clarification. Every answer is backed by the official rules text, making it the definitive tool for resolving rules disputes at the table.

## Key Features

- **Natural-language rules questions** — Ask questions in plain English; no need to know rule numbers or structure.
- **Authoritative answers with citations** — Every answer quotes the exact rule(s) from the official Comprehensive Rules document.
- **Vector-powered search** — Voyage AI embeddings + pgvector find the most relevant rules, even for complex or indirect questions.
- **Structured output** — Claude uses tool-use to return a validated schema: answer text, citations, and a disclaimer when no exact match is found.
- **Dark-themed UI** — A polished, responsive React interface with a dark gradient and red accent.
- **Single-server mode** — The built frontend is served directly by the FastAPI process; no separate web server needed.

## Technology Stack

### Backend
- **FastAPI** — Async Python web framework; async lifespan context for startup seeding and background embedding
- **Anthropic Claude API** — LLM answer generation via forced tool-use for structured output (`claude-haiku-4-5-20251001` by default)
- **Voyage AI** — `voyage-3-lite` model producing 512-dimensional embeddings for semantic search
- **PostgreSQL + pgvector** — Vector similarity search with `<->` cosine distance operator
- **SQLAlchemy (async)** — `asyncpg` driver, schema auto-created at startup via `create_tables()`
- **Pydantic Settings** — Typed configuration from `.env`
- **Sentry** — Error tracking and performance monitoring

### Frontend
- **React 19 + TypeScript** — Functional components with hooks
- **Vite 8** — Build tool and dev server (proxies API requests to FastAPI during development)
- **React Hook Form + Zod** — Form state management and schema validation
- **Vitest + Testing Library** — Unit and component tests
- **Plain CSS** — Dark-theme custom stylesheet; no CSS framework

### Testing & Tooling
- **pytest + pytest-asyncio** — Backend unit and integration tests (all function-scoped fixtures)
- **ruff** — Python linting and formatting
- **pyright** — Python static type checking (strict mode)
- **oxlint + Prettier** — Frontend linting and formatting

## Prerequisites

- **Python 3.11+**
- **uv** — Python package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Node.js 20+** and **npm**
- **PostgreSQL 15+ with pgvector**

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/MagicRules.git
cd MagicRules
```

### 2. Set Up PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql@15 pgvector
brew services start postgresql@15
createdb rulelawyerdb
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib postgresql-15-pgvector
sudo -u postgres createdb rulelawyerdb
```

The pgvector extension is enabled automatically at first startup via `CREATE EXTENSION IF NOT EXISTS vector`.

### 3. Install Backend Dependencies

```bash
uv sync
```

This creates a `.venv` and installs all dependencies from `pyproject.toml`.

### 4. Create `.env`

Create `.env` in the project root:

```dotenv
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rulelawyerdb
ANTHROPIC_API_KEY=sk-ant-...
VOYAGE_API_KEY=pa-...
SENTRY_DSN=https://...@sentry.io/...   # optional
CLAUDE_MODEL=claude-haiku-4-5-20251001
```

### 5. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 6. Create `frontend/.env` (optional)

```dotenv
VITE_SENTRY_DSN=https://...@sentry.io/...
```

Only needed if you want Sentry in the browser. The API base URL is not required — the Vite dev proxy and the FastAPI static file server both handle routing automatically.

## Running the Application

### Option A — Single-server mode (production-like)

Build the frontend once, then run a single uvicorn process that serves both the API and the UI:

```bash
cd frontend && npm run build && cd ..
uv run uvicorn backend.main:app --reload
```

Browse to `http://localhost:8000`. The API docs are at `http://localhost:8000/docs`.

### Option B — Dev mode (hot-reload UI)

Run the backend and frontend in separate terminals for instant UI hot-reload:

**Terminal 1 — Backend:**
```bash
uv run uvicorn backend.main:app --reload
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Browse to `http://localhost:5173`. API requests are proxied to `http://localhost:8000` by Vite.

### First-run behaviour

On startup the backend:
1. Creates all database tables (and enables pgvector) if they don't exist.
2. Parses the Comprehensive Rules file and seeds the database if the table is empty.
3. Launches a background task to generate embeddings for any rules that don't have them yet.

Embedding generation uses Voyage AI's free tier (3 RPM limit) and batches rules with a 21-second inter-batch delay, so it runs slowly in the background. The API is fully usable before it completes — questions are answered using whatever embeddings are available.

## Running Tests

**Backend:**
```bash
uv run pytest
```

Integration tests that call external APIs are marked `@pytest.mark.integration` and can be skipped:
```bash
uv run pytest -m "not integration"
```

**Frontend:**
```bash
cd frontend
npm run test
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (`postgresql://user:password@host:port/db`) |
| `ANTHROPIC_API_KEY` | Yes | Anthropic Claude API key |
| `VOYAGE_API_KEY` | Yes | Voyage AI API key (for embeddings) |
| `CLAUDE_MODEL` | No | Claude model ID (default: `claude-haiku-4-5-20251001`) |
| `SENTRY_DSN` | No | Sentry backend DSN |
| `CORS_ORIGINS` | No | Comma-separated allowed origins (default: `http://localhost:5173`) |
| `LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING`, or `ERROR` (default: `INFO`) |

| Frontend Variable | Required | Description |
|-------------------|----------|-------------|
| `VITE_SENTRY_DSN` | No | Sentry browser DSN |

### Getting API Keys

1. **Anthropic** — [platform.anthropic.com](https://platform.anthropic.com) → API Keys
2. **Voyage AI** — [voyageai.com](https://www.voyageai.com) → Dashboard → API Keys. Free tier: 200M tokens/month, 3 RPM.
3. **Sentry** — [sentry.io](https://sentry.io) → New Project → copy DSN. Free tier: 5k events/month.

## Project Structure

```
MagicRules/
├── pyproject.toml              # Python deps + ruff/pyright config (managed by uv)
├── uv.lock                     # Locked dependency versions
├── .python-version             # Python version pin
├── .env                        # API keys — never commit
│
├── backend/                    # FastAPI application
│   ├── main.py                 # App entry point, lifespan, all routes
│   ├── config.py               # Pydantic Settings
│   ├── database.py             # SQLAlchemy engine, RuleORM, pgvector schema
│   ├── models.py               # Pydantic request/response models
│   ├── parser.py               # Comprehensive Rules .txt parser
│   ├── embeddings.py           # Voyage AI embedding client
│   ├── log_config.py           # Structured JSON logging
│   ├── services/
│   │   ├── embedding_service.py    # Rate-limit-aware batch embedding
│   │   ├── retrieval_service.py    # pgvector cosine similarity search
│   │   ├── answer_service.py       # Claude tool-use answer generation
│   │   └── qa_service.py           # Orchestration: retrieve → answer
│   └── tests/                  # pytest test suite
│
├── frontend/                   # React + TypeScript frontend
│   ├── package.json
│   ├── vite.config.ts          # Vite + Vitest config, dev proxy
│   ├── src/
│   │   ├── App.tsx
│   │   ├── index.css           # Dark-theme CSS
│   │   ├── api/client.ts       # askQuestion() fetch wrapper + interfaces
│   │   ├── components/
│   │   │   ├── QuestionForm.tsx    # React Hook Form + Zod validation
│   │   │   ├── AnswerDisplay.tsx   # Answer + citation list
│   │   │   └── CitationCard.tsx    # Expandable rule citation
│   │   ├── hooks/useQuestion.ts    # Async submit state machine
│   │   └── tests/              # Vitest + Testing Library tests
│   └── dist/                   # Built output (gitignored; created by npm run build)
│
└── .spec4/v0/                  # Spec4 planning artifacts
    ├── IMPLEMENTED             # Marker — all phases complete
    ├── vision.json
    ├── stack.json
    ├── deployment-plan.md
    └── phases/                 # phase1.md … phase5.md
```

## Troubleshooting

**Backend won't start:**
- Check PostgreSQL is running: `psql -U postgres -c "SELECT 1"`
- Confirm `DATABASE_URL` in `.env` matches your local setup
- Run `uv sync` to ensure all dependencies are installed

**`{"detail":"Not Found"}` at `http://localhost:8000`:**
- The frontend hasn't been built yet. Run `cd frontend && npm run build` first, then restart uvicorn.
- Alternatively, use dev mode and browse to `http://localhost:5173` instead.

**Voyage AI 429 rate limit error:**
- The free tier allows 3 requests per minute. Embedding runs as a background task — the API remains fully usable, and embedding completes gradually over time.
- If you want to skip embedding entirely, remove `VOYAGE_API_KEY` from `.env`.

**`asyncpg` loop mismatch in tests:**
- All pytest fixtures must be function-scoped (not session-scoped). `asyncio_default_fixture_loop_scope = "function"` is set in `pyproject.toml` to enforce this.

**API calls fail in dev mode:**
- Ensure the backend is running on port 8000; Vite proxies `/ask`, `/answer`, `/search`, `/rules`, and `/health` to it automatically.

## References

- [Magic: The Gathering Comprehensive Rules](https://magic.wizards.com/en/rules)
- [Anthropic Claude API](https://docs.anthropic.com/en/api/getting-started)
- [Voyage AI Embeddings](https://docs.voyageai.com/docs/embeddings)
- [FastAPI](https://fastapi.tiangolo.com/)
- [pgvector](https://github.com/pgvector/pgvector)
- [uv](https://docs.astral.sh/uv/)
