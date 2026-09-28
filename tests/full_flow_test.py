"""Full user flow test — simulates what a leader does end-to-end."""
import sys
from datetime import date
import engine, data, rules, export

errors = []
def check(cond, msg):
    if not cond:
        errors.append(msg)
        print(f"  FAIL: {msg}")

print("===== FULL USER FLOW TEST =====")
print()

# ==========================================
# MEDIA TECH FLOW
# ==========================================
print("--- MEDIA TECH FLOW ---")

print("Stage 0: Load volunteers")
mt_vols, mt_roles = data.load_mt_volunteers()
# Live sheet grows over time — assert a floor, not an exact count (19 vols / 6 roles on 28 Sep 2026).
check(len(mt_vols) >= 18, f"at least 18 MT volunteers (got {len(mt_vols)})")
check(len(mt_roles) >= 5, f"at least 5 MT roles (got {len(mt_roles)})")

print("Stage 1: Select dates Apr-Jun 2026")
sundays = engine.get_sundays_in_range(2026, 4, 2026, 6)
check(len(sundays) == 13, "13 Sundays")

print("Stage 2: Review rules")
sr_mt = {
    "primary_leads": ["Gavin", "Ben", "Mich Lo"],
    "fallback_lead": "Darrell",
    "lead_role_name": "Media Team Lead",
    "role_counts": {"Stream Director": 1, "Camera 1": 1, "Projection": 1, "Sound": 1},
    "weekly_rest": True,
    "cross_rotation": True,
    "hc_sundays": [1, 3],
    "combined_sundays": [1],
}

print("Stage 3: Build services")
services = []
for d in sundays:
    ordinal = engine.sunday_ordinal(d)
    services.append({
        "date": d,
        "hc": ordinal in sr_mt["hc_sundays"],
        "combined": ordinal in sr_mt["combined_sundays"],
        "notes": "",
    })
check(services[0]["hc"], "1st Sunday is HC")
check(services[0]["combined"], "1st Sunday is Combined")
check(not services[1]["hc"], "2nd Sunday is not HC")

print("Stage 4: Mark unavailability")
unavail = {sundays[0]: {"Gavin"}, sundays[2]: {"Ben", "Mich Lo"}}

print("Stage 5: Generate roster")
result = engine.generate_mt_roster(mt_vols, services, unavail, seed=42, session_rules=sr_mt)

for d in sundays:
    r = result["roster"][d]
    for role in ["Stream Director", "Camera 1", "Projection", "Sound"]:
        check(r.get(role, "") != "", f"{d}: {role} filled")
    # Lead logic
    lead = r["Media Team Lead"]
    tech = {r[role] for role in ["Stream Director", "Camera 1", "Projection", "Sound"] if r[role]}
    primaries = tech & {"Gavin", "Ben", "Mich Lo"}
    if primaries:
        check(lead in primaries, f"{d}: Lead {lead} is primary in crew")
        check(lead in tech, f"{d}: Lead keeps tech role")
    elif lead:
        check(lead == "Darrell", f"{d}: Fallback is Darrell (got {lead})")
    # No duplicates in tech
    tech_list = [r[role] for role in ["Stream Director", "Camera 1", "Projection", "Sound"] if r[role]]
    check(len(tech_list) == len(set(tech_list)), f"{d}: No duplicate tech")

# Unavailability enforced
for role in ["Stream Director", "Camera 1", "Projection", "Sound", "Media Team Lead"]:
    check(result["roster"][sundays[0]].get(role) != "Gavin", f"Gavin not in {role} when unavail")

# Details string
details_0 = engine.build_details_string(services[0]["hc"], services[0]["combined"], "")
check(details_0 == "Combined / HC", f"Details: {details_0}")
details_custom = engine.build_details_string(True, False, "Mothers Day")
check(details_custom == "HC / Mothers Day", f"Details custom: {details_custom}")

# CSV export
print("Export CSV")
csv = export.roster_to_csv(result["roster"], services, rules.MINISTRY_MEDIA_TECH, result["load_counts"])
check("April 2026" in csv, "CSV has April")
check("May 2026" in csv, "CSV has May")
check("June 2026" in csv, "CSV has June")
check("Load Statistics" in csv, "CSV has stats")
check("Combined / HC" in csv, "CSV has details")

# Google Sheets paste
tsv = data.format_for_sheets_paste(csv)
check("\t" in tsv, "TSV has tabs")

# Lock and regenerate
print("Lock and regenerate")
locked_name = result["roster"][sundays[0]]["Sound"]
locked = {sundays[0]: {"Sound": locked_name}}
result2 = engine.generate_mt_roster(mt_vols, services, unavail, seed=999, session_rules=sr_mt, locked_cells=locked)
check(result2["roster"][sundays[0]]["Sound"] == locked_name, f"Locked cell preserved: {locked_name}")

# Previous quarter carry-forward
print("Previous quarter carry-forward")
prev = data.parse_previous_quarter_csv(csv, rules.MINISTRY_MEDIA_TECH, "Media Team Lead")
check(len(prev["load_counts"]) > 0, f"Parsed {len(prev['load_counts'])} load counts")
check(len(prev["last_week_crew"]) > 0, f"Parsed {len(prev['last_week_crew'])} last week crew")
result3 = engine.generate_mt_roster(mt_vols, services, {}, seed=42, session_rules=sr_mt, prev_quarter_data=prev)
check(len(result3["roster"]) == 13, "Carry-forward roster generated")

print("MT FLOW: OK")
print()

# ==========================================
# WELCOME FLOW
# ==========================================
print("--- WELCOME FLOW ---")

print("Stage 0: Load volunteers")
w_vols = data.load_welcome_volunteers()
check(len(w_vols) == 23, f"23 Welcome volunteers (got {len(w_vols)})")

print("Stage 2: Review rules")
sr_w = {
    "min_males": 1, "min_seniors": 1, "couples_together": True,
    "weekly_rest": True, "hc_member_count": 4, "non_hc_member_count": 3,
    "hc_sundays": [1, 3], "combined_sundays": [1],
}

print("Stage 3: Build services")
w_services = []
for d in sundays:
    ordinal = engine.sunday_ordinal(d)
    w_services.append({"date": d, "hc": ordinal in sr_w["hc_sundays"], "combined": ordinal in sr_w["combined_sundays"], "notes": ""})

print("Stage 4: Unavailability")
w_unavail = {sundays[0]: {"Malcolm Lee", "Jessline Lee"}}

print("Stage 5: Generate roster")
w_result = engine.generate_welcome_roster(w_vols, w_services, w_unavail, seed=42, session_rules=sr_w)

couple_map = data.get_couple_map(w_vols)
male_members = {v["name"] for v in w_vols if v["member"] and v["gender"] == "male"}
seniors_set = {v["name"] for v in w_vols if v["senior"]}
leads_set = {v["name"] for v in w_vols if v["lead"]}

for d in sundays:
    r = w_result["roster"][d]
    is_hc = next(s for s in w_services if s["date"] == d)["hc"]
    expected = 4 if is_hc else 3

    lead = r.get(rules.W_LEAD_ROLE, "")
    check(lead in leads_set, f"{d}: Lead {lead} qualified")

    members = [r.get(f"Member {i}", "") for i in range(1, expected + 1)]
    filled = [m for m in members if m]
    check(len(filled) == expected, f"{d}: {expected} members (got {len(filled)})")

    m1 = r.get("Member 1", "")
    if m1:
        check(m1 in male_members, f"{d}: M1 {m1} is male")

    check(any(m in seniors_set for m in filled), f"{d}: has senior")

    for m in filled:
        if m in couple_map:
            check(couple_map[m] in filled, f"{d}: couple {m}+{couple_map[m]}")

    all_p = [lead] + filled
    check(len(all_p) == len(set(all_p)), f"{d}: no duplicates")

# Unavailability
r0_people = [w_result["roster"][sundays[0]].get(r, "") for r in [rules.W_LEAD_ROLE] + [f"Member {i}" for i in range(1, 5)]]
check("Malcolm Lee" not in r0_people, "Malcolm not assigned when unavail")
check("Jessline Lee" not in r0_people, "Jessline not assigned when unavail")

# CSV
print("Export CSV")
w_csv = export.roster_to_csv(w_result["roster"], w_services, rules.MINISTRY_WELCOME, w_result["load_counts"])
check("Welcome Team Lead" in w_csv, "Welcome CSV has lead")
check("Member 1" in w_csv, "Welcome CSV has Member 1")

# Carry-forward
w_prev = data.parse_previous_quarter_csv(w_csv, rules.MINISTRY_WELCOME, rules.W_LEAD_ROLE)
check(len(w_prev["load_counts"]) > 0, "Welcome carry-forward parsed")

print("WELCOME FLOW: OK")
print()

# ==========================================
# EDGE CASES
# ==========================================
print("--- EDGE CASES ---")

# Everyone unavailable
all_mt_names = {v["name"] for v in mt_vols}
r_all = engine.generate_mt_roster(mt_vols, services, {sundays[0]: all_mt_names}, seed=42, session_rules=sr_mt)
check(len(r_all["warnings"]) > 0, "All unavail: has warnings")

# 2 projectionists
sr_2p = dict(sr_mt)
sr_2p["role_counts"] = {"Stream Director": 1, "Camera 1": 1, "Projection": 2, "Sound": 1}
r_2p = engine.generate_mt_roster(mt_vols, services, {}, seed=42, session_rules=sr_2p)
check(r_2p["roster"][sundays[0]].get("Projection 2", "") != "", "2 proj filled")
check(r_2p["roster"][sundays[0]]["Projection"] != r_2p["roster"][sundays[0]]["Projection 2"], "2 proj different people")

# Manual role (count=0)
sr_manual = dict(sr_mt)
sr_manual["role_counts"] = dict(sr_mt["role_counts"])
sr_manual["role_counts"]["Cam 2"] = 0
r_man = engine.generate_mt_roster(mt_vols, services, {}, seed=42, session_rules=sr_manual)
check(r_man["roster"][sundays[0]].get("Cam 2", "") == "", "Manual role empty")

# Welcome 0 males
sr_w0m = dict(sr_w)
sr_w0m["min_males"] = 0
r_w0m = engine.generate_welcome_roster(w_vols, w_services, {}, seed=42, session_rules=sr_w0m)
check(len(r_w0m["roster"]) == 13, "Welcome 0 males OK")

# Welcome 0 seniors
sr_w0s = dict(sr_w)
sr_w0s["min_seniors"] = 0
r_w0s = engine.generate_welcome_roster(w_vols, w_services, {}, seed=42, session_rules=sr_w0s)
check(len(r_w0s["roster"]) == 13, "Welcome 0 seniors OK")

# Welcome couples disabled
sr_wnc = dict(sr_w)
sr_wnc["couples_together"] = False
r_wnc = engine.generate_welcome_roster(w_vols, w_services, {}, seed=42, session_rules=sr_wnc)
check(len(r_wnc["roster"]) == 13, "Welcome no couples OK")

# Determinism
r_a = engine.generate_mt_roster(mt_vols, services, {}, seed=42, session_rules=sr_mt)
r_b = engine.generate_mt_roster(mt_vols, services, {}, seed=42, session_rules=sr_mt)
for d in sundays:
    for role in ["Stream Director", "Camera 1", "Projection", "Sound", "Media Team Lead"]:
        check(r_a["roster"][d][role] == r_b["roster"][d][role], f"Determinism {d} {role}")

# Different seeds give different results
import random
results_set = set()
for s in range(10):
    r = engine.generate_mt_roster(mt_vols, services, {}, seed=s, session_rules=sr_mt)
    results_set.add(r["roster"][sundays[0]]["Sound"])
check(len(results_set) > 1, f"Randomness: {len(results_set)} unique across 10 seeds")

print("EDGE CASES: OK")
print()

# ==========================================
print("=" * 50)
if errors:
    print(f"FAILED: {len(errors)} errors")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("ALL USER FLOW TESTS PASSED - 0 ERRORS")
    print("  Media Tech: full flow + CSV + lock + carry-forward")
    print("  Welcome: full flow + CSV + carry-forward")
    print("  Edge cases: all covered")
