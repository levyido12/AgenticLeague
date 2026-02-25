"""NBA data endpoints (public, no auth required)."""

import asyncio
import logging
from datetime import date, timedelta

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nba", tags=["nba"])


class NBAGameResponse(BaseModel):
    home_team: str
    away_team: str
    game_time: str
    status: str
    game_date: str = ""


class UpcomingGamesResponse(BaseModel):
    games: list[NBAGameResponse]
    game_date: str
    label: str  # "Today", "Tomorrow", "Wednesday", etc.


@router.get("/schedule/today", response_model=list[NBAGameResponse])
async def today_schedule():
    """Return today's NBA games. No auth required."""
    try:
        games = await asyncio.to_thread(_fetch_schedule_for_date, date.today())
        return games
    except Exception:
        logger.exception("Failed to fetch today's NBA schedule")
        return []


@router.get("/schedule/upcoming", response_model=UpcomingGamesResponse)
async def upcoming_schedule():
    """Return the next day with NBA games (today or up to 5 days ahead)."""
    try:
        result = await asyncio.to_thread(_fetch_upcoming)
        return result
    except Exception:
        logger.exception("Failed to fetch upcoming NBA schedule")
        return UpcomingGamesResponse(games=[], game_date="", label="No games found")


def _fetch_upcoming() -> dict:
    today = date.today()
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    month_names = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    # Check today, tomorrow, then skip by 2-3 days to find games faster.
    # NBA plays ~3-4 games per week, so gaps > 2 days are rare during season.
    offsets = [0, 1, 2, 3, 5, 7, 10, 14, 21, 28]

    for offset in offsets:
        check_date = today + timedelta(days=offset)
        games = _fetch_schedule_for_date(check_date)
        if games:
            if offset == 0:
                label = "Today"
            elif offset == 1:
                label = "Tomorrow"
            elif offset < 7:
                label = day_names[check_date.weekday()]
            else:
                label = f"{month_names[check_date.month - 1]} {check_date.day}"
            return {
                "games": games,
                "game_date": check_date.isoformat(),
                "label": label,
            }

    # NBA season runs Oct-Apr; if no games found, we're likely in the off-season
    return {"games": [], "game_date": "", "label": "Off-season"}


def _fetch_schedule_for_date(game_date: date) -> list[dict]:
    import time

    from nba_api.stats.endpoints import scoreboardv2

    time.sleep(0.6)

    formatted = game_date.strftime("%m/%d/%Y")

    try:
        sb = scoreboardv2.ScoreboardV2(game_date=formatted)
        game_header = sb.get_data_frames()[0]
    except Exception:
        logger.exception("nba_api scoreboardv2 failed for %s", formatted)
        return []

    games = []
    for _, row in game_header.iterrows():
        game_status = str(row.get("GAME_STATUS_TEXT", ""))

        home_team = str(row.get("HOME_TEAM_ID", ""))
        away_team = str(row.get("VISITOR_TEAM_ID", ""))

        matchup = str(row.get("GAMECODE", ""))
        if len(matchup) >= 13:
            teams_part = matchup.split("/")[-1] if "/" in matchup else ""
            if len(teams_part) == 6:
                away_team = teams_part[:3]
                home_team = teams_part[3:]

        games.append({
            "home_team": home_team,
            "away_team": away_team,
            "game_time": game_status or "TBD",
            "status": game_status or "Scheduled",
            "game_date": game_date.isoformat(),
        })

    return games
