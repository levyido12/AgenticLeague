import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class LeagueCreate(BaseModel):
    name: str
    sport: str = "nba"
    max_teams: int = 14
    draft_date: datetime | None = None
    scoring_config: dict[str, float] | None = None


class LeagueResponse(BaseModel):
    id: uuid.UUID
    name: str
    sport: str
    commissioner_id: uuid.UUID
    invite_code: str
    status: str
    min_teams: int
    max_teams: int
    draft_date: datetime | None
    season: str
    member_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class LeagueJoin(BaseModel):
    invite_code: str


class StandingsEntry(BaseModel):
    agent_id: uuid.UUID
    agent_name: str
    wins: int
    losses: int
    ties: int
    total_points: float
    rank: int
