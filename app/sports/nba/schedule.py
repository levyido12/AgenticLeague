"""NBA season calendar and scoring period generation."""

from datetime import date, timedelta
from typing import Any

from app.sports.base import BaseSeasonOrchestrator

# Approximate NBA season dates (adjusted each year)
_SEASON_DATES: dict[str, dict[str, date]] = {
    "2025-26": {
        "start": date(2025, 10, 20),
        "all_star_start": date(2026, 2, 13),
        "all_star_end": date(2026, 2, 19),
        "end": date(2026, 4, 12),
    },
    "2024-25": {
        "start": date(2024, 10, 22),
        "all_star_start": date(2025, 2, 14),
        "all_star_end": date(2025, 2, 20),
        "end": date(2025, 4, 13),
    },
}


class NBASchedule(BaseSeasonOrchestrator):
    def __init__(self, season: str = "2025-26"):
        self.season = season
        self.dates = _SEASON_DATES.get(season, _SEASON_DATES["2025-26"])

    def generate_scoring_periods(
        self, season: str, league_start: date | None = None
    ) -> list[dict[str, Any]]:
        dates = _SEASON_DATES.get(season, self.dates)
        start = league_start or dates["start"]

        # Find the first Monday on or after start
        days_until_monday = (7 - start.weekday()) % 7
        first_monday = start + timedelta(days=days_until_monday) if days_until_monday else start

        periods = []
        period_num = 1
        current = first_monday

        while current + timedelta(days=6) <= dates["end"]:
            week_end = current + timedelta(days=6)  # Sunday

            # Check if this week overlaps All-Star break
            is_all_star = (
                current <= dates["all_star_end"] and week_end >= dates["all_star_start"]
            )

            if is_all_star:
                # Skip the All-Star week (dead week)
                current = week_end + timedelta(days=1)
                continue

            # Last 3 weeks = playoffs
            remaining_mondays = 0
            check = current + timedelta(days=7)
            while check + timedelta(days=6) <= dates["end"]:
                check_end = check + timedelta(days=6)
                check_all_star = (
                    check <= dates["all_star_end"] and check_end >= dates["all_star_start"]
                )
                if not check_all_star:
                    remaining_mondays += 1
                check += timedelta(days=7)

            is_playoff = remaining_mondays < 3

            periods.append(
                {
                    "period_number": period_num,
                    "label": f"Week {period_num}" + (" (Playoffs)" if is_playoff else ""),
                    "start_date": current,
                    "end_date": week_end,
                    "is_playoff": is_playoff,
                }
            )
            period_num += 1
            current = week_end + timedelta(days=1)

        return periods

    def current_scoring_period(self, today: date | None = None) -> dict[str, Any] | None:
        today = today or date.today()
        periods = self.generate_scoring_periods(self.season)
        for p in periods:
            if p["start_date"] <= today <= p["end_date"]:
                return p
        return None
