"""League management endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_agent
from app.models.agent import Agent
from app.models.league import League, LeagueMembership
from app.models.team import Team
from app.schemas.leagues import LeagueCreate, LeagueJoin, LeagueResponse, StandingsEntry
from app.schemas.players import PlayerResponse
from app.services.auth import generate_invite_code
from app.services.leaderboard import get_league_standings
from app.sports.nba import NBARules

router = APIRouter(prefix="/leagues", tags=["leagues"])
_nba_rules = NBARules()


@router.post("", response_model=LeagueResponse, status_code=status.HTTP_201_CREATED)
async def create_league(
    data: LeagueCreate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    scoring = data.scoring_config or _nba_rules.default_scoring_config()
    roster = _nba_rules.default_roster_config()

    league = League(
        name=data.name,
        sport=data.sport,
        commissioner_id=agent.id,
        invite_code=generate_invite_code(),
        max_teams=data.max_teams,
        draft_date=data.draft_date,
        scoring_config=scoring,
        roster_config=roster,
    )
    db.add(league)
    await db.flush()

    # Commissioner auto-joins
    membership = LeagueMembership(league_id=league.id, agent_id=agent.id)
    db.add(membership)

    await db.commit()
    await db.refresh(league)

    return _league_response(league)


@router.get("", response_model=list[LeagueResponse])
async def list_my_leagues(
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(League)
        .join(LeagueMembership)
        .where(LeagueMembership.agent_id == agent.id)
    )
    leagues = result.scalars().all()
    return [_league_response(l) for l in leagues]


@router.get("/public", response_model=list[LeagueResponse])
async def list_public_leagues(db: AsyncSession = Depends(get_db)):
    """Return all active/playoff leagues — no auth required."""
    result = await db.execute(
        select(League).where(League.status.in_(["active", "playoffs"]))
    )
    leagues = result.scalars().all()
    return [_league_response(l) for l in leagues]


@router.get("/{league_id}", response_model=LeagueResponse)
async def get_league(league_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(League).where(League.id == league_id))
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return _league_response(league)


@router.post("/{league_id}/join", response_model=LeagueResponse)
async def join_league(
    league_id: uuid.UUID,
    data: LeagueJoin,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(League).where(League.id == league_id))
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    if league.invite_code != data.invite_code:
        raise HTTPException(status_code=403, detail="Invalid invite code")

    if league.status != "pre_season":
        raise HTTPException(status_code=400, detail="League is not accepting new members")

    # Check max teams
    if len(league.memberships) >= league.max_teams:
        raise HTTPException(status_code=400, detail="League is full")

    # Anti-collusion: no two agents from same owner
    for m in league.memberships:
        if m.agent and m.agent.owner_id == agent.owner_id:
            raise HTTPException(
                status_code=400,
                detail="You already have an agent in this league",
            )

    # Check not already a member
    existing = await db.execute(
        select(LeagueMembership).where(
            and_(
                LeagueMembership.league_id == league_id,
                LeagueMembership.agent_id == agent.id,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Agent already in this league")

    membership = LeagueMembership(league_id=league_id, agent_id=agent.id)
    db.add(membership)
    await db.commit()
    await db.refresh(league)

    return _league_response(league)


@router.get("/{league_id}/available-players", response_model=list[PlayerResponse])
async def available_players(
    league_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    from app.services.draft import get_available_players

    result = await db.execute(select(League).where(League.id == league_id))
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    players = await get_available_players(db, league_id, league.sport)
    return players


@router.post("/{league_id}/generate-season")
async def generate_season(
    league_id: uuid.UUID,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Generate scoring periods and matchups for the season (commissioner only)."""
    from app.services.matchups import generate_season as gen_season

    result = await db.execute(select(League).where(League.id == league_id))
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    if league.commissioner_id != agent.id:
        raise HTTPException(status_code=403, detail="Only the commissioner can generate the season")

    if league.status != "active":
        raise HTTPException(status_code=400, detail="League must be active (draft completed) first")

    try:
        result = await gen_season(db, league_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@router.get("/{league_id}/matchups")
async def get_matchups(
    league_id: uuid.UUID,
    week: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get matchups for a league, optionally filtered by week number."""
    from app.models.matchup import Matchup, ScoringPeriod

    query = select(ScoringPeriod).where(ScoringPeriod.league_id == league_id)
    if week is not None:
        query = query.where(ScoringPeriod.period_number == week)
    query = query.order_by(ScoringPeriod.period_number)

    result = await db.execute(query)
    periods = result.scalars().all()

    output = []
    for period in periods:
        matchups = []
        for m in period.matchups:
            matchups.append({
                "home_agent_id": str(m.home_agent_id),
                "away_agent_id": str(m.away_agent_id),
                "home_points": float(m.home_points) if m.home_points is not None else None,
                "away_points": float(m.away_points) if m.away_points is not None else None,
                "winner_agent_id": str(m.winner_agent_id) if m.winner_agent_id else None,
                "is_tie": m.is_tie,
            })
        output.append({
            "period_number": period.period_number,
            "label": period.label,
            "start_date": str(period.start_date),
            "end_date": str(period.end_date),
            "is_playoff": period.is_playoff,
            "matchups": matchups,
        })

    return output


@router.get("/{league_id}/standings", response_model=list[StandingsEntry])
async def standings(league_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await get_league_standings(db, league_id)


def _league_response(league: League) -> LeagueResponse:
    return LeagueResponse(
        id=league.id,
        name=league.name,
        sport=league.sport,
        commissioner_id=league.commissioner_id,
        invite_code=league.invite_code,
        status=league.status,
        min_teams=league.min_teams,
        max_teams=league.max_teams,
        draft_date=league.draft_date,
        season=league.season,
        member_count=len(league.memberships) if league.memberships else 0,
        created_at=league.created_at,
    )
