import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class WaiverClaim(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "waiver_claims"

    league_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("leagues.id"), index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("agents.id")
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("players.id")
    )
    drop_player_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("players.id")
    )
    priority: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, approved, denied, cancelled
    waiver_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
