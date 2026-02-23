"""Tests for NBA scoring calculations."""

from app.sports.nba.rules import NBARules


rules = NBARules()
default_config = rules.default_scoring_config()


def test_basic_scoring():
    stats = {"pts": 25, "reb": 5, "ast": 7, "stl": 2, "blk": 1, "tov": 3, "fg3m": 4}
    points = rules.calculate_fantasy_points(stats, default_config)
    # 25*1 + 5*1.2 + 7*1.5 + 2*3 + 1*3 + (-3)*1 + 4*0.5 = 25 + 6 + 10.5 + 6 + 3 - 3 + 2 = 49.5
    assert points == 49.5


def test_double_double_bonus():
    stats = {"pts": 20, "reb": 10, "ast": 5, "stl": 0, "blk": 0, "tov": 0, "fg3m": 0}
    points = rules.calculate_fantasy_points(stats, default_config)
    # 20 + 12 + 7.5 + 0 + 0 - 0 + 0 + 1.5 (dd bonus) = 41.0
    assert points == 41.0


def test_triple_double_bonus():
    stats = {"pts": 15, "reb": 12, "ast": 10, "stl": 1, "blk": 0, "tov": 2, "fg3m": 1}
    points = rules.calculate_fantasy_points(stats, default_config)
    # 15 + 14.4 + 15 + 3 + 0 - 2 + 0.5 + 3 (td bonus) = 48.9
    assert points == 48.9


def test_zero_stats():
    stats = {"pts": 0, "reb": 0, "ast": 0, "stl": 0, "blk": 0, "tov": 0, "fg3m": 0}
    points = rules.calculate_fantasy_points(stats, default_config)
    assert points == 0.0


def test_turnovers_negative():
    stats = {"pts": 0, "reb": 0, "ast": 0, "stl": 0, "blk": 0, "tov": 5, "fg3m": 0}
    points = rules.calculate_fantasy_points(stats, default_config)
    assert points == -5.0


def test_custom_scoring_config():
    custom = {"pts": 2.0, "reb": 1.0, "ast": 1.0, "stl": 2.0, "blk": 2.0, "tov": -2.0, "fg3m": 1.0}
    stats = {"pts": 10, "reb": 5, "ast": 3, "stl": 1, "blk": 1, "tov": 2, "fg3m": 2}
    points = rules.calculate_fantasy_points(stats, custom)
    # 20 + 5 + 3 + 2 + 2 - 4 + 2 = 30.0 (no dd/td bonuses in custom config)
    assert points == 30.0
