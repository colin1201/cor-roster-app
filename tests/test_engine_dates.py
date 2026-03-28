"""Tests for engine.py date utilities."""

from datetime import date

import engine
import rules


def test_get_sundays_single_month():
    """April 2026 has 4 Sundays."""
    sundays = engine.get_sundays_in_range(2026, 4, 2026, 4)
    assert len(sundays) == 4  # Apr 5, 12, 19, 26
    for d in sundays:
        assert d.weekday() == 6  # Sunday


def test_get_sundays_three_months():
    """Apr-Jun 2026 should have ~13 Sundays."""
    sundays = engine.get_sundays_in_range(2026, 4, 2026, 6)
    assert len(sundays) >= 12
    assert len(sundays) <= 14
    for d in sundays:
        assert d.weekday() == 6


def test_get_sundays_cross_year():
    """Nov 2026 - Jan 2027."""
    sundays = engine.get_sundays_in_range(2026, 11, 2027, 1)
    assert len(sundays) > 0
    months = {d.month for d in sundays}
    assert 11 in months
    assert 12 in months
    assert 1 in months


def test_get_sundays_empty_for_reversed_range():
    """If start > end, return empty."""
    sundays = engine.get_sundays_in_range(2026, 6, 2026, 4)
    assert sundays == []


def test_sunday_ordinal():
    # April 2026: 5th is 1st Sunday, 12th is 2nd, 19th is 3rd, 26th is 4th
    assert engine.sunday_ordinal(date(2026, 4, 5)) == 1
    assert engine.sunday_ordinal(date(2026, 4, 12)) == 2
    assert engine.sunday_ordinal(date(2026, 4, 19)) == 3
    assert engine.sunday_ordinal(date(2026, 4, 26)) == 4


def test_default_hc():
    """HC on 1st and 3rd Sundays."""
    assert engine.default_hc(date(2026, 4, 5)) is True   # 1st Sunday
    assert engine.default_hc(date(2026, 4, 12)) is False  # 2nd Sunday
    assert engine.default_hc(date(2026, 4, 19)) is True   # 3rd Sunday
    assert engine.default_hc(date(2026, 4, 26)) is False  # 4th Sunday


def test_default_combined():
    """Combined on 1st Sunday only."""
    assert engine.default_combined(date(2026, 4, 5)) is True   # 1st Sunday
    assert engine.default_combined(date(2026, 4, 12)) is False  # 2nd
    assert engine.default_combined(date(2026, 4, 19)) is False  # 3rd
    assert engine.default_combined(date(2026, 4, 26)) is False  # 4th


def test_build_details_string():
    assert engine.build_details_string(True, True, "") == "Combined / HC"
    assert engine.build_details_string(True, False, "") == "HC"
    assert engine.build_details_string(False, True, "") == "Combined"
    assert engine.build_details_string(False, False, "") == ""
    assert engine.build_details_string(True, True, "Covenant") == "Combined / HC / Covenant"
    assert engine.build_details_string(False, False, "Special") == "Special"


def test_build_details_string_strips_whitespace():
    assert engine.build_details_string(False, False, "  Covenant  ") == "Covenant"


def test_suggest_next_quarter():
    """Should return 3 consecutive months."""
    (sy, sm), (ey, em) = engine.suggest_next_quarter()
    # End should be 2 months after start
    months_diff = (ey * 12 + em) - (sy * 12 + sm)
    assert months_diff == 2


def test_month_label():
    assert engine.month_label(date(2026, 4, 5)) == "April 2026"
    assert engine.month_label(date(2026, 12, 25)) == "December 2026"


def test_format_date_col():
    assert engine.format_date_col(date(2026, 1, 5)) == "05-Jan"
    assert engine.format_date_col(date(2026, 12, 25)) == "25-Dec"
