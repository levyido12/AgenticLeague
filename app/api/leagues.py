"""League management endpoints."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_agent
from app.models.agent import Agent
from app.models.league import League, LeagueMembership
from app.models.matchup import Matchup, ScoringPeriod
from app.models.player import Player
from app.models.team import Team, TeamPlayer
from app.schemas.leagues import LeagueCreate, LeagueJoin, LeagueResponse, StandingsEntry
from app.schemas.players import PlayerResponse
from app.services.auth import generate_invite_code
from app.services.leaderboard import get_league_standings
from app.sports.nba import NBARules, NBASchedule

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
        min_teams=data.min_teams,
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
    """Return all active/playoff/joinable leagues — no auth required."""
    result = await db.execute(
        select(League).where(League.status.in_(["active", "playoffs", "pre_season"]))
    )
    leagues = result.scalars().all()
    # Filter pre_season leagues to only show those with available spots
    visible = [
        l for l in leagues
        if l.status != "pre_season" or len(l.memberships) < l.max_teams
    ]
    return [_league_response(l) for l in visible]


@router.get("/public/matchups")
async def public_matchups(db: AsyncSession = Depends(get_db)):
    """Current week matchups across all active/playoff leagues. No auth required."""
    # Find active/playoff leagues
    leagues_result = await db.execute(
        select(League).where(League.status.in_(["active", "playoffs"]))
    )
    leagues = leagues_result.scalars().all()

    if not leagues:
        return []

    league_ids = [l.id for l in leagues]

    # Get current week's scoring periods
    today = date.today()
    periods_result = await db.execute(
        select(ScoringPeriod).where(
            and_(
                ScoringPeriod.league_id.in_(league_ids),
                ScoringPeriod.start_date <= today,
                ScoringPeriod.end_date >= today,
            )
        )
    )
    periods = periods_result.scalars().all()

    if not periods:
        # Fall back to most recent periods
        periods_result = await db.execute(
            select(ScoringPeriod)
            .where(ScoringPeriod.league_id.in_(league_ids))
            .order_by(ScoringPeriod.end_date.desc())
            .limit(len(league_ids))
        )
        periods = periods_result.scalars().all()

    # Get agent names for display
    agent_ids = set()
    for period in periods:
        for m in period.matchups:
            agent_ids.add(m.home_agent_id)
            agent_ids.add(m.away_agent_id)

    agents_result = await db.execute(
        select(Agent).where(Agent.id.in_(list(agent_ids)))
    )
    agents_map = {a.id: a.name for a in agents_result.scalars().all()}

    # Get league names
    league_map = {l.id: l.name for l in leagues}

    output = []
    for period in periods:
        for m in period.matchups:
            output.append({
                "league_name": league_map.get(period.league_id, "Unknown"),
                "week_label": period.label,
                "home_agent_name": agents_map.get(m.home_agent_id, "Unknown"),
                "away_agent_name": agents_map.get(m.away_agent_id, "Unknown"),
                "home_points": float(m.home_points) if m.home_points is not None else None,
                "away_points": float(m.away_points) if m.away_points is not None else None,
                "winner_agent_name": agents_map.get(m.winner_agent_id) if m.winner_agent_id else None,
                "is_tie": m.is_tie,
            })

    return output


@router.post("/auto-join", response_model=LeagueResponse, status_code=status.HTTP_200_OK)
async def auto_join_league(
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """One-call onboarding: find or create a league and join automatically."""
    # Get IDs of leagues where agent's owner already has a member (anti-collusion)
    owner_league_ids_q = (
        select(LeagueMembership.league_id)
        .join(Agent, LeagueMembership.agent_id == Agent.id)
        .where(Agent.owner_id == agent.owner_id)
    )

    # Find pre_season leagues with available spots, prefer most-filled
    result = await db.execute(
        select(League)
        .where(
            and_(
                League.status == "pre_season",
                League.id.notin_(owner_league_ids_q),
            )
        )
    )
    candidates = result.scalars().all()

    # Filter to leagues with available spots, sort by most-filled first
    league = None
    candidates_with_spots = [
        l for l in candidates
        if len(l.memberships) < l.max_teams
    ]
    candidates_with_spots.sort(
        key=lambda l: len(l.memberships), reverse=True
    )

    if candidates_with_spots:
        league = candidates_with_spots[0]
    else:
        # Auto-create a new league
        scoring = _nba_rules.default_scoring_config()
        roster = _nba_rules.default_roster_config()
        league = League(
            name="Open NBA League",
            sport="nba",
            commissioner_id=agent.id,
            invite_code=generate_invite_code(),
            min_teams=2,
            max_teams=6,
            scoring_config=scoring,
            roster_config=roster,
        )
        db.add(league)
        await db.flush()

    # Check agent not already in this league
    existing = await db.execute(
        select(LeagueMembership).where(
            and_(
                LeagueMembership.league_id == league.id,
                LeagueMembership.agent_id == agent.id,
            )
        )
    )
    if existing.scalar_one_or_none():
        # Already a member — just return the league
        await db.refresh(league)
        return _league_response(league)

    membership = LeagueMembership(league_id=league.id, agent_id=agent.id)
    db.add(membership)
    await db.commit()
    await db.refresh(league)

    return _league_response(league)


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


@router.get("/{league_id}/team")
async def get_my_team(
    league_id: uuid.UUID,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Get your roster for a specific league."""
    membership_result = await db.execute(
        select(LeagueMembership).where(
            and_(
                LeagueMembership.league_id == league_id,
                LeagueMembership.agent_id == agent.id,
            )
        )
    )
    membership = membership_result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=404, detail="You are not in this league")

    team_result = await db.execute(
        select(Team).where(Team.membership_id == membership.id)
    )
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="No team found")

    # Get players with their info
    roster = []
    for tp in team.players:
        player_result = await db.execute(
            select(Player).where(Player.id == tp.player_id)
        )
        player = player_result.scalar_one_or_none()
        if player:
            roster.append({
                "player_id": str(player.id),
                "full_name": player.full_name,
                "position": player.position,
                "nba_team": player.nba_team,
                "roster_slot": tp.roster_slot,
                "is_starter": tp.is_starter,
            })

    return {
        "team_id": str(team.id),
        "league_id": str(league_id),
        "agent_id": str(agent.id),
        "roster": roster,
    }


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

    member_ids = {m.agent_id for m in league.memberships}
    if agent.id not in member_ids:
        raise HTTPException(status_code=403, detail="Only league members can generate the season")

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
    count = len(league.memberships) if league.memberships else 0
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
        member_count=count,
        current_members=count,
        created_at=league.created_at,
    )
