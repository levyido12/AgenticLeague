"""Waiver claim and free agent pickup service."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.league import LeagueMembership
from app.models.player import Player
from app.models.team import Team, TeamPlayer
from app.models.waiver import WaiverClaim


async def create_waiver_claim(
    db: AsyncSession,
    league_id: uuid.UUID,
    agent_id: uuid.UUID,
    player_id: uuid.UUID,
    drop_player_id: uuid.UUID | None = None,
) -> WaiverClaim:
    """Place a waiver claim on a player."""
    # Check player is on waivers (dropped within last 48 hours)
    # For simplicity, any unrostered player can be claimed via waivers

    # Calculate priority (inverse of standings — lower standing = higher priority)
    # For v1, use creation order as priority proxy
    existing_claims = await db.execute(
        select(WaiverClaim).where(
            and_(
                WaiverClaim.league_id == league_id,
                WaiverClaim.player_id == player_id,
                WaiverClaim.status == "pending",
            )
        )
    )
    priority = len(existing_claims.scalars().all()) + 1

    claim = WaiverClaim(
        league_id=league_id,
        agent_id=agent_id,
        player_id=player_id,
        drop_player_id=drop_player_id,
        priority=priority,
        status="pending",
        waiver_expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
    )
    db.add(claim)
    await db.commit()
    await db.refresh(claim)
    return claim


async def process_expired_waivers(db: AsyncSession, league_id: uuid.UUID) -> int:
    """Process all expired waiver claims for a league. Returns number processed."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(WaiverClaim)
        .where(
            and_(
                WaiverClaim.league_id == league_id,
                WaiverClaim.status == "pending",
                WaiverClaim.waiver_expires_at <= now,
            )
        )
        .order_by(WaiverClaim.priority.asc())
    )
    claims = result.scalars().all()

    processed = 0
    for claim in claims:
        # Check if player is still available (optimistic locking)
        player_on_team = await db.execute(
            select(TeamPlayer).where(TeamPlayer.player_id == claim.player_id)
        )
        if player_on_team.scalar_one_or_none():
            claim.status = "denied"
            processed += 1
            continue

        # Add player to agent's team
        success = await _add_player_to_team(
            db, claim.league_id, claim.agent_id, claim.player_id, claim.drop_player_id
        )
        claim.status = "approved" if success else "denied"
        processed += 1

    await db.commit()
    return processed


async def pickup_free_agent(
    db: AsyncSession,
    league_id: uuid.UUID,
    agent_id: uuid.UUID,
    player_id: uuid.UUID,
    drop_player_id: uuid.UUID | None = None,
) -> bool:
    """Pick up a free agent (not on waivers). First-come-first-served."""
    # Check no pending waiver claims
    waiver_result = await db.execute(
        select(WaiverClaim).where(
            and_(
                WaiverClaim.league_id == league_id,
                WaiverClaim.player_id == player_id,
                WaiverClaim.status == "pending",
            )
        )
    )
    if waiver_result.scalar_one_or_none():
        raise ValueError("Player is on waivers")

    return await _add_player_to_team(db, league_id, agent_id, player_id, drop_player_id)


async def _add_player_to_team(
    db: AsyncSession,
    league_id: uuid.UUID,
    agent_id: uuid.UUID,
    player_id: uuid.UUID,
    drop_player_id: uuid.UUID | None,
) -> bool:
    """Add a player to an agent's team, optionally dropping another."""
    membership_result = await db.execute(
        select(LeagueMembership).where(
            and_(
                LeagueMembership.league_id == league_id,
                LeagueMembership.agent_id == agent_id,
            )
        )
    )
    membership = membership_result.scalar_one_or_none()
    if not membership or not membership.team:
        return False

    team = membership.team

    # Drop player if specified
    if drop_player_id:
        await db.execute(
            select(TeamPlayer).where(
                and_(
                    TeamPlayer.team_id == team.id,
                    TeamPlayer.player_id == drop_player_id,
                )
            )
        )
        drop_result = await db.execute(
            select(TeamPlayer).where(
                and_(
                    TeamPlayer.team_id == team.id,
                    TeamPlayer.player_id == drop_player_id,
                )
            )
        )
        drop_tp = drop_result.scalar_one_or_none()
        if drop_tp:
            await db.delete(drop_tp)

    # Add new player to bench
    db.add(TeamPlayer(
        team_id=team.id,
        player_id=player_id,
        roster_slot="BN",
        is_starter=False,
    ))

    await db.commit()
    return True
