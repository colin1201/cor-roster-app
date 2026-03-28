"""Tests for Welcome scheduling engine.

Tests written FIRST, before engine code.
"""

from datetime import date

import engine
import rules
import data


def _make_welcome_volunteers():
    """Realistic Welcome volunteer set matching the real Google Sheet."""
    return [
        # Leaders (4)
        {"name": "Cristal Lee", "lead": True, "member": False, "gender": "female", "couple_id": None, "senior": False},
        {"name": "Joshua Sum", "lead": True, "member": False, "gender": "male", "couple_id": None, "senior": False},
        {"name": "Jaslyn Wong", "lead": True, "member": False, "gender": "female", "couple_id": None, "senior": False},
        {"name": "Valerie Chee", "lead": True, "member": False, "gender": "female", "couple_id": None, "senior": False},
        # Members - males
        {"name": "Malcolm Lee", "lead": False, "member": True, "gender": "male", "couple_id": 1, "senior": False},
        {"name": "Samuel Stephens", "lead": False, "member": True, "gender": "male", "couple_id": None, "senior": False},
        {"name": "Daniel Lim", "lead": False, "member": True, "gender": "male", "couple_id": None, "senior": False},
        {"name": "Marc Liew", "lead": False, "member": True, "gender": "male", "couple_id": None, "senior": False},
        {"name": "David Sum", "lead": False, "member": True, "gender": "male", "couple_id": 2, "senior": True},
        {"name": "Alvin Chin", "lead": False, "member": True, "gender": "male", "couple_id": None, "senior": True},
        # Members - females
        {"name": "Jessline Lee", "lead": False, "member": True, "gender": "female", "couple_id": 1, "senior": False},
        {"name": "Happy Sum", "lead": False, "member": True, "gender": "female", "couple_id": 2, "senior": True},
        {"name": "Julia Ang", "lead": False, "member": True, "gender": "female", "couple_id": None, "senior": True},
        {"name": "Kathleen Chia", "lead": False, "member": True, "gender": "female", "couple_id": None, "senior": True},
        {"name": "Sim Choo Lee", "lead": False, "member": True, "gender": "female", "couple_id": None, "senior": True},
        {"name": "Christine Tan", "lead": False, "member": True, "gender": "female", "couple_id": None, "senior": True},
        {"name": "Lim Siew Lin", "lead": False, "member": True, "gender": "female", "couple_id": None, "senior": False},
        {"name": "Michelle Fong", "lead": False, "member": True, "gender": "female", "couple_id": None, "senior": False},
        {"name": "Ong Yiling", "lead": False, "member": True, "gender": "female", "couple_id": None, "senior": False},
        {"name": "Noven Koh", "lead": False, "member": True, "gender": "female", "couple_id": None, "senior": False},
        {"name": "Jenny Yap", "lead": False, "member": True, "gender": "female", "couple_id": None, "senior": False},
        {"name": "Nicole Ng", "lead": False, "member": True, "gender": "female", "couple_id": None, "senior": False},
    ]


def _make_dates(n=4):
    from datetime import timedelta
    start = date(2026, 4, 5)
    return [start + timedelta(weeks=i) for i in range(n)]


def _make_services(dates, all_hc=False):
    return [{"date": d, "hc": all_hc or engine.default_hc(d), "combined": False, "notes": ""} for d in dates]


# ---------------------------------------------------------------------------
# W1: HC scaling
# ---------------------------------------------------------------------------

class TestHCScaling:
    def test_hc_service_has_4_members(self):
        """HC = 1 lead + 4 members."""
        vols = _make_welcome_volunteers()
        dates = _make_dates(1)
        services = [{"date": dates[0], "hc": True, "combined": False, "notes": ""}]
        result = engine.generate_welcome_roster(vols, services, {}, seed=42)

        roster = result["roster"][dates[0]]
        members = [roster.get(f"Member {i}") for i in range(1, 5)]
        filled = [m for m in members if m]
        assert len(filled) == 4, f"HC service should have 4 members, got {len(filled)}: {members}"

    def test_non_hc_service_has_3_members(self):
        """Non-HC = 1 lead + 3 members."""
        vols = _make_welcome_volunteers()
        dates = _make_dates(1)
        services = [{"date": dates[0], "hc": False, "combined": False, "notes": ""}]
        result = engine.generate_welcome_roster(vols, services, {}, seed=42)

        roster = result["roster"][dates[0]]
        members = [roster.get(f"Member {i}") for i in range(1, 4)]
        filled = [m for m in members if m]
        assert len(filled) == 3, f"Non-HC should have 3 members, got {len(filled)}"
        # Member 4 should be empty
        assert roster.get("Member 4", "") == ""

    def test_lead_always_assigned(self):
        vols = _make_welcome_volunteers()
        dates = _make_dates(4)
        services = _make_services(dates)
        result = engine.generate_welcome_roster(vols, services, {}, seed=42)

        for d in dates:
            lead = result["roster"][d].get(rules.W_LEAD_ROLE)
            assert lead, f"No lead assigned on {d}"


# ---------------------------------------------------------------------------
# W2/W3/W4: Eligibility and separation
# ---------------------------------------------------------------------------

class TestEligibility:
    def test_only_leads_in_lead_role(self):
        """W2: Only lead-qualified people can be lead."""
        vols = _make_welcome_volunteers()
        lead_names = {v["name"] for v in vols if v["lead"]}
        dates = _make_dates(4)
        services = _make_services(dates)
        result = engine.generate_welcome_roster(vols, services, {}, seed=42)

        for d in dates:
            lead = result["roster"][d].get(rules.W_LEAD_ROLE)
            if lead:
                assert lead in lead_names, f"{lead} is not a qualified lead"

    def test_only_members_in_member_roles(self):
        """W3: Only member-qualified people in member slots."""
        vols = _make_welcome_volunteers()
        member_names = {v["name"] for v in vols if v["member"]}
        dates = _make_dates(4)
        services = _make_services(dates)
        result = engine.generate_welcome_roster(vols, services, {}, seed=42)

        for d in dates:
            roster = result["roster"][d]
            for i in range(1, 5):
                person = roster.get(f"Member {i}", "")
                if person:
                    assert person in member_names, f"{person} in Member {i} but not a qualified member"

    def test_lead_not_in_member_slot(self):
        """W4: Strict separation — leads don't fill member slots."""
        vols = _make_welcome_volunteers()
        lead_names = {v["name"] for v in vols if v["lead"]}
        dates = _make_dates(4)
        services = _make_services(dates)
        result = engine.generate_welcome_roster(vols, services, {}, seed=42)

        for d in dates:
            roster = result["roster"][d]
            for i in range(1, 5):
                person = roster.get(f"Member {i}", "")
                if person:
                    assert person not in lead_names, f"Lead {person} found in Member {i}"


# ---------------------------------------------------------------------------
# W5: Male Member 1
# ---------------------------------------------------------------------------

class TestMaleMember1:
    def test_member_1_is_male(self):
        """Member 1 should be male when males are available."""
        vols = _make_welcome_volunteers()
        male_members = {v["name"] for v in vols if v["member"] and v["gender"] == "male"}
        dates = _make_dates(4)
        services = _make_services(dates)
        result = engine.generate_welcome_roster(vols, services, {}, seed=42)

        for d in dates:
            m1 = result["roster"][d].get("Member 1", "")
            if m1:
                assert m1 in male_members, f"Member 1 on {d} is {m1}, not male"

    def test_member_1_fallback_to_female_with_warning(self):
        """If no males available, fill with female but warn."""
        # Remove all males from member pool
        vols = [v for v in _make_welcome_volunteers() if not (v["member"] and v["gender"] == "male")]
        dates = _make_dates(1)
        services = _make_services(dates)
        result = engine.generate_welcome_roster(vols, services, {}, seed=42)

        m1 = result["roster"][dates[0]].get("Member 1", "")
        assert m1, "Member 1 should still be filled even without males"

        # Should have a warning
        m1_warnings = [w for w in result["warnings"] if w["role"] == "Member 1"]
        assert len(m1_warnings) > 0, "Should warn about no male for Member 1"


# ---------------------------------------------------------------------------
# W6: Senior citizen requirement
# ---------------------------------------------------------------------------

class TestSeniorCitizen:
    def test_at_least_one_senior_per_service(self):
        """At least one member should be a senior citizen."""
        vols = _make_welcome_volunteers()
        senior_names = {v["name"] for v in vols if v["senior"]}
        dates = _make_dates(4)
        services = _make_services(dates)
        result = engine.generate_welcome_roster(vols, services, {}, seed=42)

        for d in dates:
            roster = result["roster"][d]
            members = [roster.get(f"Member {i}", "") for i in range(1, 5)]
            members = [m for m in members if m]
            has_senior = any(m in senior_names for m in members)
            assert has_senior, f"No senior citizen in members on {d}: {members}"

    def test_no_senior_available_warns(self):
        """If no seniors available, warn but still fill slots."""
        vols = [v for v in _make_welcome_volunteers() if not v["senior"]]
        dates = _make_dates(1)
        services = _make_services(dates)
        result = engine.generate_welcome_roster(vols, services, {}, seed=42)

        # Should have a warning about missing senior
        senior_warnings = [w for w in result["warnings"] if "senior" in w["message"].lower()]
        assert len(senior_warnings) > 0, "Should warn about no senior citizen"


# ---------------------------------------------------------------------------
# W7/W8/W9/W10: Couples
# ---------------------------------------------------------------------------

class TestCouples:
    def test_couples_serve_together(self):
        """W8: If one partner is assigned, the other must be too."""
        vols = _make_welcome_volunteers()
        couple_map = data.get_couple_map(vols)
        dates = _make_dates(8)  # More dates to increase chance of couples being picked
        services = _make_services(dates, all_hc=True)  # HC for more member slots
        result = engine.generate_welcome_roster(vols, services, {}, seed=42)

        for d in dates:
            roster = result["roster"][d]
            members = [roster.get(f"Member {i}", "") for i in range(1, 5)]
            members = [m for m in members if m]
            for m in members:
                if m in couple_map:
                    partner = couple_map[m]
                    assert partner in members, \
                        f"{m}'s partner {partner} not in same service on {d}: {members}"

    def test_couple_not_selected_if_partner_unavailable(self):
        """W9: If partner is unavailable, don't select the coupled member."""
        vols = _make_welcome_volunteers()
        couple_map = data.get_couple_map(vols)
        dates = _make_dates(4)
        services = _make_services(dates, all_hc=True)

        # Make Jessline unavailable on all dates — Malcolm should not be selected
        unavail = {d: {"Jessline Lee"} for d in dates}
        result = engine.generate_welcome_roster(vols, services, unavail, seed=42)

        for d in dates:
            roster = result["roster"][d]
            members = [roster.get(f"Member {i}", "") for i in range(1, 5)]
            assert "Malcolm Lee" not in members, \
                f"Malcolm selected on {d} despite Jessline being unavailable"

    def test_leads_exempt_from_couples_rule(self):
        """W7: Couples rule applies to members only. A lead with couple_id is exempt."""
        # Create a scenario where a lead happens to have a couple_id
        vols = _make_welcome_volunteers()
        # Give Joshua Sum (a lead) a couple_id that matches no one
        for v in vols:
            if v["name"] == "Joshua Sum":
                v["couple_id"] = 99
        dates = _make_dates(4)
        services = _make_services(dates)
        result = engine.generate_welcome_roster(vols, services, {}, seed=42)

        # Joshua should still be assignable as lead without needing a partner
        lead_dates = [d for d in dates if result["roster"][d].get(rules.W_LEAD_ROLE) == "Joshua Sum"]
        # Joshua should appear as lead at least once over 4 dates
        assert len(lead_dates) > 0, "Joshua should be assigned as lead even with orphan couple_id"


# ---------------------------------------------------------------------------
# W10: Welcome lead counts toward load
# ---------------------------------------------------------------------------

class TestWelcomeLoadCounting:
    def test_lead_counts_toward_load(self):
        """W10: Unlike Media Tech, Welcome Team Lead counts toward shift load."""
        vols = _make_welcome_volunteers()
        dates = _make_dates(4)
        services = _make_services(dates)
        result = engine.generate_welcome_roster(vols, services, {}, seed=42)

        # Count lead assignments
        lead_assignments = {}
        for d in dates:
            lead = result["roster"][d].get(rules.W_LEAD_ROLE, "")
            if lead:
                lead_assignments[lead] = lead_assignments.get(lead, 0) + 1

        # Load counts should include lead assignments
        for name, count in lead_assignments.items():
            assert result["load_counts"].get(name, 0) >= count, \
                f"{name} has {count} lead assignments but load is {result['load_counts'].get(name, 0)}"


# ---------------------------------------------------------------------------
# Core scheduling rules (applied to Welcome)
# ---------------------------------------------------------------------------

class TestWelcomeCoreRules:
    def test_unavailability_enforcement(self):
        """U2: Unavailable people never assigned."""
        vols = _make_welcome_volunteers()
        dates = _make_dates(4)
        services = _make_services(dates)
        unavail = {d: {"Cristal Lee", "Malcolm Lee"} for d in dates}
        result = engine.generate_welcome_roster(vols, services, unavail, seed=42)

        for d in dates:
            roster = result["roster"][d]
            all_assigned = [roster.get(r, "") for r in [rules.W_LEAD_ROLE] + [f"Member {i}" for i in range(1, 5)]]
            assert "Cristal Lee" not in all_assigned
            assert "Malcolm Lee" not in all_assigned

    def test_no_duplicate_in_same_service(self):
        """No person appears twice in the same service."""
        vols = _make_welcome_volunteers()
        dates = _make_dates(4)
        services = _make_services(dates, all_hc=True)
        result = engine.generate_welcome_roster(vols, services, {}, seed=42)

        for d in dates:
            roster = result["roster"][d]
            people = [roster.get(r, "") for r in [rules.W_LEAD_ROLE] + [f"Member {i}" for i in range(1, 5)]]
            people = [p for p in people if p]
            assert len(people) == len(set(people)), f"Duplicate on {d}: {people}"

    def test_deterministic(self):
        """U8: Same seed = same roster."""
        vols = _make_welcome_volunteers()
        dates = _make_dates(4)
        services = _make_services(dates)
        r1 = engine.generate_welcome_roster(vols, services, {}, seed=42)
        r2 = engine.generate_welcome_roster(vols, services, {}, seed=42)

        for d in dates:
            for role in [rules.W_LEAD_ROLE] + [f"Member {i}" for i in range(1, 5)]:
                assert r1["roster"][d].get(role) == r2["roster"][d].get(role), \
                    f"Non-deterministic on {d} {role}"
