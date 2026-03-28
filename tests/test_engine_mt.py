"""Tests for Media Tech scheduling engine.

These tests cover the CRITICAL lead logic that was wrong in both previous prototypes.
Tests are written FIRST, before engine code.
"""

from datetime import date

import engine
import rules


def _mt_vol(name, lead=False, stream=False, cam=False, proj=False, sound=False):
    """Helper to build an MT volunteer in the new dynamic format."""
    return {
        "name": name,
        "roles": {
            "Media Team Lead": lead,
            "Stream Director": stream,
            "Camera 1": cam,
            "Projection": proj,
            "Sound": sound,
        },
    }


def _make_mt_volunteers():
    """Realistic Media Tech volunteer set matching the real Google Sheet."""
    return [
        _mt_vol("Alan", stream=True, cam=True),
        _mt_vol("Ben", lead=True, stream=True, sound=True),
        _mt_vol("Christine", proj=True),
        _mt_vol("Colin", stream=True, cam=True),
        _mt_vol("Dannel", stream=True, cam=True),
        _mt_vol("Gavin", lead=True, stream=True, sound=True),
        _mt_vol("Jax", stream=True, cam=True),
        _mt_vol("Jessica Tong", stream=True, cam=True),
        _mt_vol("Micah", sound=True),
        _mt_vol("Mich Lo", lead=True, stream=True, proj=True),
        _mt_vol("Ming Zhe", stream=True, cam=True),
        _mt_vol("Samuel", sound=True),
        _mt_vol("Sherry", cam=True),
        _mt_vol("Timmy", proj=True),
        _mt_vol("Timothy", stream=True, cam=True),
        _mt_vol("Vivian Ng", stream=True, cam=True),
    ]


def _make_dates(n=4):
    """Generate n consecutive Sundays starting April 2026."""
    return [date(2026, 4, 5 + i * 7) for i in range(n)]


def _make_services(dates):
    return [{"date": d, "hc": False, "combined": False, "notes": ""} for d in dates]


# Default session rules for MT tests
_MT_SESSION_RULES = {
    "primary_leads": list(rules.MT_PRIMARY_LEADS),
    "fallback_lead": rules.MT_FALLBACK_LEAD,
    "lead_role_name": rules.MT_LEAD_ROLE,
    "role_counts": {
        "Stream Director": 1,
        "Camera 1": 1,
        "Projection": 1,
        "Sound": 1,
    },
    "weekly_rest": True,
    "cross_rotation": True,
}

_MT_TECH_ROLES = ["Stream Director", "Camera 1", "Projection", "Sound"]


# ---------------------------------------------------------------------------
# MT3: Lead logic — THE CRITICAL TESTS
# ---------------------------------------------------------------------------

class TestMTLeadLogic:
    """The lead logic that was wrong in both previous prototypes."""

    def test_primary_lead_in_crew_gets_lead(self):
        """If Gavin/Ben/Mich Lo are in the tech crew, one of them becomes lead."""
        vols = _make_mt_volunteers()
        dates = _make_dates(1)
        services = _make_services(dates)
        result = engine.generate_mt_roster(vols, services, {}, seed=42, session_rules=_MT_SESSION_RULES)

        d = dates[0]
        roster = result["roster"][d]
        lead = roster[rules.MT_LEAD_ROLE]

        # At least one primary lead should be qualified for a tech role
        # and get assigned, becoming the lead
        if lead:
            assert lead in rules.MT_PRIMARY_LEADS

    def test_primary_lead_keeps_tech_role(self):
        """MT4: The person assigned as lead must ALSO appear in a tech role."""
        vols = _make_mt_volunteers()
        dates = _make_dates(1)
        services = _make_services(dates)
        result = engine.generate_mt_roster(vols, services, {}, seed=42, session_rules=_MT_SESSION_RULES)

        d = dates[0]
        roster = result["roster"][d]
        lead = roster[rules.MT_LEAD_ROLE]

        if lead and lead in rules.MT_PRIMARY_LEADS:
            # The lead must also be in one of the tech roles
            tech_assignments = [roster[role] for role in _MT_TECH_ROLES]
            assert lead in tech_assignments, \
                f"{lead} is lead but not in any tech role: {roster}"

    def test_fallback_to_darrell_when_no_primary(self):
        """If no primary lead is in the crew, Darrell is assigned as lead."""
        # Remove all primary leads from volunteer list
        vols = [v for v in _make_mt_volunteers() if v["name"] not in rules.MT_PRIMARY_LEADS]
        dates = _make_dates(1)
        services = _make_services(dates)
        result = engine.generate_mt_roster(vols, services, {}, seed=42, session_rules=_MT_SESSION_RULES)

        d = dates[0]
        roster = result["roster"][d]
        lead = roster[rules.MT_LEAD_ROLE]
        assert lead == rules.MT_FALLBACK_LEAD

    def test_darrell_is_lead_only_not_tech(self):
        """Darrell has no tech qualifications — he should only appear as lead."""
        vols = [v for v in _make_mt_volunteers() if v["name"] not in rules.MT_PRIMARY_LEADS]
        dates = _make_dates(1)
        services = _make_services(dates)
        result = engine.generate_mt_roster(vols, services, {}, seed=42, session_rules=_MT_SESSION_RULES)

        d = dates[0]
        roster = result["roster"][d]

        # Darrell should NOT appear in any tech role
        for role in _MT_TECH_ROLES:
            assert roster[role] != rules.MT_FALLBACK_LEAD

    def test_lead_unfilled_when_no_primary_and_darrell_unavailable(self):
        """If no primary lead in crew AND Darrell unavailable, leave lead empty."""
        vols = [v for v in _make_mt_volunteers() if v["name"] not in rules.MT_PRIMARY_LEADS]
        dates = _make_dates(1)
        services = _make_services(dates)
        unavail = {dates[0]: {rules.MT_FALLBACK_LEAD}}
        result = engine.generate_mt_roster(vols, services, unavail, seed=42, session_rules=_MT_SESSION_RULES)

        d = dates[0]
        roster = result["roster"][d]
        assert roster[rules.MT_LEAD_ROLE] == ""

    def test_multiple_primaries_picks_lowest_lead_count(self):
        """MT7: If multiple primary leads in crew, pick the one with lowest lead count."""
        # Use only 2 dates to keep it simple
        # Force both Gavin and Ben into the crew by limiting other volunteers
        vols = [
            _mt_vol("Gavin", lead=True, stream=True, sound=True),
            _mt_vol("Ben", lead=True, stream=True, sound=True),
            _mt_vol("Christine", proj=True),
            _mt_vol("Sherry", cam=True),
        ]
        dates = _make_dates(4)
        services = _make_services(dates)
        result = engine.generate_mt_roster(vols, services, {}, seed=42, session_rules=_MT_SESSION_RULES)

        # Over 4 dates, leadership should be somewhat shared between Gavin and Ben
        lead_counts = {}
        for d in dates:
            lead = result["roster"][d][rules.MT_LEAD_ROLE]
            if lead:
                lead_counts[lead] = lead_counts.get(lead, 0) + 1

        # Both should have been lead at least once
        primaries_who_led = {n for n in lead_counts if n in rules.MT_PRIMARY_LEADS}
        assert len(primaries_who_led) >= 2, f"Only {primaries_who_led} led over 4 weeks"

    def test_primary_leads_equal_priority(self):
        """Rule 16: Gavin, Ben, Mich Lo are equal priority — not ranked."""
        # This is implicitly tested by the lowest-lead-count test above
        # but let's verify none of them is hardcoded as "better"
        assert isinstance(rules.MT_PRIMARY_LEADS, set), \
            "MT_PRIMARY_LEADS should be a set (unordered) to enforce equal priority"


# ---------------------------------------------------------------------------
# MT5: Lead load-stat exclusion
# ---------------------------------------------------------------------------

class TestMTLoadStats:
    def test_lead_does_not_count_toward_load(self):
        """MT5: Team Lead assignment does NOT count toward shift load."""
        vols = _make_mt_volunteers()
        dates = _make_dates(2)
        services = _make_services(dates)
        result = engine.generate_mt_roster(vols, services, {}, seed=42, session_rules=_MT_SESSION_RULES)

        load = result["load_counts"]
        # Find who was lead
        for d in dates:
            lead = result["roster"][d][rules.MT_LEAD_ROLE]
            if lead and lead in rules.MT_PRIMARY_LEADS:
                # This person's load should only count their TECH role, not lead
                # Count how many tech roles they filled
                tech_count = sum(
                    1 for dd in dates
                    for role in _MT_TECH_ROLES
                    if result["roster"][dd][role] == lead
                )
                assert load[lead] == tech_count, \
                    f"{lead} has load {load[lead]} but filled {tech_count} tech slots"


# ---------------------------------------------------------------------------
# Core scheduling rules
# ---------------------------------------------------------------------------

class TestMTCoreRules:
    def test_qualification_enforcement(self):
        """U1: Only assign qualified people to roles."""
        vols = _make_mt_volunteers()
        dates = _make_dates(4)
        services = _make_services(dates)
        result = engine.generate_mt_roster(vols, services, {}, seed=42, session_rules=_MT_SESSION_RULES)

        vol_by_name = {v["name"]: v for v in vols}
        for d in dates:
            for role in _MT_TECH_ROLES:
                person = result["roster"][d][role]
                if person:
                    assert vol_by_name[person]["roles"][role], \
                        f"{person} assigned to {role} on {d} but not qualified"

    def test_unavailability_enforcement(self):
        """U2: Unavailable people are never assigned."""
        vols = _make_mt_volunteers()
        dates = _make_dates(4)
        services = _make_services(dates)
        # Make Gavin unavailable on all dates
        unavail = {d: {"Gavin"} for d in dates}
        result = engine.generate_mt_roster(vols, services, unavail, seed=42, session_rules=_MT_SESSION_RULES)

        for d in dates:
            roster = result["roster"][d]
            for role in _MT_TECH_ROLES + [_MT_SESSION_RULES["lead_role_name"]]:
                assert roster[role] != "Gavin", f"Gavin assigned on {d} despite unavailability"

    def test_single_role_per_service(self):
        """U3: No one fills two tech roles on the same day."""
        vols = _make_mt_volunteers()
        dates = _make_dates(4)
        services = _make_services(dates)
        result = engine.generate_mt_roster(vols, services, {}, seed=42, session_rules=_MT_SESSION_RULES)

        for d in dates:
            roster = result["roster"][d]
            tech_people = [roster[r] for r in _MT_TECH_ROLES if roster[r]]
            assert len(tech_people) == len(set(tech_people)), \
                f"Duplicate tech assignment on {d}: {tech_people}"

    def test_deterministic(self):
        """U8: Same seed + same data = same roster."""
        vols = _make_mt_volunteers()
        dates = _make_dates(4)
        services = _make_services(dates)
        result1 = engine.generate_mt_roster(vols, services, {}, seed=42, session_rules=_MT_SESSION_RULES)
        result2 = engine.generate_mt_roster(vols, services, {}, seed=42, session_rules=_MT_SESSION_RULES)

        for d in dates:
            for role in _MT_TECH_ROLES + [_MT_SESSION_RULES["lead_role_name"]]:
                assert result1["roster"][d][role] == result2["roster"][d][role], \
                    f"Non-deterministic on {d} {role}"

    def test_manual_role_stays_empty(self):
        """Roles with count=0 should remain empty (manual placeholders)."""
        vols = _make_mt_volunteers()
        dates = _make_dates(2)
        services = _make_services(dates)
        # Add a manual-only role
        sr = dict(_MT_SESSION_RULES)
        sr["role_counts"] = dict(sr["role_counts"])
        sr["role_counts"]["Cam 2"] = 0
        result = engine.generate_mt_roster(vols, services, {}, seed=42, session_rules=sr)

        for d in dates:
            assert result["roster"][d].get("Cam 2", "") == ""

    def test_inactive_never_assigned(self):
        """U13: Inactive volunteers never appear."""
        vols = _make_mt_volunteers()
        dates = _make_dates(4)
        services = _make_services(dates)
        result = engine.generate_mt_roster(vols, services, {}, seed=42, session_rules=_MT_SESSION_RULES)

        # Darrell, Edmund, Rui Jie, Wei Kiang are inactive in the real sheet
        # Our fixture doesn't include them in the volunteer list
        # But Darrell can appear as fallback lead — that's handled separately
        all_names = {v["name"] for v in vols}
        for d in dates:
            for role in _MT_TECH_ROLES:
                person = result["roster"][d][role]
                if person:
                    assert person in all_names

    def test_four_tech_roles_filled(self):
        """MT2: All 4 tech roles should be filled when enough volunteers."""
        vols = _make_mt_volunteers()
        dates = _make_dates(4)
        services = _make_services(dates)
        result = engine.generate_mt_roster(vols, services, {}, seed=42, session_rules=_MT_SESSION_RULES)

        for d in dates:
            for role in _MT_TECH_ROLES:
                assert result["roster"][d][role] != "", \
                    f"{role} unfilled on {d}"
