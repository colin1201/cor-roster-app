"""Comprehensive end-to-end test of all features."""
import sys
from datetime import date, timedelta
import random as _rng
import engine, data, rules, export

errors = []

def check(condition, msg):
    if not condition:
        errors.append(msg)
        print(f"  FAIL: {msg}")
    return condition

print("========== COMPREHENSIVE TEST ==========")
print()

# ===== 1. DATA LOADING =====
print("--- 1. Data Loading ---")
mt_vols, mt_roles = data.load_mt_volunteers()
check(len(mt_vols) > 0, "MT volunteers loaded")
check(len(mt_roles) > 0, "MT roles discovered")
check("Media Team Lead" in mt_roles, "Lead column found in MT")
check("Stream Director" in mt_roles, "Stream Director found")
check(all("roles" in v for v in mt_vols), "All MT vols have roles dict")
for v in mt_vols:
    has_qual = any(v["roles"].values())
    check(has_qual, f"{v['name']} has at least one qualification")

w_vols = data.load_welcome_volunteers()
check(len(w_vols) > 0, "Welcome volunteers loaded")
couple_map = data.get_couple_map(w_vols)
check("Malcolm Lee" in couple_map, "Couple map has Malcolm")
check(couple_map["Malcolm Lee"] == "Jessline Lee", "Malcolm paired with Jessline")
print(f"  MT: {len(mt_vols)} vols, {len(mt_roles)} roles")
print(f"  Welcome: {len(w_vols)} vols, {len(couple_map)//2} couples")

# ===== 2. DATE UTILITIES =====
print()
print("--- 2. Date Utilities ---")
sundays = engine.get_sundays_in_range(2026, 4, 2026, 6)
check(len(sundays) == 13, f"Apr-Jun 2026 has 13 Sundays (got {len(sundays)})")
check(all(d.weekday() == 6 for d in sundays), "All dates are Sundays")
check(engine.default_hc(date(2026, 4, 5)), "1st Sunday is HC")
check(not engine.default_hc(date(2026, 4, 12)), "2nd Sunday is not HC")
check(engine.default_combined(date(2026, 4, 5)), "1st Sunday is Combined")
check(engine.build_details_string(True, True, "Covenant") == "Combined / HC / Covenant", "Details string")
print("  Date utilities: OK")

# ===== 3. MT ENGINE — MULTIPLE SEEDS =====
print()
print("--- 3. MT Engine (5 seeds) ---")
services = [{"date": d, "hc": engine.default_hc(d), "combined": engine.default_combined(d), "notes": ""} for d in sundays]
sr_mt = {
    "primary_leads": list(rules.MT_PRIMARY_LEADS),
    "fallback_lead": rules.MT_FALLBACK_LEAD,
    "lead_role_name": "Media Team Lead",
    "role_counts": {"Stream Director": 1, "Camera 1": 1, "Projection": 1, "Sound": 1},
    "weekly_rest": True,
    "cross_rotation": True,
}

for seed in [42, 123, 999, 7777, 50000]:
    result = engine.generate_mt_roster(mt_vols, services, {}, seed=seed, session_rules=sr_mt)
    for d in sundays:
        r = result["roster"][d]
        for role in ["Stream Director", "Camera 1", "Projection", "Sound"]:
            check(r.get(role, "") != "", f"Seed {seed} {d}: {role} filled")
        tech = [r[role] for role in ["Stream Director", "Camera 1", "Projection", "Sound"] if r.get(role)]
        check(len(tech) == len(set(tech)), f"Seed {seed} {d}: No duplicate tech")
        lead = r.get("Media Team Lead", "")
        tech_crew = set(tech)
        primaries = tech_crew & rules.MT_PRIMARY_LEADS
        if primaries:
            check(lead in primaries, f"Seed {seed} {d}: Lead {lead} is primary in crew")
            check(lead in tech_crew, f"Seed {seed} {d}: Lead {lead} keeps tech role")
        elif lead:
            check(lead == rules.MT_FALLBACK_LEAD, f"Seed {seed} {d}: Fallback is Darrell (got {lead})")
    print(f"  Seed {seed}: OK")

# ===== 4. MT — UNAVAILABILITY =====
print()
print("--- 4. MT Unavailability ---")
unavail = {sundays[0]: {"Gavin", "Ben", "Mich Lo"}}
result = engine.generate_mt_roster(mt_vols, services, unavail, seed=42, session_rules=sr_mt)
r0 = result["roster"][sundays[0]]
for role in ["Stream Director", "Camera 1", "Projection", "Sound", "Media Team Lead"]:
    person = r0.get(role, "")
    check(person not in {"Gavin", "Ben", "Mich Lo"}, f"Unavail enforced for {role}: {person}")
check(r0.get("Media Team Lead") == "Darrell", "Darrell is lead when all primaries unavail")
print("  Unavailability: OK")

# ===== 5. MT — MULTIPLE PROJECTIONISTS =====
print()
print("--- 5. MT Multiple Roles ---")
sr_2proj = dict(sr_mt)
sr_2proj["role_counts"] = {"Stream Director": 1, "Camera 1": 1, "Projection": 2, "Sound": 1}
result = engine.generate_mt_roster(mt_vols, services, {}, seed=42, session_rules=sr_2proj)
for d in sundays[:3]:
    r = result["roster"][d]
    p1 = r.get("Projection", "")
    p2 = r.get("Projection 2", "")
    check(p1 != "", f"{d}: Projection filled")
    check(p2 != "", f"{d}: Projection 2 filled")
    check(p1 != p2, f"{d}: Projection and Projection 2 are different")
print("  2 projectionists: OK")

# ===== 6. MT — MANUAL ROLE =====
print()
print("--- 6. MT Manual Role (count=0) ---")
sr_manual = dict(sr_mt)
sr_manual["role_counts"] = {"Stream Director": 1, "Camera 1": 1, "Projection": 1, "Sound": 1, "Cam 2": 0}
result = engine.generate_mt_roster(mt_vols, services, {}, seed=42, session_rules=sr_manual)
for d in sundays[:3]:
    check(result["roster"][d].get("Cam 2", "") == "", f"{d}: Cam 2 empty (manual)")
print("  Manual role: OK")

# ===== 7. WELCOME ENGINE — MULTIPLE SEEDS =====
print()
print("--- 7. Welcome Engine (5 seeds) ---")
sr_w = {"min_males": 1, "min_seniors": 1, "couples_together": True, "weekly_rest": True, "hc_member_count": 4, "non_hc_member_count": 3}
male_members = {v["name"] for v in w_vols if v["member"] and v["gender"] == "male"}
seniors = {v["name"] for v in w_vols if v["senior"]}
leads = {v["name"] for v in w_vols if v["lead"]}

for seed in [42, 123, 999, 7777, 50000]:
    result = engine.generate_welcome_roster(w_vols, services, {}, seed=seed, session_rules=sr_w)
    for d in sundays:
        r = result["roster"][d]
        is_hc = next(s for s in services if s["date"] == d)["hc"]
        expected = 4 if is_hc else 3
        lead = r.get(rules.W_LEAD_ROLE, "")
        check(lead != "", f"Seed {seed} {d}: Lead assigned")
        check(lead in leads, f"Seed {seed} {d}: Lead {lead} qualified")
        members = [r.get(f"Member {i}", "") for i in range(1, expected + 1)]
        filled = [m for m in members if m]
        check(len(filled) == expected, f"Seed {seed} {d}: {expected} members (got {len(filled)})")
        m1 = r.get("Member 1", "")
        if m1:
            check(m1 in male_members, f"Seed {seed} {d}: M1 ({m1}) is male")
        has_senior = any(m in seniors for m in filled)
        check(has_senior, f"Seed {seed} {d}: Has senior")
        for m in filled:
            if m in couple_map:
                check(couple_map[m] in filled, f"Seed {seed} {d}: {m} with partner")
        all_people = [lead] + filled
        check(len(all_people) == len(set(all_people)), f"Seed {seed} {d}: No duplicates")
    print(f"  Seed {seed}: OK")

# ===== 8. WELCOME — COUPLE PARTIAL UNAVAIL =====
print()
print("--- 8. Couple Partial Unavailability ---")
unavail_partial = {d: {"Jessline Lee"} for d in sundays}
result = engine.generate_welcome_roster(w_vols, services, unavail_partial, seed=42, session_rules=sr_w)
for d in sundays:
    members = [result["roster"][d].get(f"Member {i}", "") for i in range(1, 5)]
    check("Malcolm Lee" not in members, f"{d}: Malcolm not assigned when Jessline unavail")
print("  Partial couple unavail: OK")

# ===== 9. CSV EXPORT =====
print()
print("--- 9. CSV Export ---")
result_mt = engine.generate_mt_roster(mt_vols, services, {}, seed=42, session_rules=sr_mt)
csv = export.roster_to_csv(result_mt["roster"], services, rules.MINISTRY_MEDIA_TECH, result_mt["load_counts"])
check("April 2026" in csv, "CSV has April")
check("May 2026" in csv, "CSV has May")
check("June 2026" in csv, "CSV has June")
check("Load Statistics" in csv, "CSV has load stats")
check("Combined / HC" in csv, "CSV has details")

result_w = engine.generate_welcome_roster(w_vols, services, {}, seed=42, session_rules=sr_w)
csv_w = export.roster_to_csv(result_w["roster"], services, rules.MINISTRY_WELCOME, result_w["load_counts"])
check("Welcome Team Lead" in csv_w, "Welcome CSV has lead")
check("Member 1" in csv_w, "Welcome CSV has Member 1")
print("  CSV export: OK")

# ===== 10. LOCK AND REGENERATE =====
print()
print("--- 10. Lock and Regenerate ---")
locked = {sundays[0]: {"Sound": "Samuel", "Projection": "Christine"}}
result2 = engine.generate_mt_roster(mt_vols, services, {}, seed=999, session_rules=sr_mt, locked_cells=locked)
check(result2["roster"][sundays[0]]["Sound"] == "Samuel", "Locked Sound preserved")
check(result2["roster"][sundays[0]]["Projection"] == "Christine", "Locked Projection preserved")
locked_w = {sundays[0]: {"Welcome Team Lead": "Joshua Sum"}}
result_w2 = engine.generate_welcome_roster(w_vols, services, {}, seed=999, session_rules=sr_w, locked_cells=locked_w)
check(result_w2["roster"][sundays[0]][rules.W_LEAD_ROLE] == "Joshua Sum", "Welcome locked lead preserved")
print("  Lock and regenerate: OK")

# ===== 11. DETERMINISM =====
print()
print("--- 11. Determinism ---")
r1 = engine.generate_mt_roster(mt_vols, services, {}, seed=42, session_rules=sr_mt)
r2 = engine.generate_mt_roster(mt_vols, services, {}, seed=42, session_rules=sr_mt)
for d in sundays:
    for role in ["Stream Director", "Camera 1", "Projection", "Sound", "Media Team Lead"]:
        check(r1["roster"][d][role] == r2["roster"][d][role], f"MT determinism {d} {role}")
print("  Determinism: OK")

# ===== 12. RANDOMNESS =====
print()
print("--- 12. Randomness ---")
results = set()
for seed in range(10):
    r = engine.generate_mt_roster(mt_vols, services, {}, seed=seed, session_rules=sr_mt)
    results.add(r["roster"][sundays[0]]["Sound"])
check(len(results) > 1, f"Different seeds give different results ({len(results)} unique)")
print(f"  {len(results)} unique Sound assignments across 10 seeds: OK")

# ===== 13. CUSTOM WELCOME RULES =====
print()
print("--- 13. Custom Welcome Rules ---")
sr_custom = {"min_males": 2, "min_seniors": 2, "couples_together": True, "weekly_rest": True, "hc_member_count": 4, "non_hc_member_count": 3}
hc_services = [{"date": d, "hc": True, "combined": False, "notes": ""} for d in sundays[:4]]
result = engine.generate_welcome_roster(w_vols, hc_services, {}, seed=42, session_rules=sr_custom)
for d in sundays[:4]:
    members = [result["roster"][d].get(f"Member {i}", "") for i in range(1, 5)]
    members = [m for m in members if m]
    n_males = sum(1 for m in members if m in male_members)
    n_seniors = sum(1 for m in members if m in seniors)
    check(n_males >= 2, f"{d}: {n_males} males (need 2)")
    check(n_seniors >= 2, f"{d}: {n_seniors} seniors (need 2)")
print("  Custom rules (2 males, 2 seniors): OK")

# ===== 14. EDGE: ALL UNAVAILABLE =====
print()
print("--- 14. Edge: All Unavailable ---")
all_unavail = {sundays[0]: {v["name"] for v in mt_vols}}
result = engine.generate_mt_roster(mt_vols, services, all_unavail, seed=42, session_rules=sr_mt)
unfilled = sum(1 for role in ["Stream Director", "Camera 1", "Projection", "Sound"] if result["roster"][sundays[0]].get(role, "") == "")
check(unfilled > 0, "Some slots unfilled")
check(len(result["warnings"]) > 0, "Warnings generated")
print(f"  All unavailable: {unfilled} unfilled, {len(result['warnings'])} warnings: OK")

# ===== 15. 2-PROJ CSV EXPORT =====
print()
print("--- 15. Multi-role CSV Export ---")
sr_2proj = dict(sr_mt)
sr_2proj["role_counts"] = {"Stream Director": 1, "Camera 1": 1, "Projection": 2, "Sound": 1}
result = engine.generate_mt_roster(mt_vols, services, {}, seed=42, session_rules=sr_2proj)
csv = export.roster_to_csv(result["roster"], services, rules.MINISTRY_MEDIA_TECH, result["load_counts"])
check("Projection" in csv, "CSV has Projection")
check("Projection 2" in csv, "CSV has Projection 2")
print("  Multi-role CSV: OK")

# ===== SUMMARY =====
print()
print("=" * 50)
if errors:
    print(f"FAILED: {len(errors)} errors")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("ALL 15 TEST SECTIONS PASSED - 0 ERRORS")
