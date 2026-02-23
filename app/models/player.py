import uuid
from datetime import date

from sqlalchemy import JSON, Date, ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Player(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "players"

    external_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    sport: Mapped[str] = mapped_column(String(20), default="nba")
    full_name: Mapped[str] = mapped_column(String(100))
    position: Mapped[str] = mapped_column(String(20))  # e.g. "nba:PG", "nba:SG-SF"
    nba_team: Mapped[str] = mapped_column(String(5))  # e.g. "LAL", "BOS"
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, injured, out
    season_stats: Mapped[dict] = mapped_column(JSON, default=dict)


class PlayerGameLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "player_game_logs"

    player_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("players.id"), index=True
    )
    game_date: Mapped[date] = mapped_column(Date)
    season: Mapped[str] = mapped_column(String(10))
    stats: Mapped[dict] = mapped_column(JSON)
    fantasy_points: Mapped[float | None] = mapped_column(Numeric(8, 2))

    __table_args__ = (
        UniqueConstraint("player_id", "game_date", name="uq_player_game_date"),
    )
