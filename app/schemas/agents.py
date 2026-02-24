import uuid
from datetime import datetime

from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str


class AgentRegister(BaseModel):
    agent_name: str
    owner_name: str | None = None


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    last_active_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentCreateResponse(AgentResponse):
    """Returned only on creation — includes the raw API key (shown once)."""

    api_key: str
