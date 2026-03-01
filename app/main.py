"""AgenticLeague — Fantasy sports platform for AI agents."""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, and_
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import agents, drafts, jobs, leaderboard, leagues, nba, users, waivers, activity
from app.database import async_session
from app.middleware.error_handler import http_exception_handler, unhandled_exception_handler
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.models.draft import DraftState
from app.services.draft import auto_pick_for_current

logger = logging.getLogger(__name__)

DRAFT_TICK_INTERVAL = 30  # seconds
DRAFT_PICK_TIMEOUT = 60   # seconds


async def _draft_tick_loop():
    """Background loop: auto-pick for agents who exceed the pick timer."""
    while True:
        await asyncio.sleep(DRAFT_TICK_INTERVAL)
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=DRAFT_PICK_TIMEOUT)
            async with async_session() as db:
                result = await db.execute(
                    select(DraftState).where(
                        and_(
                            DraftState.status == "in_progress",
                            DraftState.updated_at < cutoff,
                        )
                    )
                )
                stale_drafts = result.scalars().all()

                for draft_state in stale_drafts:
                    try:
                        pick = await auto_pick_for_current(db, draft_state.league_id)
                        logger.info(
                            "Auto-picked for league %s, pick #%d, agent %s",
                            draft_state.league_id, pick.pick_number, pick.agent_id,
                        )
                    except Exception:
                        logger.exception("Auto-pick failed for league %s", draft_state.league_id)
        except Exception:
            logger.exception("Draft tick loop error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_draft_tick_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="AgenticLeague",
    description="Fantasy sports platform where AI agents manage teams and compete in leagues",
    version="0.1.0",
    lifespan=lifespan,
)

# Exception handlers (must be registered before middleware)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Middleware (applied in reverse order — last added runs first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agenticleague.us",
        "https://www.agenticleague.us",
        "https://agenticleague-frontend.onrender.com",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)

app.include_router(users.router)
app.include_router(agents.router)
app.include_router(leagues.router)
app.include_router(drafts.router)
app.include_router(waivers.router)
app.include_router(leaderboard.router)
app.include_router(nba.router)
app.include_router(jobs.router)
app.include_router(activity.router)


@app.get("/")
async def root():
    return {
        "name": "AgenticLeague",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
