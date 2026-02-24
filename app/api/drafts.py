"""Draft endpoints."""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_agent
from app.models.agent import Agent
from app.schemas.drafts import DraftPickRequest, DraftPickResponse, DraftStateResponse
from app.services.draft import get_draft_state, initialize_draft, make_pick

router = APIRouter(prefix="/leagues/{league_id}/draft", tags=["draft"])


@router.post("/start", response_model=DraftStateResponse)
async def start_draft(
    league_id: uuid.UUID,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Start the draft (commissioner only)."""
    from app.models.league import League
    from sqlalchemy import select

    result = await db.execute(select(League).where(League.id == league_id))
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    member_ids = {m.agent_id for m in league.memberships}
    if agent.id not in member_ids:
        raise HTTPException(status_code=403, detail="Only league members can start the draft")

    if league.status != "pre_season":
        raise HTTPException(status_code=400, detail="Draft can only start from pre-season")

    if len(league.memberships) < league.min_teams:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least {league.min_teams} teams to start draft",
        )

    draft_state = await initialize_draft(db, league_id)
    order = json.loads(draft_state.draft_order)

    return DraftStateResponse(
        league_id=draft_state.league_id,
        current_pick=draft_state.current_pick,
        total_picks=draft_state.total_picks,
        status=draft_state.status,
        current_agent_id=uuid.UUID(order[0]) if order else None,
        draft_order=[uuid.UUID(x) for x in order],
    )


@router.get("", response_model=DraftStateResponse)
async def get_draft(league_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    draft_state = await get_draft_state(db, league_id)
    if not draft_state:
        raise HTTPException(status_code=404, detail="No draft found for this league")

    order = json.loads(draft_state.draft_order)
    current_agent = None
    if draft_state.status == "in_progress" and draft_state.current_pick <= len(order):
        current_agent = uuid.UUID(order[draft_state.current_pick - 1])

    return DraftStateResponse(
        league_id=draft_state.league_id,
        current_pick=draft_state.current_pick,
        total_picks=draft_state.total_picks,
        status=draft_state.status,
        current_agent_id=current_agent,
        draft_order=[uuid.UUID(x) for x in order],
    )


@router.post("/pick", response_model=DraftPickResponse)
async def draft_pick(
    league_id: uuid.UUID,
    data: DraftPickRequest,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    try:
        pick = await make_pick(db, league_id, agent.id, data.player_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return pick
