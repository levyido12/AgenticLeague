"""Global leaderboard endpoint."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.players import LeaderboardEntry
from app.services.cache import cached
from app.services.leaderboard import get_global_leaderboard, get_platform_stats

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


class PlatformStatsResponse(BaseModel):
    agent_count: int
    total_fantasy_points: float
    league_count: int


@router.get("/stats", response_model=PlatformStatsResponse)
async def leaderboard_stats(db: AsyncSession = Depends(get_db)):
    """Lightweight stats for the landing page stats bar."""
    return await cached(
        "leaderboard:stats", 120, lambda: get_platform_stats(db)
    )


@router.get("", response_model=list[LeaderboardEntry])
async def leaderboard(db: AsyncSession = Depends(get_db)):
    return await cached(
        "leaderboard:full", 120, lambda: get_global_leaderboard(db)
    )
