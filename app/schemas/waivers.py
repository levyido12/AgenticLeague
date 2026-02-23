import uuid
from datetime import datetime

from pydantic import BaseModel


class WaiverClaimRequest(BaseModel):
    player_id: uuid.UUID
    drop_player_id: uuid.UUID | None = None


class WaiverClaimResponse(BaseModel):
    id: uuid.UUID
    league_id: uuid.UUID
    agent_id: uuid.UUID
    player_id: uuid.UUID
    drop_player_id: uuid.UUID | None
    priority: int
    status: str
    waiver_expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class FreeAgentPickupRequest(BaseModel):
    player_id: uuid.UUID
    drop_player_id: uuid.UUID | None = None
