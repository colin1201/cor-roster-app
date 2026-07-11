"""Regression tests for the July 2026 bug-fix pass.

Covers three defects the original suite missed:
  Fix 3 — couples could drag a Lead into a Member slot; and a member was
          wrongly blocked when their LEAD partner was unavailable (W7).
  Fix 4 — locked cells didn't count toward load, so lock-and-regenerate
          broke fairness.
  Fix 5 — non-HC blanking was hardcoded to "Member 4" instead of being
          derived from the session member counts, and blanked locked cells.
"""

from datetime import date, timedelta

import engine
import rules


def _make_dates(n=4):
    start = date(2026, 4, 5)  # a Sunday
    return [start + timedelta(weeks=i) for i in range(n)]


def _w_vol(name, lead=False, member=False, gender="female", couple_id=None, senior=False):
    return {
        "name": name, "lead": lead, "member": member,
        "gender": gender, "couple_id": couple_id, "senior": senior,
    }


def _mt_vol(name, lead=False, stream=False, cam=False, proj=False, sound=False):
    return {
        "name": name,
        "roles": {
            "Media Team Lead": lead, "Stream Director": stream,
            "Camera 1": cam, "Projection": proj, "Sound": sound,
        },
    }


_MT_RULES = {
    "primary_leads": list(rules.MT_PRIMARY_LEADS),
    "fallback_lead": rules.MT_FALLBACK_LEAD,
    "lead_role_name": rules.MT_LEAD_ROLE,
    "role_counts": {"Stream Director": 1, "Camera 1": 1, "Projection": 1, "Sound": 1},
    "weekly_rest": False,   # off so single-date load assertions are exact
    "cross_rotation": True,
}

_W_RULES = {
    "min_males": 1, "min_seniors": 1, "couples_together": True,
    "weekly_rest": False, "hc_member_count": 4, "non_hc_member_count": 3,
}


# ---------------------------------------------------------------------------
# Fix 3 — Couples: lead may not be dragged into a member slot (W7)
# ---------------------------------------------------------------------------

class TestCoupleLeadPartner:
    def _vols_with_lead_member_couple(self):
        # Bella (member) is coupled (id 9) to Leo (a LEAD). They must NOT be
        # treated as a member-member couple.
        return [
            _w_vol("Cara", lead=True, gender="female"),
            _w_vol("Leo", lead=True, gender="male", couple_id=9),
            _w_vol("Bella", member=True, gender="female", couple_id=9, senior=True),
            _w_vol("Max", member=True, gender="male"),
            _w_vol("Nora", member=True, gender="female", senior=True),
            _w_vol("Owen", member=True, gender="male"),
            _w_vol("Pia", member=True, gender="female", senior=True),
        ]

    def test_lead_partner_never_in_member_slot(self):
        vols = self._vols_with_lead_member_couple()
        dates = _make_dates(6)
        services = [{"date": d, "hc": True, "combined": False, "notes": ""} for d in dates]
        result = engine.generate_welcome_roster(vols, services, {}, seed=7, session_rules=_W_RULES)

        for d in dates:
            roster = result["roster"][d]
            member_slots = [roster.get(f"Member {i}", "") for i in range(1, 5)]
            assert "Leo" not in member_slots, \
                f"Lead 'Leo' was dragged into a member slot on {d}: {member_slots}"

    def test_member_not_blocked_by_unavailable_lead_partner(self):
        """W7 mirror defect: a member must stay selectable even when their
        LEAD partner is unavailable (leads are exempt from couples rules)."""
        vols = self._vols_with_lead_member_couple()
        dates = _make_dates(4)
        services = [{"date": d, "hc": True, "combined": False, "notes": ""} for d in dates]
        # Leo (the lead partner) is unavailable everywhere.
        unavail = {d: {"Leo"} for d in dates}
        result = engine.generate_welcome_roster(vols, services, unavail, seed=7, session_rules=_W_RULES)

        # Bella should still be assignable on at least one date.
        assigned_somewhere = any(
            "Bella" in [result["roster"][d].get(f"Member {i}", "") for i in range(1, 5)]
            for d in dates
        )
        assert assigned_somewhere, "Bella was wrongly blocked by her unavailable LEAD partner"

    def test_member_member_couple_still_together(self):
        """Regression: genuine member-member couples still move together."""
        vols = [
            _w_vol("Cara", lead=True, gender="female"),
            _w_vol("Ann", member=True, gender="female", couple_id=3, senior=True),
            _w_vol("Ben", member=True, gender="male", couple_id=3),
            _w_vol("Max", member=True, gender="male"),
            _w_vol("Nora", member=True, gender="female", senior=True),
            _w_vol("Owen", member=True, gender="male"),
        ]
        dates = _make_dates(6)
        services = [{"date": d, "hc": True, "combined": False, "notes": ""} for d in dates]
        result = engine.generate_welcome_roster(vols, services, {}, seed=11, session_rules=_W_RULES)

        for d in dates:
            members = [result["roster"][d].get(f"Member {i}", "") for i in range(1, 5)]
            if "Ann" in members:
                assert "Ben" in members, f"Ann placed without partner Ben on {d}: {members}"
            if "Ben" in members:
                assert "Ann" in members, f"Ben placed without partner Ann on {d}: {members}"


# ---------------------------------------------------------------------------
# Fix 4 — Locked cells count toward load
# ---------------------------------------------------------------------------

class TestLockedLoadCounting:
    def test_mt_locked_tech_role_counts(self):
        vols = [
            _mt_vol("Alan", stream=True, cam=True),
            _mt_vol("Colin", proj=True),
            _mt_vol("Micah", sound=True),
            _mt_vol("Gavin", lead=True, stream=True),
            _mt_vol("Timmy", cam=True, proj=True),
        ]
        d = _make_dates(1)[0]
        services = [{"date": d, "hc": False, "combined": False, "notes": ""}]
        locked = {d: {"Sound": "Micah"}}
        result = engine.generate_mt_roster(
            vols, services, {}, seed=5, session_rules=_MT_RULES, locked_cells=locked
        )
        assert result["load_counts"].get("Micah", 0) == 1, \
            f"Locked Sound=Micah should count 1, got {result['load_counts'].get('Micah', 0)}"

    def test_mt_locked_lead_counts_only_as_lead(self):
        """MT5: a locked lead bumps lead_counts, not load_counts."""
        vols = [
            _mt_vol("Alan", stream=True, cam=True),
            _mt_vol("Colin", proj=True),
            _mt_vol("Micah", sound=True),
            _mt_vol("Darrell", lead=True),  # lead-only, no tech
            _mt_vol("Timmy", cam=True, proj=True),
        ]
        d = _make_dates(1)[0]
        services = [{"date": d, "hc": False, "combined": False, "notes": ""}]
        locked = {d: {rules.MT_LEAD_ROLE: "Darrell"}}
        result = engine.generate_mt_roster(
            vols, services, {}, seed=5, session_rules=_MT_RULES, locked_cells=locked
        )
        assert result["lead_counts"].get("Darrell", 0) == 1, "Locked lead should bump lead_counts"
        assert result["load_counts"].get("Darrell", 0) == 0, \
            "Locked lead must NOT count toward shift load (MT5)"

    def test_welcome_locked_member_counts(self):
        vols = [
            _w_vol("Cara", lead=True, gender="female"),
            _w_vol("Max", member=True, gender="male"),
            _w_vol("Nora", member=True, gender="female", senior=True),
            _w_vol("Owen", member=True, gender="male"),
            _w_vol("Pia", member=True, gender="female", senior=True),
        ]
        d = _make_dates(1)[0]
        services = [{"date": d, "hc": False, "combined": False, "notes": ""}]
        locked = {d: {"Member 2": "Nora"}}
        result = engine.generate_welcome_roster(
            vols, services, {}, seed=5, session_rules=_W_RULES, locked_cells=locked
        )
        assert result["load_counts"].get("Nora", 0) == 1, \
            f"Locked member Nora should count 1, got {result['load_counts'].get('Nora', 0)}"

    def test_welcome_locked_lead_counts_toward_load(self):
        """W10: Welcome lead counts toward load AND lead_counts."""
        vols = [
            _w_vol("Cara", lead=True, gender="female"),
            _w_vol("Max", member=True, gender="male"),
            _w_vol("Nora", member=True, gender="female", senior=True),
            _w_vol("Owen", member=True, gender="male"),
        ]
        d = _make_dates(1)[0]
        services = [{"date": d, "hc": False, "combined": False, "notes": ""}]
        locked = {d: {rules.W_LEAD_ROLE: "Cara"}}
        result = engine.generate_welcome_roster(
            vols, services, {}, seed=5, session_rules=_W_RULES, locked_cells=locked
        )
        assert result["load_counts"].get("Cara", 0) == 1, "Welcome locked lead should count toward load (W10)"
        assert result["lead_counts"].get("Cara", 0) == 1, "Welcome locked lead should bump lead_counts"


# ---------------------------------------------------------------------------
# Fix 5 — Non-HC blanking derived from rules, respects locks
# ---------------------------------------------------------------------------

class TestNonHCBlanking:
    def _member_vols(self):
        return [
            _w_vol("Cara", lead=True, gender="female"),
            _w_vol("Max", member=True, gender="male"),
            _w_vol("Nora", member=True, gender="female", senior=True),
            _w_vol("Owen", member=True, gender="male"),
            _w_vol("Pia", member=True, gender="female", senior=True),
            _w_vol("Quin", member=True, gender="male"),
            _w_vol("Rae", member=True, gender="female", senior=True),
        ]

    def test_blanks_all_slots_beyond_non_hc_count(self):
        """hc=5, non_hc=3 → a non-HC service must blank Member 4 AND Member 5
        (old code only ever blanked the hardcoded 'Member 4')."""
        vols = self._member_vols()
        d = _make_dates(1)[0]
        services = [{"date": d, "hc": False, "combined": False, "notes": ""}]
        sr = dict(_W_RULES, hc_member_count=5, non_hc_member_count=3)
        result = engine.generate_welcome_roster(vols, services, {}, seed=5, session_rules=sr)

        roster = result["roster"][d]
        assert roster.get("Member 4", "") == "", "Member 4 should be blank on non-HC"
        assert roster.get("Member 5", "") == "", "Member 5 should be blank on non-HC"
        # And the first 3 are filled.
        filled = [roster.get(f"Member {i}", "") for i in range(1, 4)]
        assert all(filled), f"First 3 members should be filled: {filled}"

    def test_hc_service_keeps_extra_slots(self):
        """With hc_member_count=5, an HC service fills up to Member 5."""
        vols = self._member_vols()
        d = _make_dates(1)[0]
        services = [{"date": d, "hc": True, "combined": False, "notes": ""}]
        sr = dict(_W_RULES, hc_member_count=5, non_hc_member_count=3)
        result = engine.generate_welcome_roster(vols, services, {}, seed=5, session_rules=sr)

        roster = result["roster"][d]
        filled = [roster.get(f"Member {i}", "") for i in range(1, 6)]
        assert all(filled), f"HC service should fill all 5 member slots: {filled}"

    def test_non_hc_count_equal_to_hc_keeps_member_4(self):
        """If a leader sets non-HC members to 4, Member 4 is legitimately filled
        on a non-HC service and must NOT be blanked (old code hardcoded a blank
        of 'Member 4' for every non-HC date, destroying the assignment)."""
        vols = self._member_vols()
        d = _make_dates(1)[0]
        services = [{"date": d, "hc": False, "combined": False, "notes": ""}]
        sr = dict(_W_RULES, hc_member_count=4, non_hc_member_count=4)
        result = engine.generate_welcome_roster(vols, services, {}, seed=5, session_rules=sr)

        assert result["roster"][d].get("Member 4", "") != "", \
            "Member 4 was wrongly blanked on a non-HC service configured for 4 members"

    def test_locked_member_not_blanked_on_non_hc(self):
        """A locked slot beyond the non-HC count must survive the blanking pass."""
        vols = self._member_vols()
        d = _make_dates(1)[0]
        services = [{"date": d, "hc": False, "combined": False, "notes": ""}]
        sr = dict(_W_RULES, hc_member_count=5, non_hc_member_count=3)
        locked = {d: {"Member 4": "Rae"}}
        result = engine.generate_welcome_roster(
            vols, services, {}, seed=5, session_rules=sr, locked_cells=locked
        )
        assert result["roster"][d].get("Member 4", "") == "Rae", \
            "Locked Member 4 must not be blanked on a non-HC service"
