"""Draft service: snake draft logic with auto-pick fallback."""

import json
import random
import uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.draft import DraftPick, DraftState
from app.models.league import League, LeagueMembership
from app.models.player import Player
from app.models.team import Team, TeamPlayer
from app.sports.nba import NBARules

_nba_rules = NBARules()


async def initialize_draft(db: AsyncSession, league_id: uuid.UUID) -> DraftState:
    """Create a draft state with randomized snake order."""
    # Get league members
    result = await db.execute(
        select(LeagueMembership).where(LeagueMembership.league_id == league_id)
    )
    members = result.scalars().all()
    agent_ids = [str(m.agent_id) for m in members]
    random.shuffle(agent_ids)

    roster_size = _nba_rules.default_roster_config()["total_roster_size"]
    num_teams = len(agent_ids)
    total_picks = num_teams * roster_size

    # Generate snake draft order
    snake_order = []
    for round_num in range(roster_size):
        if round_num % 2 == 0:
            snake_order.extend(agent_ids)
        else:
            snake_order.extend(reversed(agent_ids))

    draft_state = DraftState(
        league_id=league_id,
        current_pick=1,
        total_picks=total_picks,
        status="in_progress",
        draft_order=json.dumps(snake_order),
    )
    db.add(draft_state)

    # Update league status
    league_result = await db.execute(select(League).where(League.id == league_id))
    league = league_result.scalar_one()
    league.status = "drafting"

    # Create teams for each member
    for member in members:
        existing_team = await db.execute(
            select(Team).where(Team.membership_id == member.id)
        )
        if not existing_team.scalar_one_or_none():
            db.add(Team(membership_id=member.id))

    await db.commit()
    await db.refresh(draft_state)
    return draft_state


async def make_pick(
    db: AsyncSession,
    league_id: uuid.UUID,
    agent_id: uuid.UUID,
    player_id: uuid.UUID,
    is_auto: bool = False,
) -> DraftPick:
    """Make a draft pick. Validates it's the agent's turn and player is available."""
    # Get draft state
    result = await db.execute(
        select(DraftState).where(DraftState.league_id == league_id)
    )
    draft_state = result.scalar_one_or_none()
    if not draft_state or draft_state.status != "in_progress":
        raise ValueError("Draft is not in progress")

    order = json.loads(draft_state.draft_order)
    current_agent = order[draft_state.current_pick - 1]

    if str(agent_id) != current_agent:
        raise ValueError("It's not your turn to pick")

    # Check player not already drafted
    existing = await db.execute(
        select(DraftPick).where(
            and_(DraftPick.league_id == league_id, DraftPick.player_id == player_id)
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError("Player already drafted")

    # Determine round number
    num_teams = len(set(order))
    round_number = ((draft_state.current_pick - 1) // num_teams) + 1

    # Create pick
    pick = DraftPick(
        league_id=league_id,
        agent_id=agent_id,
        player_id=player_id,
        pick_number=draft_state.current_pick,
        round_number=round_number,
        is_auto_pick=is_auto,
    )
    db.add(pick)

    # Add player to team
    membership_result = await db.execute(
        select(LeagueMembership).where(
            and_(
                LeagueMembership.league_id == league_id,
                LeagueMembership.agent_id == agent_id,
            )
        )
    )
    membership = membership_result.scalar_one()
    team_result = await db.execute(
        select(Team).where(Team.membership_id == membership.id)
    )
    team = team_result.scalar_one()

    # Assign roster slot
    roster_config = _nba_rules.default_roster_config()
    starter_slots = roster_config["starter_slots"]
    current_players = await db.execute(
        select(TeamPlayer).where(TeamPlayer.team_id == team.id)
    )
    current_count = len(current_players.scalars().all())

    if current_count < len(starter_slots):
        slot = starter_slots[current_count]
        is_starter = True
    else:
        slot = "BN"
        is_starter = False

    db.add(TeamPlayer(
        team_id=team.id,
        player_id=player_id,
        roster_slot=slot,
        is_starter=is_starter,
    ))

    # Advance draft
    draft_state.current_pick += 1
    if draft_state.current_pick > draft_state.total_picks:
        draft_state.status = "completed"
        # Update league status
        league_result = await db.execute(select(League).where(League.id == league_id))
        league = league_result.scalar_one()
        league.status = "active"

    await db.commit()

    # Auto-generate season schedule when draft completes
    if draft_state.status == "completed":
        try:
            from app.services.matchups import generate_season
            await generate_season(db, league_id)
        except Exception:
            pass  # Don't break the draft if season generation fails
    await db.refresh(pick)
    return pick


async def get_draft_state(db: AsyncSession, league_id: uuid.UUID) -> DraftState | None:
    result = await db.execute(
        select(DraftState).where(DraftState.league_id == league_id)
    )
    return result.scalar_one_or_none()


async def get_available_players(
    db: AsyncSession, league_id: uuid.UUID, sport: str = "nba"
) -> list[Player]:
    """Get players not yet drafted in this league."""
    drafted = select(DraftPick.player_id).where(DraftPick.league_id == league_id)
    result = await db.execute(
        select(Player).where(
            and_(Player.sport == sport, Player.id.notin_(drafted))
        )
    )
    return result.scalars().all()
