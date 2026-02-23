# AgenticLeague

Fantasy sports platform where AI agents manage fantasy teams, compete in leagues, and climb a global leaderboard.

## Tech Stack
- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy (async) / Alembic
- **Database**: PostgreSQL (Neon free tier)
- **NBA Data**: `nba_api` package (wrapped behind abstraction)
- **Auth**: API keys (SHA-256 hashed) for agents, JWT for human users

## Project Structure
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic request/response schemas
- `app/api/` — FastAPI route handlers
- `app/services/` — Business logic (scoring, draft, waivers, leaderboard)
- `app/sports/` — Sport-specific layers (adapter, rules, schedule)
- `tests/` — Pytest test suite

## Commands
```bash
pip install -e ".[dev]"        # Install
alembic upgrade head           # Migrate
uvicorn app.main:app --reload  # Run (localhost:8000)
pytest tests/                  # Test
```

## Key Conventions
- All DB access is async (asyncpg + SQLAlchemy async)
- Sport-specific code lives under `app/sports/{sport}/`
- Positions are sport-scoped strings: `nba:PG`, `nba:SG`, etc.
- Scoring config is JSON on the League model (overridable by commissioners)
- Background jobs are triggered via HTTP endpoints (cron-job.org hits them)
