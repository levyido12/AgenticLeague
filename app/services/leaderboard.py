"""Leaderboard service: league standings and global rankings."""

import uuid
from collections import defaultdict

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.league import LeagueMembership
from app.models.matchup import Matchup, ScoringPeriod
from app.models.user import User
from app.schemas.leagues import StandingsEntry
from app.schemas.players import LeaderboardEntry


async def get_league_standings(
    db: AsyncSession, league_id: uuid.UUID
) -> list[StandingsEntry]:
    """Calculate standings for a league based on matchup results."""
    # Get all scoring periods for this league
    periods_result = await db.execute(
        select(ScoringPeriod).where(ScoringPeriod.league_id == league_id)
    )
    periods = periods_result.scalars().all()
    period_ids = [p.id for p in periods]

    if not period_ids:
        # No matchups yet — return members with zero records
        members_result = await db.execute(
            select(LeagueMembership).where(LeagueMembership.league_id == league_id)
        )
        members = members_result.scalars().all()
        entries = []
        for i, m in enumerate(members):
            agent = m.agent
            entries.append(StandingsEntry(
                agent_id=m.agent_id,
                agent_name=agent.name if agent else "Unknown",
                wins=0, losses=0, ties=0, total_points=0.0, rank=i + 1,
            ))
        return entries

    # Get all matchups
    matchups_result = await db.execute(
        select(Matchup).where(Matchup.scoring_period_id.in_(period_ids))
    )
    matchups = matchups_result.scalars().all()

    # Tally wins/losses/ties and points
    records: dict[uuid.UUID, dict] = defaultdict(
        lambda: {"wins": 0, "losses": 0, "ties": 0, "total_points": 0.0}
    )

    for m in matchups:
        if m.home_points is not None:
            records[m.home_agent_id]["total_points"] += float(m.home_points)
        if m.away_points is not None:
            records[m.away_agent_id]["total_points"] += float(m.away_points)

        if m.winner_agent_id:
            records[m.winner_agent_id]["wins"] += 1
            loser = m.away_agent_id if m.winner_agent_id == m.home_agent_id else m.home_agent_id
            records[loser]["losses"] += 1
        elif m.is_tie:
            records[m.home_agent_id]["ties"] += 1
            records[m.away_agent_id]["ties"] += 1

    # Get agent names
    agent_ids = list(records.keys())
    agents_result = await db.execute(select(Agent).where(Agent.id.in_(agent_ids)))
    agents = {a.id: a for a in agents_result.scalars().all()}

    # Sort by wins desc, then total_points desc
    sorted_ids = sorted(
        records.keys(),
        key=lambda aid: (records[aid]["wins"], records[aid]["total_points"]),
        reverse=True,
    )

    entries = []
    for rank, aid in enumerate(sorted_ids, 1):
        r = records[aid]
        agent = agents.get(aid)
        entries.append(StandingsEntry(
            agent_id=aid,
            agent_name=agent.name if agent else "Unknown",
            wins=r["wins"],
            losses=r["losses"],
            ties=r["ties"],
            total_points=round(r["total_points"], 2),
            rank=rank,
        ))

    return entries


async def get_global_leaderboard(db: AsyncSession) -> list[LeaderboardEntry]:
    """Global leaderboard: total fantasy points across all leagues."""
    # Get all matchups with points
    matchups_result = await db.execute(select(Matchup))
    matchups = matchups_result.scalars().all()

    agent_points: dict[uuid.UUID, float] = defaultdict(float)
    agent_leagues: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)

    for m in matchups:
        if m.home_points is not None:
            agent_points[m.home_agent_id] += float(m.home_points)
        if m.away_points is not None:
            agent_points[m.away_agent_id] += float(m.away_points)

    # Count leagues per agent
    memberships_result = await db.execute(select(LeagueMembership))
    for mem in memberships_result.scalars().all():
        agent_leagues[mem.agent_id].add(mem.league_id)

    # Get agent details with owners
    agent_ids = list(set(agent_points.keys()) | set(agent_leagues.keys()))
    if not agent_ids:
        return []

    agents_result = await db.execute(select(Agent).where(Agent.id.in_(agent_ids)))
    agents = {a.id: a for a in agents_result.scalars().all()}

    owner_ids = {a.owner_id for a in agents.values()}
    users_result = await db.execute(select(User).where(User.id.in_(owner_ids)))
    users = {u.id: u for u in users_result.scalars().all()}

    sorted_ids = sorted(agent_ids, key=lambda aid: agent_points.get(aid, 0), reverse=True)

    entries = []
    for rank, aid in enumerate(sorted_ids, 1):
        agent = agents.get(aid)
        if not agent:
            continue
        owner = users.get(agent.owner_id)
        entries.append(LeaderboardEntry(
            agent_id=aid,
            agent_name=agent.name,
            owner_username=owner.username if owner else "Unknown",
            total_fantasy_points=round(agent_points.get(aid, 0), 2),
            leagues_count=len(agent_leagues.get(aid, set())),
            rank=rank,
        ))

    return entries
