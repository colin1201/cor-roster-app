"""Tests for rules.py — verify all constants are correct."""

import rules


def test_mt_tech_roles_has_four():
    assert len(rules.MT_TECH_ROLES) == 4


def test_mt_tech_roles_content():
    assert "Stream Director" in rules.MT_TECH_ROLES
    assert "Camera 1" in rules.MT_TECH_ROLES
    assert "Projection" in rules.MT_TECH_ROLES
    assert "Sound" in rules.MT_TECH_ROLES


def test_mt_primary_leads_has_three():
    assert len(rules.MT_PRIMARY_LEADS) == 3


def test_mt_primary_leads_content():
    assert "Gavin" in rules.MT_PRIMARY_LEADS
    assert "Ben" in rules.MT_PRIMARY_LEADS
    assert "Mich Lo" in rules.MT_PRIMARY_LEADS


def test_mt_fallback_lead():
    assert rules.MT_FALLBACK_LEAD == "Darrell"


def test_mt_cam2_not_in_tech_roles():
    assert rules.MT_CAM2_ROLE not in rules.MT_TECH_ROLES


def test_welcome_hc_member_count():
    assert rules.W_HC_MEMBER_COUNT == 4
    assert len(rules.W_MEMBER_ROLES_HC) == 4


def test_welcome_non_hc_member_count():
    assert rules.W_NON_HC_MEMBER_COUNT == 3
    assert len(rules.W_MEMBER_ROLES_NON_HC) == 3


def test_hc_default_sundays():
    assert rules.HC_DEFAULT_SUNDAYS == [1, 3]


def test_combined_default_sundays():
    assert rules.COMBINED_DEFAULT_SUNDAYS == [1]


def test_roster_month_count():
    assert rules.ROSTER_MONTH_COUNT == 3


def test_mt_display_order_includes_all_roles():
    for role in rules.MT_TECH_ROLES:
        assert role in rules.MT_ROLES_DISPLAY
    assert rules.MT_LEAD_ROLE in rules.MT_ROLES_DISPLAY
    assert rules.MT_CAM2_ROLE in rules.MT_ROLES_DISPLAY
    assert "Details" in rules.MT_ROLES_DISPLAY


def test_welcome_display_order_includes_all_roles():
    assert rules.W_LEAD_ROLE in rules.W_ROLES_DISPLAY_HC
    for role in rules.W_MEMBER_ROLES_HC:
        assert role in rules.W_ROLES_DISPLAY_HC
    assert "Details" in rules.W_ROLES_DISPLAY_HC
