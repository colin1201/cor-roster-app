"""
COR Roster App — Scheduling Engine

Pure scheduling logic. No Streamlit imports, no network calls.
All I/O happens in data.py; all constants live in rules.py.
"""

import calendar
import hashlib
import random
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import rules


# ---------------------------------------------------------------------------
# Date Utilities
# ---------------------------------------------------------------------------

def suggest_next_quarter() -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Return (start_year_month, end_year_month) for the next 3 consecutive months.
    Each is (year, month). Based on current date.
    """
    today = date.today()
    # Start from next month
    if today.month == 12:
        start_year, start_month = today.year + 1, 1
    else:
        start_year, start_month = today.year, today.month + 1

    # End month is 2 months after start
    end_year, end_month = start_year, start_month
    for _ in range(rules.ROSTER_MONTH_COUNT - 1):
        if end_month == 12:
            end_year += 1
            end_month = 1
        else:
            end_month += 1

    return (start_year, start_month), (end_year, end_month)


def get_sundays_in_range(start_year: int, start_month: int,
                          end_year: int, end_month: int) -> List[date]:
    """Return all Sundays between start and end month (inclusive)."""
    sundays = []
    year, month = start_year, start_month

    while (year, month) <= (end_year, end_month):
        _, days_in_month = calendar.monthrange(year, month)
        for day in range(1, days_in_month + 1):
            d = date(year, month, day)
            if d.weekday() == 6:  # Sunday
                sundays.append(d)

        # Next month
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    return sundays


def sunday_ordinal(d: date) -> int:
    """
    Which Sunday of the month is this? (1st, 2nd, 3rd, 4th, 5th)
    Returns 1-based index.
    """
    return (d.day - 1) // 7 + 1


def default_hc(d: date) -> bool:
    """True if this date should have HC auto-checked (1st and 3rd Sunday)."""
    return sunday_ordinal(d) in rules.HC_DEFAULT_SUNDAYS


def default_combined(d: date) -> bool:
    """True if this date should have Combined auto-checked (1st Sunday)."""
    return sunday_ordinal(d) in rules.COMBINED_DEFAULT_SUNDAYS


def build_details_string(hc: bool, combined: bool, notes: str) -> str:
    """Auto-build the Details row from checkboxes + free text."""
    parts = []
    if combined:
        parts.append("Combined")
    if hc:
        parts.append("HC")
    if notes and notes.strip():
        parts.append(notes.strip())
    return " / ".join(parts)


def month_label(d: date) -> str:
    """E.g. 'January 2026'"""
    return d.strftime("%B %Y")


def format_date_col(d: date) -> str:
    """E.g. '05-Jan'"""
    return d.strftime("%d-%b")


# ---------------------------------------------------------------------------
# Scheduling Primitives (shared by both ministries)
# ---------------------------------------------------------------------------

def _is_qualified(vol: Dict, role_key: str) -> bool:
    """Check if a volunteer is qualified for a role. Handles both formats:
    - MT new format: vol["roles"][role_key]
    - Welcome/legacy: vol[role_key]
    """
    if "roles" in vol:
        return bool(vol["roles"].get(role_key, False))
    return bool(vol.get(role_key, False))


def build_eligible_pool(
    volunteers: List[Dict],
    role_key: str,
    unavailable: Set[str],
    assigned_today: Set[str],
) -> List[Dict]:
    """
    Filter volunteers to those who:
    - Are qualified for the role
    - Are not unavailable
    - Are not already assigned today
    """
    return [
        v for v in volunteers
        if _is_qualified(v, role_key)
        and v["name"] not in unavailable
        and v["name"] not in assigned_today
    ]


def apply_weekly_rest(
    names: List[str],
    service_date: date,
    assignments_by_date: Dict[date, Set[str]],
    prev_quarter_last_crew: Optional[Set[str]] = None,
) -> Tuple[List[str], List[str]]:
    """
    Filter out people who served the previous week.
    Returns (rested_pool, full_pool).
    If rested_pool is empty, caller should use full_pool (self-healing).
    """
    # Find previous Sunday
    prev_sunday = service_date - timedelta(days=7)

    # Get who served previous week
    prev_crew = set()
    if prev_sunday in assignments_by_date:
        prev_crew = assignments_by_date[prev_sunday]
    elif prev_quarter_last_crew and not assignments_by_date:
        # Quarter boundary: use previous quarter's last crew for the first Sunday
        prev_crew = prev_quarter_last_crew

    rested = [n for n in names if n not in prev_crew]
    return rested, list(names)


def sort_by_load(names: List[str], load_counts: Dict[str, int]) -> List[str]:
    """Sort names by ascending load count. Missing = 0."""
    return sorted(names, key=lambda n: load_counts.get(n, 0))


def seeded_tiebreak(
    names: List[str],
    seed: int,
    date_str: str,
    role: str,
) -> Optional[str]:
    """
    Deterministic shuffle + pick first. Combines seed with date and role
    for unique randomization per slot.
    """
    if not names:
        return None
    if len(names) == 1:
        return names[0]

    # Create a deterministic seed from the combination
    combined = f"{seed}-{date_str}-{role}"
    hash_val = int(hashlib.md5(combined.encode()).hexdigest(), 16)
    rng = random.Random(hash_val)

    pool = list(names)
    rng.shuffle(pool)
    return pool[0]


def select_one(
    volunteers: List[Dict],
    role_key: str,
    service_date: date,
    unavailable: Set[str],
    assigned_today: Set[str],
    assignments_by_date: Dict[date, Set[str]],
    load_counts: Dict[str, int],
    seed: int,
    prev_quarter_last_crew: Optional[Set[str]] = None,
) -> Optional[str]:
    """
    Full selection pipeline for one role slot:
    1. Build eligible pool (qualified + available + not assigned today)
    2. Apply weekly rest (self-heal if everyone rested out)
    3. Sort by lowest load
    4. Tiebreak with seeded shuffle
    """
    pool = build_eligible_pool(volunteers, role_key, unavailable, assigned_today)
    if not pool:
        return None

    pool_names = [v["name"] for v in pool]

    # Weekly rest
    rested, full = apply_weekly_rest(
        pool_names, service_date, assignments_by_date, prev_quarter_last_crew
    )
    working_pool = rested if rested else full  # Self-heal

    if not working_pool:
        return None

    # Sort by load
    working_pool = sort_by_load(working_pool, load_counts)

    # Take the group with the lowest load
    min_load = load_counts.get(working_pool[0], 0)
    tied = [n for n in working_pool if load_counts.get(n, 0) == min_load]

    # Tiebreak
    date_str = service_date.isoformat()
    return seeded_tiebreak(tied, seed, date_str, role_key)


# ---------------------------------------------------------------------------
# Media Tech Roster Generation
# ---------------------------------------------------------------------------

def generate_mt_roster(
    volunteers: List[Dict],
    services: List[Dict],
    unavailability: Dict[date, Set[str]],
    seed: int,
    prev_quarter_data: Optional[Dict] = None,
    locked_cells: Optional[Dict] = None,
    session_rules: Optional[Dict] = None,
) -> Dict:
    """
    Generate a Media Tech roster.

    Args:
        volunteers: List of volunteer dicts from data.parse_mt_volunteers
        services: List of service dicts [{date, hc, combined, notes}, ...]
        unavailability: {date -> set of unavailable names}
        seed: Random seed for deterministic generation
        prev_quarter_data: Optional {"load_counts": dict, "last_week_crew": set}
        locked_cells: Optional {date -> {role -> name}} for lock-and-regenerate

    Returns:
        {
            "roster": {date -> {role -> name}},
            "load_counts": {name -> int},  # tech roles only, not lead
            "lead_counts": {name -> int},
            "warnings": [{date, role, message}, ...],
            "assignments_by_date": {date -> set of names},
        }
    """
    locked_cells = locked_cells or {}
    prev_quarter_data = prev_quarter_data or {}
    session_rules = session_rules or {}

    # Editable rules — override defaults from rules.py if leader changed them
    mt_primary_leads = set(session_rules.get("primary_leads", rules.MT_PRIMARY_LEADS))
    mt_fallback_lead = session_rules.get("fallback_lead", rules.MT_FALLBACK_LEAD)
    use_weekly_rest = session_rules.get("weekly_rest", True)
    use_cross_rotation = session_rules.get("cross_rotation", True)

    # Initialize load counts (carry forward from previous quarter if available)
    load_counts: Dict[str, int] = {}
    for v in volunteers:
        load_counts[v["name"]] = prev_quarter_data.get("load_counts", {}).get(v["name"], 0)

    lead_counts: Dict[str, int] = {}
    assignments_by_date: Dict[date, Set[str]] = {}
    prev_quarter_last_crew = prev_quarter_data.get("last_week_crew", set())

    # Role cross-rotation tracking: (person, role) -> count
    role_history: Dict[Tuple[str, str], int] = {}

    roster: Dict[date, Dict[str, str]] = {}
    warnings: List[Dict] = []

    # Dynamic role list from session_rules (set in Stage 2 from sheet headers)
    # role_counts: {"Stream Director": 1, "Sound": 1, ...}
    # Roles with count 0 are skipped (manual-only, like Cam 2)
    role_counts = session_rules.get("role_counts", {r: 1 for r in rules.MT_TECH_ROLES})
    # Expand counts into individual slots: {"Projection": 2} -> [("Projection", "Projection"), ("Projection 2", "Projection")]
    # Each tuple is (slot_display_name, qualification_key)
    auto_fill_slots = []
    for role, count in role_counts.items():
        if count <= 0:
            continue
        for i in range(count):
            slot_name = role if i == 0 else f"{role} {i + 1}"
            auto_fill_slots.append((slot_name, role))
    manual_roles = [role for role, count in role_counts.items() if count == 0]
    # Lead role is handled separately
    lead_role_name = session_rules.get("lead_role_name", rules.MT_LEAD_ROLE)

    for svc in services:
        d = svc["date"]
        locked = locked_cells.get(d, {})
        assigned_today: Set[str] = set()
        day_roster: Dict[str, str] = {}

        # Pre-populate locked cells
        for role, name in locked.items():
            if name:
                day_roster[role] = name
                assigned_today.add(name)

        unavail = unavailability.get(d, set())

        # Step 1-4: Fill auto-fill tech roles (dynamic from sheet headers)
        for slot_name, qual_key in auto_fill_slots:
            if slot_name in locked:
                continue

            # qual_key = the sheet column header (used to check vol["roles"][qual_key])
            pool = build_eligible_pool(volunteers, qual_key, unavail, assigned_today)
            if not pool:
                day_roster[slot_name] = ""
                warnings.append({"date": d, "role": slot_name, "message": f"No qualified volunteer available for {slot_name}"})
                continue

            pool_names = [v["name"] for v in pool]

            # Weekly rest (if enabled)
            if use_weekly_rest:
                rested, full = apply_weekly_rest(
                    pool_names, d, assignments_by_date, prev_quarter_last_crew
                )
                working = rested if rested else full
            else:
                working = list(pool_names)

            if not working:
                day_roster[slot_name] = ""
                warnings.append({"date": d, "role": slot_name, "message": f"No volunteer available for {slot_name}"})
                continue

            # Sort by load
            working = sort_by_load(working, load_counts)

            # Take lowest-load group
            min_load = load_counts.get(working[0], 0)
            tied = [n for n in working if load_counts.get(n, 0) == min_load]

            # Cross-rotation tiebreak (if enabled): use qual_key so "Projection" and "Projection 2" share rotation
            if use_cross_rotation and len(tied) > 1:
                min_role_count = min(role_history.get((n, qual_key), 0) for n in tied)
                tied = [n for n in tied if role_history.get((n, qual_key), 0) == min_role_count]

            # Final tiebreak
            pick = seeded_tiebreak(tied, seed, d.isoformat(), slot_name)

            if pick:
                day_roster[slot_name] = pick
                assigned_today.add(pick)
                load_counts[pick] = load_counts.get(pick, 0) + 1
                role_history[(pick, qual_key)] = role_history.get((pick, qual_key), 0) + 1
            else:
                day_roster[slot_name] = ""

        # Step 5: Manual placeholder roles (count=0) get empty slots
        for role in manual_roles:
            if role not in locked:
                day_roster[role] = ""

        # Step 6: Assign Team Lead
        if lead_role_name not in locked:
            all_slot_names = [s[0] for s in auto_fill_slots]
            lead = _assign_mt_lead(day_roster, d, unavail, lead_counts, seed, mt_primary_leads, mt_fallback_lead, all_slot_names)
            day_roster[lead_role_name] = lead
            if not lead:
                warnings.append({
                    "date": d,
                    "role": lead_role_name,
                    "message": "No qualified team lead available",
                })
        # Note: lead does NOT count toward load_counts (rule MT5)

        roster[d] = day_roster
        assignments_by_date[d] = assigned_today.copy()

    return {
        "roster": roster,
        "load_counts": load_counts,
        "lead_counts": lead_counts,
        "warnings": warnings,
        "assignments_by_date": assignments_by_date,
    }


def _assign_mt_lead(
    day_roster: Dict[str, str],
    service_date: date,
    unavailable: Set[str],
    lead_counts: Dict[str, int],
    seed: int,
    primary_leads: Optional[Set[str]] = None,
    fallback_lead: Optional[str] = None,
    tech_roles: Optional[List[str]] = None,
) -> str:
    """
    Media Tech lead assignment logic (CRITICAL — was wrong in previous prototypes).

    1. Check if primary leads are in today's tech crew
    2. If yes → one of them is lead (lowest lead count, seeded tiebreak). They KEEP their tech role.
    3. If no → assign fallback lead as dedicated lead-only
    4. If fallback also unavailable → return "" (unfilled)
    """
    primary_leads = primary_leads if primary_leads is not None else rules.MT_PRIMARY_LEADS
    fallback_lead = fallback_lead if fallback_lead is not None else rules.MT_FALLBACK_LEAD
    tech_roles = tech_roles if tech_roles is not None else rules.MT_TECH_ROLES

    # Get today's tech crew
    tech_crew = set()
    for role in tech_roles:
        person = day_roster.get(role, "")
        if person:
            tech_crew.add(person)

    # Step 1: Check for primary leads in the crew
    primaries_in_crew = tech_crew & set(primary_leads)

    if primaries_in_crew:
        # Pick the one with lowest lead count
        candidates = list(primaries_in_crew)
        candidates = sort_by_load(candidates, lead_counts)
        min_count = lead_counts.get(candidates[0], 0)
        tied = [c for c in candidates if lead_counts.get(c, 0) == min_count]

        pick = seeded_tiebreak(tied, seed, service_date.isoformat(), "mt_lead")
        if pick:
            lead_counts[pick] = lead_counts.get(pick, 0) + 1
            return pick

    # Step 2: No primary lead in crew → assign fallback
    if fallback_lead and fallback_lead not in unavailable:
        lead_counts[fallback_lead] = lead_counts.get(fallback_lead, 0) + 1
        return fallback_lead

    # Step 3: Darrell also unavailable → unfilled
    return ""


# ---------------------------------------------------------------------------
# Welcome Roster Generation
# ---------------------------------------------------------------------------

def _build_couple_map(volunteers: List[Dict]) -> Dict[str, str]:
    """Build person -> partner map from volunteer couple_ids."""
    by_id: Dict[int, List[str]] = {}
    for v in volunteers:
        cid = v.get("couple_id")
        if cid is not None:
            by_id.setdefault(cid, []).append(v["name"])
    couple_map = {}
    for cid, names in by_id.items():
        if len(names) == 2:
            couple_map[names[0]] = names[1]
            couple_map[names[1]] = names[0]
    return couple_map


def generate_welcome_roster(
    volunteers: List[Dict],
    services: List[Dict],
    unavailability: Dict[date, Set[str]],
    seed: int,
    prev_quarter_data: Optional[Dict] = None,
    locked_cells: Optional[Dict] = None,
    session_rules: Optional[Dict] = None,
) -> Dict:
    """
    Generate a Welcome roster.

    Returns same structure as generate_mt_roster:
    {
        "roster": {date -> {role -> name}},
        "load_counts": {name -> int},  # ALL roles count including lead
        "lead_counts": {name -> int},
        "warnings": [{date, role, message}, ...],
        "assignments_by_date": {date -> set of names},
    }
    """
    locked_cells = locked_cells or {}
    prev_quarter_data = prev_quarter_data or {}
    session_rules = session_rules or {}

    # Editable rules
    use_weekly_rest = session_rules.get("weekly_rest", True)
    min_males = session_rules.get("min_males", 1)
    min_seniors = session_rules.get("min_seniors", 1)
    use_couples_together = session_rules.get("couples_together", True)
    hc_member_count = session_rules.get("hc_member_count", rules.W_HC_MEMBER_COUNT)
    non_hc_member_count = session_rules.get("non_hc_member_count", rules.W_NON_HC_MEMBER_COUNT)

    couple_map = _build_couple_map(volunteers) if use_couples_together else {}

    # Separate lead and member pools (strict separation — rule W4)
    lead_pool = [v for v in volunteers if v["lead"]]
    member_pool = [v for v in volunteers if v["member"]]

    # Build name lookup
    vol_by_name = {v["name"]: v for v in volunteers}

    # Useful sets
    male_members = {v["name"] for v in member_pool if v["gender"] == "male"}
    senior_members = {v["name"] for v in member_pool if v["senior"]}

    # Initialize load counts
    load_counts: Dict[str, int] = {}
    for v in volunteers:
        load_counts[v["name"]] = prev_quarter_data.get("load_counts", {}).get(v["name"], 0)

    lead_counts: Dict[str, int] = {}
    assignments_by_date: Dict[date, Set[str]] = {}
    prev_quarter_last_crew = prev_quarter_data.get("last_week_crew", set())

    roster: Dict[date, Dict[str, str]] = {}
    warnings: List[Dict] = []

    for svc in services:
        d = svc["date"]
        is_hc = svc.get("hc", False)
        locked = locked_cells.get(d, {})
        assigned_today: Set[str] = set()
        day_roster: Dict[str, str] = {}

        member_count = hc_member_count if is_hc else non_hc_member_count
        member_roles = [f"Member {i}" for i in range(1, member_count + 1)]

        # Pre-populate locked cells
        for role, name in locked.items():
            if name:
                day_roster[role] = name
                assigned_today.add(name)

        unavail = unavailability.get(d, set())

        # --- Step 1: Assign Welcome Team Lead ---
        if rules.W_LEAD_ROLE not in locked:
            lead_candidates = [
                v for v in lead_pool
                if v["name"] not in unavail and v["name"] not in assigned_today
            ]
            lead_names = [v["name"] for v in lead_candidates]

            # Weekly rest (if enabled)
            if use_weekly_rest:
                rested, full = apply_weekly_rest(lead_names, d, assignments_by_date, prev_quarter_last_crew)
                working = rested if rested else full
            else:
                working = list(lead_names)

            if working:
                working = sort_by_load(working, load_counts)
                min_load = load_counts.get(working[0], 0)
                tied = [n for n in working if load_counts.get(n, 0) == min_load]
                pick = seeded_tiebreak(tied, seed, d.isoformat(), "welcome_lead")
                if pick:
                    day_roster[rules.W_LEAD_ROLE] = pick
                    assigned_today.add(pick)
                    load_counts[pick] = load_counts.get(pick, 0) + 1  # W10: lead counts
                    lead_counts[pick] = lead_counts.get(pick, 0) + 1
                else:
                    day_roster[rules.W_LEAD_ROLE] = ""
                    warnings.append({"date": d, "role": rules.W_LEAD_ROLE, "message": "No qualified lead available"})
            else:
                day_roster[rules.W_LEAD_ROLE] = ""
                warnings.append({"date": d, "role": rules.W_LEAD_ROLE, "message": "No qualified lead available"})

        # Helper: check if a member can be selected (couple feasibility)
        def _can_select_member(name: str) -> bool:
            """Check if this member can be selected, considering couple constraints."""
            partner = couple_map.get(name)
            if not partner:
                return True  # No couple constraint
            # Partner must be available and there must be room for both
            if partner in unavail:
                return False
            if partner in assigned_today:
                return True  # Partner already assigned, that's fine
            # Need at least 2 remaining slots (this member + partner)
            filled_count = sum(1 for r in member_roles if day_roster.get(r, ""))
            remaining = member_count - filled_count
            return remaining >= 2

        def _select_member(
            candidates: List[str],
            role: str,
            seed_offset: int,
        ) -> Optional[str]:
            """Select a member using the full pipeline."""
            # Filter for couple feasibility
            feasible = [n for n in candidates if _can_select_member(n)]
            if not feasible:
                return None

            # Weekly rest (if enabled)
            if use_weekly_rest:
                rested, full = apply_weekly_rest(feasible, d, assignments_by_date, prev_quarter_last_crew)
                working = rested if rested else full
            else:
                working = list(feasible)
            if not working:
                return None

            # Sort by load
            working = sort_by_load(working, load_counts)
            min_load = load_counts.get(working[0], 0)
            tied = [n for n in working if load_counts.get(n, 0) == min_load]

            return seeded_tiebreak(tied, seed + seed_offset, d.isoformat(), role)

        def _place_member(name: str, role: str):
            """Assign a member and handle couple magnet."""
            day_roster[role] = name
            assigned_today.add(name)
            load_counts[name] = load_counts.get(name, 0) + 1

            # Couple magnet: auto-assign partner to next empty slot
            partner = couple_map.get(name)
            if partner and partner not in assigned_today and partner not in unavail:
                next_slot = _next_empty_member_slot()
                if next_slot:
                    day_roster[next_slot] = partner
                    assigned_today.add(partner)
                    load_counts[partner] = load_counts.get(partner, 0) + 1

        def _next_empty_member_slot() -> Optional[str]:
            for r in member_roles:
                if not day_roster.get(r, ""):
                    return r
            return None

        # --- Step 2: Fill male member slots first (min_males requirement) ---
        males_placed = 0
        for slot_idx in range(min_males):
            slot = _next_empty_member_slot()
            if not slot or slot in locked:
                break

            male_candidates = [
                v["name"] for v in member_pool
                if v["name"] not in unavail
                and v["name"] not in assigned_today
                and v["gender"] == "male"
            ]
            pick = _select_member(male_candidates, slot, seed_offset=100 + slot_idx)

            if pick:
                _place_member(pick, slot)
                males_placed += 1
            else:
                # Soft constraint: fall back to any member with warning
                all_candidates = [
                    v["name"] for v in member_pool
                    if v["name"] not in unavail
                    and v["name"] not in assigned_today
                ]
                pick = _select_member(all_candidates, slot, seed_offset=150 + slot_idx)
                if pick:
                    _place_member(pick, slot)
                    warnings.append({
                        "date": d, "role": slot,
                        "message": f"No eligible male available — assigned female volunteer",
                    })
                else:
                    day_roster[slot] = ""
                    warnings.append({"date": d, "role": slot, "message": "No member available"})

        # --- Step 3: Fill senior citizen slots (min_seniors requirement) ---
        seniors_placed = sum(
            1 for r in member_roles
            if day_roster.get(r, "") in senior_members
        )

        for senior_idx in range(min_seniors - seniors_placed):
            next_slot = _next_empty_member_slot()
            if not next_slot or next_slot in locked:
                break

            senior_candidates = [
                v["name"] for v in member_pool
                if v["name"] not in unavail
                and v["name"] not in assigned_today
                and v["name"] in senior_members
            ]
            pick = _select_member(senior_candidates, next_slot, seed_offset=200 + senior_idx)
            if pick:
                _place_member(pick, next_slot)
            else:
                warnings.append({
                    "date": d, "role": next_slot,
                    "message": "No senior citizen available for this service",
                })
                break

        # --- Step 4: Fill remaining member slots ---
        while True:
            slot = _next_empty_member_slot()
            if not slot or slot in locked:
                break

            candidates = [
                v["name"] for v in member_pool
                if v["name"] not in unavail
                and v["name"] not in assigned_today
            ]
            pick = _select_member(candidates, slot, seed_offset=300 + len(assigned_today))
            if pick:
                _place_member(pick, slot)
            else:
                day_roster[slot] = ""
                warnings.append({"date": d, "role": slot, "message": "No member available"})
                break

        # Fill any remaining empty slots (non-HC Member 4)
        if not is_hc:
            day_roster["Member 4"] = ""

        roster[d] = day_roster
        assignments_by_date[d] = assigned_today.copy()

    return {
        "roster": roster,
        "load_counts": load_counts,
        "lead_counts": lead_counts,
        "warnings": warnings,
        "assignments_by_date": assignments_by_date,
    }
