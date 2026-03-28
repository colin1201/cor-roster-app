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
