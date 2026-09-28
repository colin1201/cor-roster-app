"""Tests for CSV export."""

from datetime import date

import export
import rules


def test_csv_has_monthly_blocks():
    roster = {
        date(2026, 4, 5): {"Stream Director": "Alice", "Camera 1": "Bob", "Projection": "Carol", "Sound": "Dave", "Cam 2": "", "Media Team Lead": "Alice"},
        date(2026, 5, 3): {"Stream Director": "Eve", "Camera 1": "Bob", "Projection": "Carol", "Sound": "Dave", "Cam 2": "", "Media Team Lead": "Eve"},
    }
    services = [
        {"date": date(2026, 4, 5), "hc": True, "combined": True, "notes": ""},
        {"date": date(2026, 5, 3), "hc": False, "combined": False, "notes": ""},
    ]
    load = {"Alice": 1, "Bob": 2, "Carol": 2, "Dave": 2, "Eve": 1}
    csv = export.roster_to_csv(roster, services, rules.MINISTRY_MEDIA_TECH, load)

    assert "April 2026" in csv
    assert "May 2026" in csv


def test_csv_has_details_row():
    roster = {
        date(2026, 4, 5): {"Stream Director": "A", "Camera 1": "B", "Projection": "C", "Sound": "D", "Cam 2": "", "Media Team Lead": "A"},
    }
    services = [{"date": date(2026, 4, 5), "hc": True, "combined": True, "notes": "Covenant"}]
    load = {"A": 1, "B": 1, "C": 1, "D": 1}
    csv = export.roster_to_csv(roster, services, rules.MINISTRY_MEDIA_TECH, load)

    assert "Combined / HC / Covenant" in csv


def test_csv_has_load_stats():
    roster = {
        date(2026, 4, 5): {"Stream Director": "A", "Camera 1": "B", "Projection": "C", "Sound": "D", "Cam 2": "", "Media Team Lead": "A"},
    }
    services = [{"date": date(2026, 4, 5), "hc": False, "combined": False, "notes": ""}]
    load = {"A": 3, "B": 2, "C": 1, "D": 1}
    csv = export.roster_to_csv(roster, services, rules.MINISTRY_MEDIA_TECH, load)

    assert "Load Statistics" in csv
    assert "A,3" in csv
    assert "B,2" in csv


def test_csv_date_format():
    roster = {
        date(2026, 4, 5): {"Stream Director": "A", "Camera 1": "B", "Projection": "C", "Sound": "D", "Cam 2": "", "Media Team Lead": "A"},
    }
    services = [{"date": date(2026, 4, 5), "hc": False, "combined": False, "notes": ""}]
    load = {"A": 1}
    csv = export.roster_to_csv(roster, services, rules.MINISTRY_MEDIA_TECH, load)

    assert "05-Apr" in csv


def test_csv_welcome_roles():
    roster = {
        date(2026, 4, 5): {"Welcome Team Lead": "X", "Member 1": "A", "Member 2": "B", "Member 3": "C", "Member 4": "D"},
    }
    services = [{"date": date(2026, 4, 5), "hc": True, "combined": False, "notes": ""}]
    load = {"X": 1, "A": 1, "B": 1, "C": 1, "D": 1}
    csv = export.roster_to_csv(roster, services, rules.MINISTRY_WELCOME, load)

    assert "Welcome Team Lead" in csv
    assert "Member 1" in csv
    assert "Member 4" in csv


def test_mt_display_order_follows_sheet_columns():
    import engine
    sheet = ["Sound", "Projection", "Stream Director", "Camera 1", "Livestream sound", "Media Team Lead"]
    slots = ["Stream Director", "Camera 1", "Projection", "Projection 2", "Sound", "Livestream sound", "Cam 2"]
    out = engine.order_mt_display_roles(slots, "Media Team Lead", sheet_order=sheet)
    assert out == ["Sound", "Projection", "Projection 2", "Stream Director", "Camera 1",
                   "Livestream sound", "Media Team Lead", "Cam 2"]


def test_mt_display_order_lead_keeps_its_sheet_position():
    import engine
    sheet = ["Media Team Lead", "Camera 1", "sound"]
    out = engine.order_mt_display_roles(["Sound", "Camera 1"], "Media Team Lead", sheet_order=sheet)
    assert out == ["Media Team Lead", "Camera 1", "Sound"]


def test_mt_display_order_without_sheet_puts_lead_last():
    import engine
    out = engine.order_mt_display_roles(["Camera 1", "Sound"], "Lead")
    assert out == ["Camera 1", "Sound", "Lead"]


def test_unavailability_clashes_found_including_manual_edits_and_lead():
    import engine
    d1, d2 = date(2026, 10, 4), date(2026, 10, 11)
    roster = {
        d1: {"Details": "Alan", "Sound": "Alan", "Media Team Lead": "ben"},
        d2: {"Sound": "Alan", "Media Team Lead": ""},
    }
    unavail = {d1: {"Alan", "Ben"}, d2: set()}
    out = engine.find_unavailability_clashes(roster, unavail)
    assert out == [("Alan", d1, "Sound"), ("ben", d1, "Media Team Lead")]
    assert engine.find_unavailability_clashes(roster, {}) == []


def test_csv_load_stats_include_unavailable_dates_and_zero_shift_people():
    import engine
    roster = {
        date(2026, 11, 1): {"Sound": "Ben", "Media Team Lead": "Ben"},
        date(2026, 11, 8): {"Sound": "Micah", "Media Team Lead": ""},
    }
    services = [{"date": d, "hc": False, "combined": False, "notes": ""} for d in roster]
    unavail = engine.unavailable_dates_by_person(
        {"2026-11-08": {"Ben", "Zoe"}, "2026-11-01": {"Zoe"}, "2027-01-03": {"Ben"}},
        list(roster.keys()),
    )
    csv = export.roster_to_csv(roster, services, rules.MINISTRY_MEDIA_TECH,
                               {"Ben": 1, "Micah": 1}, unavailable=unavail,
                               all_names=["Ben", "Micah", "Zoe"])
    assert "Name,Shifts,Unavailable dates" in csv
    assert "Ben,1,08-Nov" in csv          # out-of-roster date dropped
    assert "Micah,1," in csv
    assert 'Zoe,0,"01-Nov, 08-Nov"' in csv  # 0-shift person listed, dates sorted
