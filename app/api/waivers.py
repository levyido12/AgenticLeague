"""Waiver and free agent pickup endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_agent
from app.models.agent import Agent
from app.schemas.waivers import FreeAgentPickupRequest, WaiverClaimRequest, WaiverClaimResponse
from app.services.waivers import create_waiver_claim, pickup_free_agent

router = APIRouter(prefix="/leagues/{league_id}", tags=["waivers"])


@router.post("/waivers/claim", response_model=WaiverClaimResponse, status_code=status.HTTP_201_CREATED)
async def claim_waiver(
    league_id: uuid.UUID,
    data: WaiverClaimRequest,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    claim = await create_waiver_claim(
        db, league_id, agent.id, data.player_id, data.drop_player_id
    )
    return claim


@router.post("/free-agents/pickup")
async def pickup(
    league_id: uuid.UUID,
    data: FreeAgentPickupRequest,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    try:
        success = await pickup_free_agent(
            db, league_id, agent.id, data.player_id, data.drop_player_id
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not success:
        raise HTTPException(status_code=400, detail="Could not add player to team")

    return {"status": "ok", "message": "Player added to roster"}
