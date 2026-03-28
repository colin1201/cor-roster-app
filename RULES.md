# COR Roster App — Rules Reference

Quick-reference for all scheduling rules. Each rule maps to a test.

## Universal Rules (Both Ministries)

| # | Rule | Type | Self-heals? |
|---|---|---|---|
| U1 | Only assign people to roles they're qualified for | Hard | No |
| U2 | Never schedule someone marked unavailable | Hard | No |
| U3 | One person = one role per service (except Media Lead, see MT3) | Hard | No |
| U4 | Avoid consecutive weeks | Soft | Yes — relaxes when pool exhausted |
| U5 | Prioritize lowest shift count | Soft | N/A |
| U6 | Vary crew combinations (social mixing) | Soft | N/A |
| U7 | Shuffle tied candidates (no alphabetical bias) | Soft | N/A |
| U8 | Same data + same seed = same roster (deterministic) | Hard | No |
| U9 | Switching ministry resets all state (isolation) | Hard | No |
| U10 | Leave slot empty rather than violate hard rule | Hard | No |
| U11 | Carry forward previous quarter shift counts | Soft | N/A |
| U12 | Check previous quarter's last Sunday for weekly rest | Soft | Yes |
| U13 | Skip volunteers with zero qualifications (inactive) | Hard | No |

## Media Tech Rules

| # | Rule | Type |
|---|---|---|
| MT1 | Fill 4 tech roles: Stream Director, Camera 1, Projection, Sound | Hard |
| MT2 | Cam 2 is always a manual placeholder — never auto-fill | Hard |
| MT3 | Team Lead assigned AFTER tech roles filled. Check crew for Gavin/Ben/Mich Lo (equal priority). If present, one of them is lead (keeps tech role). If none present, assign Darrell as dedicated lead. If Darrell unavailable, leave unfilled. | Hard |
| MT4 | Team Lead is an additional hat — person keeps their tech role | Hard |
| MT5 | Team Lead does NOT count toward shift load stats | Hard |
| MT6 | Rotate people across different tech roles (cross-training) | Soft |
| MT7 | Primary leads (Gavin, Ben, Mich Lo) are equal priority — pick lowest lead count | Soft |

## Welcome Rules

| # | Rule | Type | Self-heals? |
|---|---|---|---|
| W1 | HC service = 1 Lead + 4 Members. Non-HC = 1 Lead + 3 Members | Hard | No |
| W2 | Only "Welcome Team Lead" qualified people can be lead | Hard | No |
| W3 | Only "Member" qualified people can fill member slots | Hard | No |
| W4 | Leads and members are strictly separate pools | Hard | No |
| W5 | Member 1 must be Male. If no male available, fill with female but highlight | Soft | Yes — degrades with warning |
| W6 | At least one senior citizen per service. If none available, highlight | Soft | Yes — degrades with warning |
| W7 | Couples rules apply to members only (leads exempt) | Hard | No |
| W8 | If one partner selected, the other auto-fills next member slot | Hard | No |
| W9 | If one partner unavailable, don't select the other | Hard | No |
| W10 | Welcome Team Lead counts toward shift load stats | Hard | No |

## Service Defaults

| Default | When | Toggleable |
|---|---|---|
| HC checked | 1st and 3rd Sunday of each month | Yes |
| Combined checked | 1st Sunday of each month | Yes |
| Details row | Auto-built: "Combined / HC" + Notes | N/A |

## Generation Order

### Media Tech
1. Fill Stream Director
2. Fill Camera 1
3. Fill Projection
4. Fill Sound
5. Check crew for Gavin/Ben/Mich Lo → assign as Team Lead (keeps tech role)
6. If none present → assign Darrell as dedicated lead
7. Cam 2 left empty

### Welcome
1. Assign Welcome Team Lead
2. Assign Member 1 (male only)
3. Ensure at least one senior citizen among members
4. Fill remaining member slots
5. Enforce couples/partner magnet during member assignment

## Assignment Priority (per slot)
1. Build eligible pool by role qualification
2. Remove unavailable
3. Remove already-assigned on same date
4. Apply weekly rest preference (including quarter boundary)
5. Prefer lowest load (including previous quarter carry-forward)
6. Prefer social mixing (least repeated pairings)
7. Resolve ties with seeded shuffle
