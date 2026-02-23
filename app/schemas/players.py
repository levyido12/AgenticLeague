import uuid
from typing import Any

from pydantic import BaseModel


class PlayerResponse(BaseModel):
    id: uuid.UUID
    external_id: str
    sport: str
    full_name: str
    position: str
    nba_team: str
    status: str
    season_stats: dict[str, Any]

    model_config = {"from_attributes": True}


class LeaderboardEntry(BaseModel):
    agent_id: uuid.UUID
    agent_name: str
    owner_username: str
    total_fantasy_points: float
    leagues_count: int
    rank: int
