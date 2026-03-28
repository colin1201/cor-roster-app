"""Tests for shared scheduling primitives in engine.py."""

from datetime import date

import engine


# ---------------------------------------------------------------------------
# build_eligible_pool
# ---------------------------------------------------------------------------

def test_eligible_pool_filters_by_qualification():
    vols = [
        {"name": "Alice", "sound": True, "projection": False},
        {"name": "Bob", "sound": False, "projection": True},
        {"name": "Carol", "sound": True, "projection": True},
    ]
    pool = engine.build_eligible_pool(vols, "sound", set(), set())
    names = {p["name"] for p in pool}
    assert names == {"Alice", "Carol"}


def test_eligible_pool_excludes_unavailable():
    vols = [
        {"name": "Alice", "sound": True},
        {"name": "Bob", "sound": True},
    ]
    pool = engine.build_eligible_pool(vols, "sound", unavailable={"Alice"}, assigned_today=set())
    names = {p["name"] for p in pool}
    assert names == {"Bob"}


def test_eligible_pool_excludes_already_assigned():
    vols = [
        {"name": "Alice", "sound": True},
        {"name": "Bob", "sound": True},
    ]
    pool = engine.build_eligible_pool(vols, "sound", unavailable=set(), assigned_today={"Alice"})
    names = {p["name"] for p in pool}
    assert names == {"Bob"}


def test_eligible_pool_empty_when_none_qualified():
    vols = [
        {"name": "Alice", "sound": False},
    ]
    pool = engine.build_eligible_pool(vols, "sound", set(), set())
    assert pool == []


# ---------------------------------------------------------------------------
# apply_weekly_rest
# ---------------------------------------------------------------------------

def test_weekly_rest_filters_previous_week():
    names = ["Alice", "Bob", "Carol"]
    d = date(2026, 4, 12)  # Sunday
    prev_week = date(2026, 4, 5)
    assignments = {prev_week: {"Alice", "Bob"}}

    rested, full = engine.apply_weekly_rest(names, d, assignments)
    assert "Alice" not in rested
    assert "Bob" not in rested
    assert "Carol" in rested
    # Full pool should still have everyone
    assert set(full) == {"Alice", "Bob", "Carol"}


def test_weekly_rest_no_filter_if_gap():
    names = ["Alice", "Bob"]
    d = date(2026, 4, 19)
    assignments = {date(2026, 4, 5): {"Alice", "Bob"}}  # 2 weeks ago, not consecutive

    rested, full = engine.apply_weekly_rest(names, d, assignments)
    assert set(rested) == {"Alice", "Bob"}


def test_weekly_rest_self_heal_when_all_served():
    """If everyone served last week, rested pool is empty — full pool used for self-healing."""
    names = ["Alice", "Bob"]
    d = date(2026, 4, 12)
    assignments = {date(2026, 4, 5): {"Alice", "Bob"}}

    rested, full = engine.apply_weekly_rest(names, d, assignments)
    assert rested == []
    assert set(full) == {"Alice", "Bob"}


# ---------------------------------------------------------------------------
# sort_by_load
# ---------------------------------------------------------------------------

def test_sort_by_load():
    names = ["Alice", "Bob", "Carol"]
    load = {"Alice": 3, "Bob": 1, "Carol": 2}
    sorted_names = engine.sort_by_load(names, load)
    assert sorted_names[0] == "Bob"
    assert sorted_names[1] == "Carol"
    assert sorted_names[2] == "Alice"


def test_sort_by_load_missing_defaults_to_zero():
    names = ["Alice", "Bob"]
    load = {"Alice": 2}
    sorted_names = engine.sort_by_load(names, load)
    assert sorted_names[0] == "Bob"  # load=0


# ---------------------------------------------------------------------------
# seeded_tiebreak
# ---------------------------------------------------------------------------

def test_seeded_tiebreak_deterministic():
    names = ["Alice", "Bob", "Carol", "Dave"]
    result1 = engine.seeded_tiebreak(names, seed=42, date_str="2026-04-05", role="Sound")
    result2 = engine.seeded_tiebreak(names, seed=42, date_str="2026-04-05", role="Sound")
    assert result1 == result2


def test_seeded_tiebreak_different_seed_different_result():
    names = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank"]
    result1 = engine.seeded_tiebreak(names, seed=42, date_str="2026-04-05", role="Sound")
    result2 = engine.seeded_tiebreak(names, seed=99, date_str="2026-04-05", role="Sound")
    # With enough names, different seeds should (very likely) give different results
    # This is probabilistic but with 6 names it's extremely unlikely to match
    assert result1 != result2


def test_seeded_tiebreak_single_name():
    assert engine.seeded_tiebreak(["Alice"], seed=42, date_str="2026-04-05", role="Sound") == "Alice"


def test_seeded_tiebreak_empty():
    assert engine.seeded_tiebreak([], seed=42, date_str="2026-04-05", role="Sound") is None


# ---------------------------------------------------------------------------
# select_one (full pipeline)
# ---------------------------------------------------------------------------

def test_select_one_picks_qualified_available():
    vols = [
        {"name": "Alice", "sound": True},
        {"name": "Bob", "sound": False},
        {"name": "Carol", "sound": True},
    ]
    pick = engine.select_one(
        volunteers=vols,
        role_key="sound",
        service_date=date(2026, 4, 5),
        unavailable=set(),
        assigned_today=set(),
        assignments_by_date={},
        load_counts={},
        seed=42,
    )
    assert pick in ("Alice", "Carol")


def test_select_one_respects_unavailability():
    vols = [
        {"name": "Alice", "sound": True},
        {"name": "Bob", "sound": True},
    ]
    pick = engine.select_one(
        volunteers=vols,
        role_key="sound",
        service_date=date(2026, 4, 5),
        unavailable={"Alice"},
        assigned_today=set(),
        assignments_by_date={},
        load_counts={},
        seed=42,
    )
    assert pick == "Bob"


def test_select_one_prefers_lowest_load():
    vols = [
        {"name": "Alice", "sound": True},
        {"name": "Bob", "sound": True},
    ]
    pick = engine.select_one(
        volunteers=vols,
        role_key="sound",
        service_date=date(2026, 4, 5),
        unavailable=set(),
        assigned_today=set(),
        assignments_by_date={},
        load_counts={"Alice": 5, "Bob": 1},
        seed=42,
    )
    assert pick == "Bob"


def test_select_one_returns_none_when_impossible():
    vols = [
        {"name": "Alice", "sound": False},
    ]
    pick = engine.select_one(
        volunteers=vols,
        role_key="sound",
        service_date=date(2026, 4, 5),
        unavailable=set(),
        assigned_today=set(),
        assignments_by_date={},
        load_counts={},
        seed=42,
    )
    assert pick is None


def test_select_one_self_heals_weekly_rest():
    """If everyone served last week, should still pick someone."""
    vols = [
        {"name": "Alice", "sound": True},
        {"name": "Bob", "sound": True},
    ]
    prev_date = date(2026, 4, 5)
    this_date = date(2026, 4, 12)
    pick = engine.select_one(
        volunteers=vols,
        role_key="sound",
        service_date=this_date,
        unavailable=set(),
        assigned_today=set(),
        assignments_by_date={prev_date: {"Alice", "Bob"}},
        load_counts={},
        seed=42,
    )
    assert pick in ("Alice", "Bob")
