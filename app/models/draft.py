import uuid

from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class DraftState(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "draft_states"

    league_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("leagues.id"), unique=True
    )
    current_pick: Mapped[int] = mapped_column(Integer, default=1)
    total_picks: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, in_progress, completed
    draft_order: Mapped[str] = mapped_column(String(2000))  # JSON list of agent IDs in snake order


class DraftPick(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "draft_picks"

    league_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("leagues.id"), index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("agents.id")
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("players.id")
    )
    pick_number: Mapped[int] = mapped_column(Integer)
    round_number: Mapped[int] = mapped_column(Integer)
    is_auto_pick: Mapped[bool] = mapped_column(default=False)
