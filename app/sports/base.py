"""Abstract base classes for the 3-layer sport extensibility design."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class BaseSportAdapter(ABC):
    """Fetches real-world stats from an external source."""

    @abstractmethod
    async def fetch_game_logs(self, game_date: date) -> list[dict[str, Any]]:
        """Fetch all player game logs for a given date.

        Returns list of dicts with keys: external_player_id, player_name, team,
        position, stats (dict with sport-specific stat keys).
        """
        ...

    @abstractmethod
    async def fetch_players(self) -> list[dict[str, Any]]:
        """Fetch the full player roster for the sport.

        Returns list of dicts with keys: external_id, full_name, position, team, status.
        """
        ...


class BaseSportRules(ABC):
    """Sport-specific scoring, positions, and roster validation."""

    @abstractmethod
    def default_scoring_config(self) -> dict[str, float]:
        """Return the default scoring weights for this sport."""
        ...

    @abstractmethod
    def default_roster_config(self) -> dict[str, Any]:
        """Return default roster structure: starter slots, bench count, total size."""
        ...

    @abstractmethod
    def calculate_fantasy_points(
        self, stats: dict[str, Any], scoring_config: dict[str, float]
    ) -> float:
        """Calculate fantasy points for one player game log."""
        ...

    @abstractmethod
    def valid_positions(self) -> list[str]:
        """Return all valid position strings for this sport (e.g. ['nba:PG', ...])."""
        ...

    @abstractmethod
    def position_eligible(self, player_position: str, roster_slot: str) -> bool:
        """Check if a player's position is eligible for a roster slot."""
        ...


class BaseSeasonOrchestrator(ABC):
    """Defines scoring periods, season lifecycle, and schedule."""

    @abstractmethod
    def generate_scoring_periods(
        self, season: str, league_start: date | None = None
    ) -> list[dict[str, Any]]:
        """Generate all scoring periods for a season.

        Returns list of dicts with keys: period_number, label, start_date, end_date, is_playoff.
        """
        ...

    @abstractmethod
    def current_scoring_period(self, today: date | None = None) -> dict[str, Any] | None:
        """Return the current scoring period based on date, or None if off-season."""
        ...
