"""Agent management endpoints."""

import uuid as uuid_mod
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_agent, get_current_user
from app.models.agent import Agent
from app.models.league import LeagueMembership
from app.models.player import PlayerGameLog
from app.models.team import Team, TeamPlayer
from app.models.user import User
from app.schemas.agents import AgentCreate, AgentCreateResponse, AgentDirectoryEntry, AgentMeResponse, AgentRegister, AgentResponse, LeagueInfo
from app.services.auth import generate_api_key, hash_api_key, hash_password

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/register", response_model=AgentCreateResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(
    data: AgentRegister,
    db: AsyncSession = Depends(get_db),
):
    """Self-registration for agents — no auth required.

    Creates a shadow user and an agent in one call, returning the API key (shown once).
    """
    owner_name = data.owner_name or data.agent_name
    # Shadow username must be unique — append short random suffix
    shadow_username = f"{owner_name}_{uuid_mod.uuid4().hex[:8]}"
    random_email = f"{uuid_mod.uuid4()}@agent.local"
    random_password = generate_api_key()  # never exposed

    user = User(
        username=shadow_username,
        email=random_email,
        hashed_password=hash_password(random_password),
    )
    db.add(user)

    raw_key = generate_api_key()
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration failed — please try again with a different name",
        )

    agent = Agent(
        name=data.agent_name,
        hashed_api_key=hash_api_key(raw_key),
        owner_id=user.id,
    )
    db.add(agent)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration failed — please try again",
        )
    await db.refresh(agent)

    return AgentCreateResponse(
        id=agent.id,
        name=agent.name,
        owner_id=agent.owner_id,
        last_active_at=agent.last_active_at,
        created_at=agent.created_at,
        api_key=raw_key,
    )


@router.post("", response_model=AgentCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raw_key = generate_api_key()
    agent = Agent(
        name=data.name,
        hashed_api_key=hash_api_key(raw_key),
        owner_id=user.id,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    return AgentCreateResponse(
        id=agent.id,
        name=agent.name,
        owner_id=agent.owner_id,
        last_active_at=agent.last_active_at,
        created_at=agent.created_at,
        api_key=raw_key,  # Shown once!
    )


@router.get("", response_model=list[AgentResponse])
async def list_my_agents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Agent).where(Agent.owner_id == user.id))
    return result.scalars().all()


@router.get("/directory", response_model=list[AgentDirectoryEntry])
async def agent_directory(
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Public agent directory — no auth required."""
    query = select(Agent)
    if active_only:
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        query = query.where(Agent.last_active_at >= cutoff)

    result = await db.execute(query)
    agents = result.scalars().all()

    if not agents:
        return []

    # Get owner usernames
    owner_ids = {a.owner_id for a in agents}
    users_result = await db.execute(select(User).where(User.id.in_(owner_ids)))
    users_map = {u.id: u.username for u in users_result.scalars().all()}

    # Count leagues per agent
    agent_ids = [a.id for a in agents]
    league_counts: dict[uuid_mod.UUID, int] = defaultdict(int)
    mem_result = await db.execute(
        select(LeagueMembership.agent_id, func.count())
        .where(LeagueMembership.agent_id.in_(agent_ids))
        .group_by(LeagueMembership.agent_id)
    )
    for agent_id, cnt in mem_result.all():
        league_counts[agent_id] = cnt

    # Sum fantasy points per agent (from starters across all leagues)
    agent_points: dict[uuid_mod.UUID, float] = defaultdict(float)
    memberships_result = await db.execute(
        select(LeagueMembership).where(LeagueMembership.agent_id.in_(agent_ids))
    )
    memberships = memberships_result.scalars().all()

    for mem in memberships:
        team = mem.team
        if not team or not team.players:
            continue
        starter_ids = [tp.player_id for tp in team.players if tp.is_starter]
        if not starter_ids:
            continue
        pts_result = await db.execute(
            select(func.coalesce(func.sum(PlayerGameLog.fantasy_points), 0)).where(
                PlayerGameLog.player_id.in_(starter_ids),
            )
        )
        agent_points[mem.agent_id] += float(pts_result.scalar())

    entries = []
    for agent in agents:
        entries.append(AgentDirectoryEntry(
            id=agent.id,
            name=agent.name,
            owner_username=users_map.get(agent.owner_id, "Unknown"),
            created_at=agent.created_at,
            last_active_at=agent.last_active_at,
            leagues_count=league_counts.get(agent.id, 0),
            total_fantasy_points=round(agent_points.get(agent.id, 0), 2),
        ))

    entries.sort(key=lambda e: e.total_fantasy_points, reverse=True)
    return entries


@router.get("/me", response_model=AgentMeResponse)
async def get_my_agent(
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Get the current agent's profile and leagues. Requires agent API key."""
    # Re-fetch agent to ensure clean state after get_current_agent's commit
    await db.refresh(agent)

    from app.models.league import League
    result = await db.execute(
        select(League)
        .join(LeagueMembership)
        .where(LeagueMembership.agent_id == agent.id)
    )
    agent_leagues = result.scalars().all()

    leagues = []
    for league in agent_leagues:
        leagues.append(LeagueInfo(
            id=league.id,
            name=league.name,
            sport=league.sport,
            status=league.status,
            invite_code=league.invite_code,
            member_count=len(league.memberships) if league.memberships else 0,
            max_teams=league.max_teams,
        ))

    return AgentMeResponse(
        id=agent.id,
        name=agent.name,
        owner_id=agent.owner_id,
        last_active_at=agent.last_active_at,
        created_at=agent.created_at,
        leagues=leagues,
    )


@router.post("/{agent_id}/claim", response_model=AgentResponse)
async def claim_agent(
    agent_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link a self-registered agent to your user account.

    Requires the user's JWT. Re-assigns the agent's owner_id so it
    appears on the user's dashboard.
    """
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.owner_id = user.id
    await db.commit()
    await db.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
