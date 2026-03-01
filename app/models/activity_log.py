"""Activity log for agent actions (join, draft, waiver, etc.)."""

import uuid

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class ActivityLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "activity_logs"

    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("agents.id"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(50), index=True)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
