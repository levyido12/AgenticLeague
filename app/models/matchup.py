import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ScoringPeriod(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "scoring_periods"

    league_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("leagues.id"), index=True
    )
    period_number: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(50))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    is_playoff: Mapped[bool] = mapped_column(default=False)

    league = relationship("League", back_populates="scoring_periods", lazy="selectin")
    matchups = relationship("Matchup", back_populates="scoring_period", lazy="selectin")


class Matchup(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "matchups"

    scoring_period_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("scoring_periods.id"), index=True
    )
    home_agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("agents.id")
    )
    away_agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("agents.id")
    )
    home_points: Mapped[float | None] = mapped_column(Numeric(10, 2))
    away_points: Mapped[float | None] = mapped_column(Numeric(10, 2))
    winner_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("agents.id")
    )
    is_tie: Mapped[bool] = mapped_column(default=False)

    scoring_period = relationship("ScoringPeriod", back_populates="matchups", lazy="selectin")
