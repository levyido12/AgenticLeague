"""Matchup generation: create scoring periods and weekly head-to-head pairings."""

import random
import uuid
from itertools import combinations

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.league import League, LeagueMembership
from app.models.matchup import Matchup, ScoringPeriod
from app.sports.nba import NBASchedule


async def generate_season(db: AsyncSession, league_id: uuid.UUID) -> dict:
    """Generate all scoring periods and matchups for a league's season.

    Uses a round-robin schedule so every agent plays every other agent,
    then repeats. Each week, agents are paired for head-to-head matchups.
    """
    # Get league
    result = await db.execute(select(League).where(League.id == league_id))
    league = result.scalar_one_or_none()
    if not league:
        raise ValueError("League not found")

    # Check if scoring periods already exist
    existing = await db.execute(
        select(ScoringPeriod).where(ScoringPeriod.league_id == league_id)
    )
    if existing.scalars().first():
        raise ValueError("Season already generated for this league")

    # Get members
    members_result = await db.execute(
        select(LeagueMembership).where(LeagueMembership.league_id == league_id)
    )
    members = members_result.scalars().all()
    agent_ids = [m.agent_id for m in members]
    num_teams = len(agent_ids)

    if num_teams < 2:
        raise ValueError("Need at least 2 teams")

    # Generate scoring periods from NBA schedule
    schedule = NBASchedule(league.season)
    periods_data = schedule.generate_scoring_periods(league.season)

    if not periods_data:
        raise ValueError("No scoring periods generated for this season")

    # Generate round-robin matchup rotation
    matchup_rounds = _generate_round_robin(agent_ids)

    # Create scoring periods and matchups
    periods_created = 0
    matchups_created = 0

    for p_data in periods_data:
        period = ScoringPeriod(
            league_id=league_id,
            period_number=p_data["period_number"],
            label=p_data["label"],
            start_date=p_data["start_date"],
            end_date=p_data["end_date"],
            is_playoff=p_data["is_playoff"],
        )
        db.add(period)
        await db.flush()  # Get the period ID

        # Pick the matchup round for this week (cycle through rounds)
        round_index = (p_data["period_number"] - 1) % len(matchup_rounds)
        week_matchups = matchup_rounds[round_index]

        for home_id, away_id in week_matchups:
            matchup = Matchup(
                scoring_period_id=period.id,
                home_agent_id=home_id,
                away_agent_id=away_id,
            )
            db.add(matchup)
            matchups_created += 1

        periods_created += 1

    await db.commit()

    return {
        "league_id": str(league_id),
        "periods_created": periods_created,
        "matchups_created": matchups_created,
        "first_week": str(periods_data[0]["start_date"]),
        "last_week": str(periods_data[-1]["end_date"]),
    }


def _generate_round_robin(agent_ids: list[uuid.UUID]) -> list[list[tuple]]:
    """Generate round-robin matchup rounds.

    If odd number of teams, one team gets a bye each round.
    Returns list of rounds, each round is a list of (home, away) tuples.
    """
    ids = list(agent_ids)
    random.shuffle(ids)

    # If odd number of teams, add a "bye" placeholder
    if len(ids) % 2 == 1:
        ids.append(None)

    n = len(ids)
    rounds = []

    # Standard round-robin algorithm: fix first team, rotate the rest
    for round_num in range(n - 1):
        round_matchups = []
        for i in range(n // 2):
            home = ids[i]
            away = ids[n - 1 - i]
            # Skip if either is a bye
            if home is not None and away is not None:
                round_matchups.append((home, away))
        rounds.append(round_matchups)

        # Rotate: keep ids[0] fixed, rotate the rest
        ids = [ids[0]] + [ids[-1]] + ids[1:-1]

    return rounds
