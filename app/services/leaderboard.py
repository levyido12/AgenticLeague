"""Leaderboard service: league standings and global rankings (total points model)."""

import uuid
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.league import League, LeagueMembership
from app.models.player import Player, PlayerGameLog
from app.models.team import Team, TeamPlayer
from app.models.user import User
from app.schemas.leagues import StandingsEntry
from app.schemas.players import LeaderboardEntry


async def get_league_standings(
    db: AsyncSession, league_id: uuid.UUID
) -> list[StandingsEntry]:
    """Calculate standings for a league based on total fantasy points from PlayerGameLog."""
    # Get league to know the season
    league_result = await db.execute(select(League).where(League.id == league_id))
    league = league_result.scalar_one_or_none()
    if not league:
        return []

    # Get all members
    members_result = await db.execute(
        select(LeagueMembership).where(LeagueMembership.league_id == league_id)
    )
    members = members_result.scalars().all()

    if not members:
        return []

    # For each member, sum fantasy_points from PlayerGameLog for their starters
    agent_points: dict[uuid.UUID, float] = {}

    for member in members:
        team = member.team
        if not team or not team.players:
            agent_points[member.agent_id] = 0.0
            continue

        starter_player_ids = [tp.player_id for tp in team.players if tp.is_starter]
        if not starter_player_ids:
            agent_points[member.agent_id] = 0.0
            continue

        points_result = await db.execute(
            select(func.coalesce(func.sum(PlayerGameLog.fantasy_points), 0)).where(
                PlayerGameLog.player_id.in_(starter_player_ids),
                PlayerGameLog.season == league.season,
            )
        )
        total = float(points_result.scalar())
        agent_points[member.agent_id] = total

    # Get agent names
    agent_ids = list(agent_points.keys())
    agents_result = await db.execute(select(Agent).where(Agent.id.in_(agent_ids)))
    agents = {a.id: a for a in agents_result.scalars().all()}

    # Sort by total points DESC
    sorted_ids = sorted(agent_ids, key=lambda aid: agent_points[aid], reverse=True)

    entries = []
    for rank, aid in enumerate(sorted_ids, 1):
        agent = agents.get(aid)
        pts = round(agent_points[aid], 2)
        entries.append(StandingsEntry(
            agent_id=aid,
            agent_name=agent.name if agent else "Unknown",
            wins=0,
            losses=0,
            ties=0,
            total_points=pts,
            rank=rank,
        ))

    return entries


async def get_platform_stats(db: AsyncSession) -> dict:
    """Return lightweight aggregate stats (agent count, total points, league count)."""
    # Count distinct agents in any league
    agent_count_result = await db.execute(
        select(func.count(func.distinct(LeagueMembership.agent_id)))
    )
    agent_count = agent_count_result.scalar() or 0

    # Total fantasy points across all game logs
    points_result = await db.execute(
        select(func.coalesce(func.sum(PlayerGameLog.fantasy_points), 0))
    )
    total_fantasy_points = round(float(points_result.scalar()), 2)

    # Count active leagues
    league_count_result = await db.execute(select(func.count(League.id)))
    league_count = league_count_result.scalar() or 0

    return {
        "agent_count": agent_count,
        "total_fantasy_points": total_fantasy_points,
        "league_count": league_count,
    }


async def get_global_leaderboard(db: AsyncSession) -> list[LeaderboardEntry]:
    """Global leaderboard: total fantasy points from PlayerGameLog across all leagues."""
    # Get all memberships
    memberships_result = await db.execute(select(LeagueMembership))
    memberships = memberships_result.scalars().all()

    if not memberships:
        return []

    agent_points: dict[uuid.UUID, float] = defaultdict(float)
    agent_leagues: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)

    for mem in memberships:
        agent_leagues[mem.agent_id].add(mem.league_id)

        team = mem.team
        if not team or not team.players:
            continue

        starter_player_ids = [tp.player_id for tp in team.players if tp.is_starter]
        if not starter_player_ids:
            continue

        # Get league season
        league = mem.league
        season = league.season if league else "2025-26"

        points_result = await db.execute(
            select(func.coalesce(func.sum(PlayerGameLog.fantasy_points), 0)).where(
                PlayerGameLog.player_id.in_(starter_player_ids),
                PlayerGameLog.season == season,
            )
        )
        agent_points[mem.agent_id] += float(points_result.scalar())

    # All agents in at least one league
    agent_ids = list(set(agent_leagues.keys()))
    if not agent_ids:
        return []

    agents_result = await db.execute(select(Agent).where(Agent.id.in_(agent_ids)))
    agents = {a.id: a for a in agents_result.scalars().all()}

    owner_ids = {a.owner_id for a in agents.values()}
    users_result = await db.execute(select(User).where(User.id.in_(owner_ids)))
    users = {u.id: u for u in users_result.scalars().all()}

    # Get top 3 players per agent
    agent_top_players: dict[uuid.UUID, list[str]] = defaultdict(list)
    for mem in memberships:
        team = mem.team
        if not team or not team.players:
            continue

        player_ids = [tp.player_id for tp in team.players if tp.is_starter]
        if not player_ids:
            player_ids = [tp.player_id for tp in team.players]

        players_result = await db.execute(
            select(Player).where(Player.id.in_(player_ids[:5]))
        )
        players = players_result.scalars().all()

        sorted_players = sorted(
            players,
            key=lambda p: p.season_stats.get("pts", 0) if p.season_stats else 0,
            reverse=True,
        )
        # Only set if not already populated (first league wins)
        if not agent_top_players[mem.agent_id]:
            agent_top_players[mem.agent_id] = [p.full_name for p in sorted_players[:3]]

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
            wins=0,
            losses=0,
            ties=0,
            top_players=agent_top_players.get(aid, []),
        ))

    return entries
