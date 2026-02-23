"""NBA-specific scoring, positions, and roster validation."""

from typing import Any

from app.sports.base import BaseSportRules

# Position eligibility mapping: roster_slot -> eligible player positions
_POSITION_ELIGIBILITY: dict[str, set[str]] = {
    "PG": {"nba:PG"},
    "SG": {"nba:SG"},
    "SF": {"nba:SF"},
    "PF": {"nba:PF"},
    "C": {"nba:C"},
    "G": {"nba:PG", "nba:SG"},
    "F": {"nba:SF", "nba:PF"},
    "UTIL": {"nba:PG", "nba:SG", "nba:SF", "nba:PF", "nba:C"},
    "BN": {"nba:PG", "nba:SG", "nba:SF", "nba:PF", "nba:C"},
}


class NBARules(BaseSportRules):
    def default_scoring_config(self) -> dict[str, float]:
        return {
            "pts": 1.0,
            "reb": 1.2,
            "ast": 1.5,
            "stl": 3.0,
            "blk": 3.0,
            "tov": -1.0,
            "fg3m": 0.5,
            "double_double_bonus": 1.5,
            "triple_double_bonus": 3.0,
        }

    def default_roster_config(self) -> dict[str, Any]:
        return {
            "starter_slots": ["PG", "SG", "SF", "PF", "C", "G", "F", "UTIL", "UTIL", "UTIL"],
            "bench_slots": 3,
            "total_roster_size": 13,
        }

    def calculate_fantasy_points(
        self, stats: dict[str, Any], scoring_config: dict[str, float]
    ) -> float:
        pts = stats.get("pts", 0)
        reb = stats.get("reb", 0)
        ast = stats.get("ast", 0)
        stl = stats.get("stl", 0)
        blk = stats.get("blk", 0)
        tov = stats.get("tov", 0)
        fg3m = stats.get("fg3m", 0)

        total = (
            pts * scoring_config.get("pts", 1.0)
            + reb * scoring_config.get("reb", 1.2)
            + ast * scoring_config.get("ast", 1.5)
            + stl * scoring_config.get("stl", 3.0)
            + blk * scoring_config.get("blk", 3.0)
            + tov * scoring_config.get("tov", -1.0)
            + fg3m * scoring_config.get("fg3m", 0.5)
        )

        # Count categories >= 10 for double-double / triple-double
        cats_over_10 = sum(1 for v in [pts, reb, ast, stl, blk] if v >= 10)
        if cats_over_10 >= 3:
            total += scoring_config.get("triple_double_bonus", 3.0)
        elif cats_over_10 >= 2:
            total += scoring_config.get("double_double_bonus", 1.5)

        return round(total, 2)

    def valid_positions(self) -> list[str]:
        return ["nba:PG", "nba:SG", "nba:SF", "nba:PF", "nba:C"]

    def position_eligible(self, player_position: str, roster_slot: str) -> bool:
        eligible = _POSITION_ELIGIBILITY.get(roster_slot, set())
        # A player can have multi-position like "nba:SG-SF"
        player_positions = {p.strip() for p in player_position.split("-")}
        # Expand: "nba:SG-SF" -> {"nba:SG", "nba:SF"}
        expanded = set()
        for pos in player_positions:
            if ":" in pos:
                expanded.add(pos)
            else:
                expanded.add(f"nba:{pos}")
        return bool(eligible & expanded)
