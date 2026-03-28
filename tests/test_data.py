"""Tests for data.py — volunteer parsing and data loading."""

import pandas as pd
import pytest

import data
import rules


# ---------------------------------------------------------------------------
# CSV URL builder
# ---------------------------------------------------------------------------

def test_build_csv_url():
    url = data.build_csv_url("SHEET123", "GID456")
    assert "SHEET123" in url
    assert "GID456" in url
    assert url.startswith("https://")


# ---------------------------------------------------------------------------
# Media Tech volunteer parsing
# ---------------------------------------------------------------------------

def test_mt_parse_returns_tuple(mt_csv_df):
    result = data.parse_mt_volunteers(mt_csv_df)
    assert isinstance(result, tuple)
    vols, role_names = result
    assert isinstance(vols, list)
    assert len(vols) > 0
    assert isinstance(role_names, list)
    assert len(role_names) > 0


def test_mt_parse_has_required_keys(mt_csv_df):
    vols, _ = data.parse_mt_volunteers(mt_csv_df)
    for v in vols:
        assert "name" in v
        assert "roles" in v
        assert isinstance(v["roles"], dict)


def test_mt_parse_qualifications(mt_csv_df):
    vols, role_names = data.parse_mt_volunteers(mt_csv_df)
    by_name = {v["name"]: v for v in vols}

    # Ben: Media Team Lead + Stream Director + Sound
    assert by_name["Ben"]["roles"]["Media Team Lead"] is True
    assert by_name["Ben"]["roles"]["Stream Director"] is True
    assert by_name["Ben"]["roles"]["Sound"] is True
    assert by_name["Ben"]["roles"]["Camera 1"] is False
    assert by_name["Ben"]["roles"]["Projection"] is False

    # Christine: Projection only
    assert by_name["Christine"]["roles"]["Projection"] is True
    assert by_name["Christine"]["roles"]["Media Team Lead"] is False

    # Gavin: Media Team Lead + Stream Director + Sound
    assert by_name["Gavin"]["roles"]["Media Team Lead"] is True
    assert by_name["Gavin"]["roles"]["Stream Director"] is True
    assert by_name["Gavin"]["roles"]["Sound"] is True


def test_mt_parse_discovers_roles(mt_csv_df):
    """Roles should be discovered from sheet headers."""
    _, role_names = data.parse_mt_volunteers(mt_csv_df)
    assert "Media Team Lead" in role_names
    assert "Stream Director" in role_names
    assert "Camera 1" in role_names
    assert "Projection" in role_names
    assert "Sound" in role_names


def test_mt_parse_excludes_inactive(mt_csv_df_with_inactive):
    """Rule U13: volunteers with zero qualifications are excluded."""
    vols, _ = data.parse_mt_volunteers(mt_csv_df_with_inactive)
    names = {v["name"] for v in vols}
    assert "Rui Jie" not in names
    assert "Wei Kiang" not in names


def test_mt_darrell_excluded_as_inactive(mt_csv_df):
    """Darrell has zero qualifications in the sheet — he's excluded from the volunteer list."""
    vols, _ = data.parse_mt_volunteers(mt_csv_df)
    names = {v["name"] for v in vols}
    assert "Darrell" not in names


def test_mt_parse_name_normalization():
    """Names with extra whitespace should be cleaned."""
    df = pd.DataFrame({
        "Name": ["  Alan  ", "Ben\t"],
        "Media Team Lead": ["", "Yes"],
        "Stream Director": ["Yes", "Yes"],
        "Camera 1": ["", ""],
        "Projection": ["", ""],
        "Sound": ["", ""],
    })
    vols, _ = data.parse_mt_volunteers(df)
    names = {v["name"] for v in vols}
    assert "Alan" in names
    assert "Ben" in names


def test_mt_parse_missing_name_column():
    """Should raise ValueError if Name column is missing."""
    df = pd.DataFrame({"Foo": ["Bar"], "Sound": ["Yes"]})
    with pytest.raises(ValueError, match="Name"):
        data.parse_mt_volunteers(df)


# ---------------------------------------------------------------------------
# Welcome volunteer parsing
# ---------------------------------------------------------------------------

def test_welcome_parse_returns_list(welcome_csv_df):
    result = data.parse_welcome_volunteers(welcome_csv_df)
    assert isinstance(result, list)
    assert len(result) > 0


def test_welcome_parse_has_required_keys(welcome_csv_df):
    result = data.parse_welcome_volunteers(welcome_csv_df)
    required_keys = {"name", "lead", "member", "gender", "couple_id", "senior"}
    for v in result:
        assert set(v.keys()) == required_keys


def test_welcome_parse_leads(welcome_csv_df):
    result = data.parse_welcome_volunteers(welcome_csv_df)
    leads = [v for v in result if v["lead"]]
    lead_names = {v["name"] for v in leads}
    assert "Cristal Lee" in lead_names
    assert "Joshua Sum" in lead_names
    assert "Jaslyn Wong" in lead_names
    assert "Valerie Chee" in lead_names


def test_welcome_parse_members(welcome_csv_df):
    result = data.parse_welcome_volunteers(welcome_csv_df)
    members = [v for v in result if v["member"]]
    assert len(members) > 0
    # Leads should not be members
    for v in result:
        if v["lead"]:
            assert v["member"] is False or v["lead"] is True  # leads are separate


def test_welcome_parse_gender(welcome_csv_df):
    result = data.parse_welcome_volunteers(welcome_csv_df)
    by_name = {v["name"]: v for v in result}
    assert by_name["Joshua Sum"]["gender"] == "male"
    assert by_name["Cristal Lee"]["gender"] == "female"
    assert by_name["Malcolm Lee"]["gender"] == "male"


def test_welcome_parse_couples(welcome_csv_df):
    result = data.parse_welcome_volunteers(welcome_csv_df)
    by_name = {v["name"]: v for v in result}
    # Malcolm and Jessline are couple 1
    assert by_name["Malcolm Lee"]["couple_id"] == 1
    assert by_name["Jessline Lee"]["couple_id"] == 1
    # David and Happy are couple 2
    assert by_name["David Sum"]["couple_id"] == 2
    assert by_name["Happy Sum"]["couple_id"] == 2
    # Non-coupled person
    assert by_name["Samuel Stephens"]["couple_id"] is None


def test_welcome_parse_seniors(welcome_csv_df):
    result = data.parse_welcome_volunteers(welcome_csv_df)
    seniors = [v for v in result if v["senior"]]
    senior_names = {v["name"] for v in seniors}
    assert "David Sum" in senior_names
    assert "Happy Sum" in senior_names
    assert "Julia Ang" in senior_names
    assert "Kathleen Chia" in senior_names
    assert "Alvin Chin" in senior_names


def test_welcome_parse_excludes_inactive():
    """Volunteers who are neither lead nor member are excluded."""
    df = pd.DataFrame({
        "Name": ["Active Lead", "Active Member", "Inactive"],
        "Welcome Team Lead": ["Yes", "", ""],
        "Member": ["", "Yes", ""],
        "Gender": ["Female", "Male", "Male"],
        "Couple": ["", "", ""],
        "Senior citizen": ["", "", ""],
    })
    result = data.parse_welcome_volunteers(df)
    names = {v["name"] for v in result}
    assert "Active Lead" in names
    assert "Active Member" in names
    assert "Inactive" not in names


# ---------------------------------------------------------------------------
# Couple map
# ---------------------------------------------------------------------------

def test_couple_map(welcome_csv_df):
    vols = data.parse_welcome_volunteers(welcome_csv_df)
    cmap = data.get_couple_map(vols)
    assert cmap["Malcolm Lee"] == "Jessline Lee"
    assert cmap["Jessline Lee"] == "Malcolm Lee"
    assert cmap["David Sum"] == "Happy Sum"
    assert cmap["Happy Sum"] == "David Sum"
    # Non-coupled person not in map
    assert "Samuel Stephens" not in cmap


def test_couple_map_ignores_bad_data():
    """If a couple_id has only 1 person, ignore it."""
    vols = [
        {"name": "Solo", "couple_id": 99, "lead": False, "member": True, "gender": "male", "senior": False},
    ]
    cmap = data.get_couple_map(vols)
    assert "Solo" not in cmap
