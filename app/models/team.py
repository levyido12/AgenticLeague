import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Team(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "teams"

    membership_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("league_memberships.id"), unique=True
    )

    membership = relationship("LeagueMembership", back_populates="team", lazy="selectin")
    players = relationship("TeamPlayer", back_populates="team", lazy="selectin")


class TeamPlayer(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "team_players"

    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("teams.id"), index=True
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("players.id"), index=True
    )
    roster_slot: Mapped[str] = mapped_column(String(10))
    is_starter: Mapped[bool] = mapped_column(default=True)

    team = relationship("Team", back_populates="players", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("team_id", "player_id", name="uq_team_player"),
    )
