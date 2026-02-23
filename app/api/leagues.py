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
