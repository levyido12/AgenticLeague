"""Tests for NBA schedule / scoring period generation."""

from datetime import date

from app.sports.nba.schedule import NBASchedule


def test_generate_scoring_periods():
    schedule = NBASchedule("2025-26")
    periods = schedule.generate_scoring_periods("2025-26")

    assert len(periods) > 0
    # Each period is Monday-Sunday
    for p in periods:
        assert p["start_date"].weekday() == 0  # Monday
        assert p["end_date"].weekday() == 6  # Sunday

    # First period number is 1
    assert periods[0]["period_number"] == 1

    # Last few periods should be playoffs
    playoff_periods = [p for p in periods if p["is_playoff"]]
    assert len(playoff_periods) >= 1


def test_current_scoring_period_during_season():
    schedule = NBASchedule("2025-26")
    # Pick a date during the season
    period = schedule.current_scoring_period(date(2025, 12, 15))
    assert period is not None
    assert period["start_date"] <= date(2025, 12, 15) <= period["end_date"]


def test_current_scoring_period_off_season():
    schedule = NBASchedule("2025-26")
    # Pick a date in the off-season
    period = schedule.current_scoring_period(date(2026, 7, 1))
    assert period is None
