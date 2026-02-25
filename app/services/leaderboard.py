"""Leaderboard service: league standings and global rankings."""

import uuid
from collections import defaultdict

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.league import LeagueMembership
from app.models.matchup import Matchup, ScoringPeriod
from app.models.player import Player
from app.models.team import Team, TeamPlayer
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

    # Ensure all members are in the records
    records: dict[uuid.UUID, dict] = defaultdict(
        lambda: {"wins": 0, "losses": 0, "ties": 0, "points_for": 0.0, "points_against": 0.0}
    )

    # Seed all league members
    members_result = await db.execute(
        select(LeagueMembership).where(LeagueMembership.league_id == league_id)
    )
    members = members_result.scalars().all()
    for m in members:
        _ = records[m.agent_id]  # ensure entry exists

    # Tally wins/losses/ties and points
    for m in matchups:
        if m.home_points is not None:
            records[m.home_agent_id]["points_for"] += float(m.home_points)
            records[m.away_agent_id]["points_against"] += float(m.home_points)
        if m.away_points is not None:
            records[m.away_agent_id]["points_for"] += float(m.away_points)
            records[m.home_agent_id]["points_against"] += float(m.away_points)

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

    # Sort by wins desc, then points_for desc
    sorted_ids = sorted(
        records.keys(),
        key=lambda aid: (records[aid]["wins"], records[aid]["points_for"]),
        reverse=True,
    )

    entries = []
    for rank, aid in enumerate(sorted_ids, 1):
        r = records[aid]
        agent = agents.get(aid)
        pf = round(r["points_for"], 2)
        entries.append(StandingsEntry(
            agent_id=aid,
            agent_name=agent.name if agent else "Unknown",
            wins=r["wins"],
            losses=r["losses"],
            ties=r["ties"],
            total_points=pf,
            points_for=pf,
            points_against=round(r["points_against"], 2),
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
    agent_records: dict[uuid.UUID, dict] = defaultdict(
        lambda: {"wins": 0, "losses": 0, "ties": 0}
    )

    for m in matchups:
        if m.home_points is not None:
            agent_points[m.home_agent_id] += float(m.home_points)
        if m.away_points is not None:
            agent_points[m.away_agent_id] += float(m.away_points)

        if m.winner_agent_id:
            agent_records[m.winner_agent_id]["wins"] += 1
            loser = m.away_agent_id if m.winner_agent_id == m.home_agent_id else m.home_agent_id
            agent_records[loser]["losses"] += 1
        elif m.is_tie:
            agent_records[m.home_agent_id]["ties"] += 1
            agent_records[m.away_agent_id]["ties"] += 1

    # Count leagues per agent
    memberships_result = await db.execute(select(LeagueMembership))
    memberships = memberships_result.scalars().all()
    membership_ids = []
    for mem in memberships:
        agent_leagues[mem.agent_id].add(mem.league_id)
        membership_ids.append(mem.id)

    # Include all agents that are in at least one league
    agent_ids = list(set(agent_points.keys()) | set(agent_leagues.keys()))
    # Also include agents in leagues that haven't played yet
    all_member_agent_ids = {mem.agent_id for mem in memberships}
    agent_ids = list(set(agent_ids) | all_member_agent_ids)
    if not agent_ids:
        return []

    agents_result = await db.execute(select(Agent).where(Agent.id.in_(agent_ids)))
    agents = {a.id: a for a in agents_result.scalars().all()}

    owner_ids = {a.owner_id for a in agents.values()}
    users_result = await db.execute(select(User).where(User.id.in_(owner_ids)))
    users = {u.id: u for u in users_result.scalars().all()}

    # Get top 3 players per agent (from their team rosters)
    agent_top_players: dict[uuid.UUID, list[str]] = defaultdict(list)
    if membership_ids:
        teams_result = await db.execute(
            select(Team).where(Team.membership_id.in_(membership_ids))
        )
        teams = teams_result.scalars().all()

        # Map membership_id -> agent_id
        mem_to_agent = {mem.id: mem.agent_id for mem in memberships}

        for team in teams:
            agent_id = mem_to_agent.get(team.membership_id)
            if not agent_id or not team.players:
                continue

            # Get player IDs from the team
            player_ids = [tp.player_id for tp in team.players if tp.is_starter]
            if not player_ids:
                player_ids = [tp.player_id for tp in team.players]

            players_result = await db.execute(
                select(Player).where(Player.id.in_(player_ids[:5]))
            )
            players = players_result.scalars().all()

            # Sort by season stats points if available, take top 3
            sorted_players = sorted(
                players,
                key=lambda p: p.season_stats.get("pts", 0) if p.season_stats else 0,
                reverse=True,
            )
            agent_top_players[agent_id] = [p.full_name for p in sorted_players[:3]]

    sorted_ids = sorted(agent_ids, key=lambda aid: agent_points.get(aid, 0), reverse=True)

    entries = []
    for rank, aid in enumerate(sorted_ids, 1):
        agent = agents.get(aid)
        if not agent:
            continue
        owner = users.get(agent.owner_id)
        rec = agent_records[aid]
        entries.append(LeaderboardEntry(
            agent_id=aid,
            agent_name=agent.name,
            owner_username=owner.username if owner else "Unknown",
            total_fantasy_points=round(agent_points.get(aid, 0), 2),
            leagues_count=len(agent_leagues.get(aid, set())),
            rank=rank,
            wins=rec["wins"],
            losses=rec["losses"],
            ties=rec["ties"],
            top_players=agent_top_players.get(aid, []),
        ))

    return entries
