"""Agent management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.models.agent import Agent
from app.models.user import User
from app.schemas.agents import AgentCreate, AgentCreateResponse, AgentResponse
from app.services.auth import generate_api_key, hash_api_key

router = APIRouter(prefix="/agents", tags=["agents"])


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
