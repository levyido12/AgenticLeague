import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class League(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "leagues"

    name: Mapped[str] = mapped_column(String(100))
    sport: Mapped[str] = mapped_column(String(20), default="nba")
    commissioner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("agents.id")
    )
    invite_code: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    status: Mapped[str] = mapped_column(
        String(20), default="pre_season"
    )  # pre_season, drafting, active, playoffs, completed
    min_teams: Mapped[int] = mapped_column(Integer, default=6)
    max_teams: Mapped[int] = mapped_column(Integer, default=14)
    draft_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scoring_config: Mapped[dict] = mapped_column(JSON, default=dict)
    roster_config: Mapped[dict] = mapped_column(JSON, default=dict)
    season: Mapped[str] = mapped_column(String(10), default="2025-26")

    commissioner = relationship("Agent", foreign_keys=[commissioner_id], lazy="selectin")
    memberships = relationship("LeagueMembership", back_populates="league", lazy="selectin")
    scoring_periods = relationship("ScoringPeriod", back_populates="league", lazy="noload")


class LeagueMembership(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "league_memberships"

    league_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("leagues.id")
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("agents.id")
    )

    league = relationship("League", back_populates="memberships", lazy="selectin")
    agent = relationship("Agent", back_populates="memberships", lazy="selectin")
    team = relationship("Team", back_populates="membership", uselist=False, lazy="selectin")

    __table_args__ = (
        UniqueConstraint("league_id", "agent_id", name="uq_league_agent"),
    )
