"""Agent management endpoints."""

import uuid as uuid_mod

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.agent import Agent
from app.models.user import User
from app.schemas.agents import AgentCreate, AgentCreateResponse, AgentRegister, AgentResponse
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
    random_email = f"{uuid_mod.uuid4()}@agent.local"
    random_password = generate_api_key()  # never exposed

    user = User(
        username=owner_name,
        email=random_email,
        hashed_password=hash_password(random_password),
    )
    db.add(user)
    await db.flush()

    raw_key = generate_api_key()
    agent = Agent(
        name=data.agent_name,
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


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent
