"""Tests for NBA roster rules and position eligibility."""

from app.sports.nba.rules import NBARules

rules = NBARules()


def test_valid_positions():
    positions = rules.valid_positions()
    assert "nba:PG" in positions
    assert "nba:C" in positions
    assert len(positions) == 5


def test_position_eligibility_exact():
    assert rules.position_eligible("nba:PG", "PG") is True
    assert rules.position_eligible("nba:SG", "PG") is False


def test_position_eligibility_guard_slot():
    assert rules.position_eligible("nba:PG", "G") is True
    assert rules.position_eligible("nba:SG", "G") is True
    assert rules.position_eligible("nba:SF", "G") is False


def test_position_eligibility_forward_slot():
    assert rules.position_eligible("nba:SF", "F") is True
    assert rules.position_eligible("nba:PF", "F") is True
    assert rules.position_eligible("nba:C", "F") is False


def test_position_eligibility_util():
    for pos in rules.valid_positions():
        assert rules.position_eligible(pos, "UTIL") is True


def test_position_eligibility_bench():
    for pos in rules.valid_positions():
        assert rules.position_eligible(pos, "BN") is True


def test_multi_position_player():
    # SG-SF can play SG, SF, G, F, UTIL, BN
    assert rules.position_eligible("nba:SG-SF", "SG") is True
    assert rules.position_eligible("nba:SG-SF", "SF") is True
    assert rules.position_eligible("nba:SG-SF", "G") is True
    assert rules.position_eligible("nba:SG-SF", "F") is True
    assert rules.position_eligible("nba:SG-SF", "PG") is False


def test_default_roster_config():
    config = rules.default_roster_config()
    assert config["total_roster_size"] == 13
    assert config["bench_slots"] == 3
    assert len(config["starter_slots"]) == 10
