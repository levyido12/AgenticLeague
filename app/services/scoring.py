"""Scoring service: fetch stats, calculate fantasy points, update matchups."""

import logging
from datetime import date, datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.matchup import Matchup, ScoringPeriod
from app.models.player import Player, PlayerGameLog
from app.models.team import TeamPlayer
from app.sports.nba import NBAAdapter, NBARules

logger = logging.getLogger(__name__)

_nba_rules = NBARules()
_nba_adapter = NBAAdapter()


async def fetch_and_store_game_logs(db: AsyncSession, game_date: date) -> int:
    """Fetch NBA game logs for a date and store them. Returns count of records processed."""
    logs = await _nba_adapter.fetch_game_logs(game_date)
    count = 0

    for log in logs:
        # Find player by external_id
        result = await db.execute(
            select(Player).where(Player.external_id == log["external_player_id"])
        )
        player = result.scalar_one_or_none()
        if not player:
            continue

        # Upsert game log (keyed on player_id + game_date)
        existing = await db.execute(
            select(PlayerGameLog).where(
                and_(
                    PlayerGameLog.player_id == player.id,
                    PlayerGameLog.game_date == game_date,
                )
            )
        )
        game_log = existing.scalar_one_or_none()

        fantasy_pts = _nba_rules.calculate_fantasy_points(
            log["stats"], _nba_rules.default_scoring_config()
        )

        if game_log:
            game_log.stats = log["stats"]
            game_log.fantasy_points = fantasy_pts
        else:
            game_log = PlayerGameLog(
                player_id=player.id,
                game_date=game_date,
                season=NBAAdapter._date_to_season(game_date),
                stats=log["stats"],
                fantasy_points=fantasy_pts,
            )
            db.add(game_log)

        count += 1

    await db.commit()
    return count


async def score_matchups_for_period(db: AsyncSession, period_id) -> int:
    """Score all matchups in a scoring period. Returns number of matchups scored."""
    result = await db.execute(
        select(ScoringPeriod).where(ScoringPeriod.id == period_id)
    )
    period = result.scalar_one_or_none()
    if not period:
        return 0

    # Get all matchups for this period
    matchup_result = await db.execute(
        select(Matchup).where(Matchup.scoring_period_id == period_id)
    )
    matchups = matchup_result.scalars().all()

    count = 0
    for matchup in matchups:
        home_pts = await _calculate_team_points(
            db, matchup.home_agent_id, period.league_id,
            period.start_date, period.end_date
        )
        away_pts = await _calculate_team_points(
            db, matchup.away_agent_id, period.league_id,
            period.start_date, period.end_date
        )

        matchup.home_points = home_pts
        matchup.away_points = away_pts

        if home_pts > away_pts:
            matchup.winner_agent_id = matchup.home_agent_id
            matchup.is_tie = False
        elif away_pts > home_pts:
            matchup.winner_agent_id = matchup.away_agent_id
            matchup.is_tie = False
        else:
            # Tie-breaker: highest single player score
            matchup.is_tie = True
            matchup.winner_agent_id = None

        count += 1

    await db.commit()
    return count


async def _calculate_team_points(
    db: AsyncSession,
    agent_id,
    league_id,
    start_date: date,
    end_date: date,
) -> float:
    """Sum fantasy points for an agent's starters over a scoring period."""
    from app.models.league import LeagueMembership
    from app.models.team import Team

    # Get the team for this agent in this league
    membership_result = await db.execute(
        select(LeagueMembership).where(
            and_(
                LeagueMembership.agent_id == agent_id,
                LeagueMembership.league_id == league_id,
            )
        )
    )
    membership = membership_result.scalar_one_or_none()
    if not membership or not membership.team:
        return 0.0

    team = membership.team

    # Get starter player IDs
    tp_result = await db.execute(
        select(TeamPlayer).where(
            and_(TeamPlayer.team_id == team.id, TeamPlayer.is_starter == True)
        )
    )
    team_players = tp_result.scalars().all()
    player_ids = [tp.player_id for tp in team_players]

    if not player_ids:
        return 0.0

    # Sum fantasy points for those players in the date range
    logs_result = await db.execute(
        select(PlayerGameLog).where(
            and_(
                PlayerGameLog.player_id.in_(player_ids),
                PlayerGameLog.game_date >= start_date,
                PlayerGameLog.game_date <= end_date,
            )
        )
    )
    logs = logs_result.scalars().all()

    return sum(float(log.fantasy_points or 0) for log in logs)
