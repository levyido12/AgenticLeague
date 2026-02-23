import uuid
from datetime import datetime

from pydantic import BaseModel


class DraftPickRequest(BaseModel):
    player_id: uuid.UUID


class DraftPickResponse(BaseModel):
    id: uuid.UUID
    league_id: uuid.UUID
    agent_id: uuid.UUID
    player_id: uuid.UUID
    pick_number: int
    round_number: int
    is_auto_pick: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DraftStateResponse(BaseModel):
    league_id: uuid.UUID
    current_pick: int
    total_picks: int
    status: str
    current_agent_id: uuid.UUID | None = None
    draft_order: list[uuid.UUID]

    model_config = {"from_attributes": True}
