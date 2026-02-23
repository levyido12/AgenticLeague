"""NBA data adapter using the nba_api package."""

import asyncio
import logging
from datetime import date
from typing import Any

from app.config import settings
from app.sports.base import BaseSportAdapter

logger = logging.getLogger(__name__)


class NBAAdapter(BaseSportAdapter):
    """Wraps nba_api to fetch player data and game logs from NBA.com."""

    def __init__(self, delay: float | None = None):
        self.delay = delay if delay is not None else settings.nba_api_delay_seconds

    async def fetch_game_logs(self, game_date: date) -> list[dict[str, Any]]:
        """Fetch all player game logs for a given date."""
        return await asyncio.to_thread(self._fetch_game_logs_sync, game_date)

    def _fetch_game_logs_sync(self, game_date: date) -> list[dict[str, Any]]:
        import time

        from nba_api.stats.endpoints import playergamelogs

        date_str = game_date.strftime("%m/%d/%Y")
        season = self._date_to_season(game_date)

        try:
            time.sleep(self.delay)
            logs = playergamelogs.PlayerGameLogs(
                season_nullable=season,
                date_from_nullable=date_str,
                date_to_nullable=date_str,
            )
            df = logs.get_data_frames()[0]
        except Exception:
            logger.exception("Failed to fetch game logs for %s", game_date)
            return []

        results = []
        for _, row in df.iterrows():
            results.append(
                {
                    "external_player_id": str(row["PLAYER_ID"]),
                    "player_name": row["PLAYER_NAME"],
                    "team": row["TEAM_ABBREVIATION"],
                    "stats": {
                        "pts": int(row.get("PTS", 0)),
                        "reb": int(row.get("REB", 0)),
                        "ast": int(row.get("AST", 0)),
                        "stl": int(row.get("STL", 0)),
                        "blk": int(row.get("BLK", 0)),
                        "tov": int(row.get("TOV", 0)),
                        "fg3m": int(row.get("FG3M", 0)),
                        "min": row.get("MIN", 0),
                    },
                }
            )

        return results

    async def fetch_players(self) -> list[dict[str, Any]]:
        """Fetch the full NBA player roster."""
        return await asyncio.to_thread(self._fetch_players_sync)

    def _fetch_players_sync(self) -> list[dict[str, Any]]:
        import time

        from nba_api.stats.static import players as nba_players

        time.sleep(self.delay)
        all_players = nba_players.get_active_players()

        results = []
        for p in all_players:
            results.append(
                {
                    "external_id": str(p["id"]),
                    "full_name": p["full_name"],
                    "position": "",  # nba_api static doesn't include position; enriched later
                    "team": "",
                    "status": "active",
                }
            )
        return results

    @staticmethod
    def _date_to_season(d: date) -> str:
        """Convert a date to NBA season string (e.g. '2025-26')."""
        year = d.year if d.month >= 10 else d.year - 1
        return f"{year}-{str(year + 1)[-2:]}"
