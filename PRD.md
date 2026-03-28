# COR Media Tech and Welcome Roster App — PRD

## 1. Product Overview

### 1.1 Purpose
The COR Roster App generates fair, deterministic volunteer rosters from Google Sheets for two ministries:
- **Media Tech**
- **Welcome**

It replaces manual roster creation with a rules-driven workflow that:
- Reads volunteer qualifications from Google Sheets
- Captures service details and unavailability
- Generates ministry-specific rosters
- Allows manual edits in an Excel-like interface with lock-and-regenerate
- Updates load statistics live

### 1.2 Core Product Goal
Generate usable, fair, burnout-aware rosters that respect:
- Volunteer qualifications
- Service-specific requirements
- Ministry-specific staffing rules
- Leadership constraints
- Unavailability
- Fair rotation
- Previous quarter history

---

## 2. Objectives

### 2.1 Business Objectives
- Reduce manual scheduling effort
- Improve fairness and transparency in volunteer allocation
- Prevent overuse of the same volunteers
- Ensure services are adequately staffed with the right skill mix
- Provide a simple editing workflow after auto-generation

### 2.2 User Objectives
Users should be able to:
- Select a ministry and date range quickly
- Define service details (HC, Combined, Notes)
- Record unavailability
- Generate a draft roster automatically
- Lock cells and regenerate remaining slots
- Manually tweak assignments with undo capability
- Immediately see updated workload stats with fairness indicators

---

## 3. Users

### 3.1 Primary Users
- 2 Media Tech ministry leaders
- 2 Welcome ministry leaders

### 3.2 User Characteristics
- Desktop only (no mobile requirement)
- Comfortable with spreadsheets
- Expect deterministic behavior, clear rules, editable outputs, low-friction UI
- Non-technical — UI must be self-explanatory

---

## 4. Scope

### 4.1 In Scope (v1)
- Two ministries: Media Tech and Welcome
- Google Sheet-driven volunteer qualification import
- 5-stage workflow (Ministry Selection + 4-stage pipeline)
- Deterministic seeded generation (seed auto-generated, hidden from user)
- Manual editing with lock-and-regenerate in Stage 4
- Undo/reset cell to generated value
- Live workload statistics with fairness indicators
- Ministry-specific staffing logic
- HC-based scaling for Welcome
- Load balancing and burnout prevention
- Previous quarter carry-forward (shift counts + last week's crew)
- Quarter boundary rest awareness
- Case-insensitive statistics counting
- CSV export matching existing Google Sheet format

### 4.2 v2 Features (Deferred)
- Google Form for volunteer self-service unavailability
- "Copy as image" button for direct WhatsApp sharing
- Google Sheets push export (write directly to a Sheet)

### 4.3 Out of Scope
- Multi-service-per-day scheduling beyond the current Sunday service model
- Automated messaging to volunteers
- Attendance confirmation workflows
- Native mobile app
- Authentication/permissions model
- General-purpose scheduling beyond these two ministries

---

## 5. Product Principles

1. **Deterministic, not mysterious** — same data + same seed = same roster
2. **Spreadsheet-native** — Sheets are the source of truth for volunteer qualifications and member metadata
3. **Constraint-first** — hard rules must never be broken unless explicitly allowed via self-healing logic
4. **Editable after generation** — coordinators must be able to override the generated result manually, with lock-and-regenerate support
5. **Fair but practical** — optimize fairness while still covering services
6. **Rules are testable** — every rule has automated tests; rules live in config, not scattered through code

---

## 6. Data Sources

### 6.1 Google Sheets as Source of Truth
The application reads data from configured Google Sheet tabs.

**Sheet ID:** `1jh6ScfqpHe7rRN1s-9NYPsm7hwqWWLjdLKTYThRRGUo`

### 6.2 Media Tech Members Sheet (GID: 0)
| Column | Purpose |
|---|---|
| Name | Volunteer name |
| Media Team Lead | "Yes" if qualified as lead |
| Stream Director | "Yes" if qualified |
| Camera 1 | "Yes" if qualified |
| Projection | "Yes" if qualified |
| Sound | "Yes" if qualified |

- Volunteers with zero qualifications are inactive/on break — skip them in scheduling
- Cam 2 appears in output UI as a manual placeholder, never auto-filled

### 6.3 Welcome Members Sheet (GID: 2080125013)
| Column | Purpose |
|---|---|
| Name | Volunteer name |
| Welcome Team Lead | "Yes" if qualified as lead |
| Member | "Yes" if qualified as member |
| Gender | "Male" or "Female" |
| Couple | Numeric ID — partners share the same number |
| Senior citizen | "Yes" if senior citizen |

- "Male" column exists in sheet but is redundant — use Gender column only

### 6.4 Previous Quarter Roster Sheet
- Leader pastes last quarter's final roster into a tab in the same Google Sheet
- App reads this to extract:
  - **Historical shift counts** for load carry-forward
  - **Last week's crew** for quarter boundary rest rule

### 6.5 Service Details Data
Per selected service date, user defines:
- HC checkbox (auto-defaults: 1st and 3rd Sunday)
- Combined checkbox (auto-defaults: 1st Sunday)
- Notes (free text)

### 6.6 Unavailability Data
Per service date, user marks who is unavailable via a grid/matrix UI.

---

## 7. Workflow

### 7.0 Stage 0 — Ministry Selection
User selects which ministry they are from:
- Media Tech
- Welcome

**Requirements:**
- This is the first screen the user sees
- Switching ministry resets all application state (ministry isolation)

### 7.1 Stage 1 — Date Selection
User selects:
- Start month and end month (auto-suggests next 3 consecutive months)
- Spreadsheet configuration (Sheet ID, previous quarter tab)

**Requirements:**
- On initial load, app automatically pre-selects the next 3 consecutive months
- Always 3 consecutive months
- Seed is auto-generated internally (not shown to user)

### 7.2 Stage 2 — Service Details
App displays all Sundays in selected range with auto-populated defaults.

**Fields per date:**
- Date
- HC checkbox — auto-checked on 1st and 3rd Sundays, toggleable
- Combined checkbox — auto-checked on 1st Sunday, toggleable
- Notes — free text field for remarks (e.g. "Covenant", "Womens Sunday")
- Details row auto-builds from checkboxes + notes (e.g. "Combined / HC / Covenant")

**Requirements:**
- Users must be able to add dates manually (e.g. Good Friday, extra services)
- Users must be able to remove dates manually (e.g. no service that week)
- HC status is used by Welcome staffing logic
- Combined is informational only — no staffing impact

### 7.3 Stage 3 — Unavailability
Users mark volunteers as unavailable for specific service dates.

**Requirements:**
- Displayed as a grid/matrix: persons as rows, dates as columns, checkboxes
- Unavailability is ministry-specific
- Volunteers marked unavailable are strictly excluded from assignment on that date
- Back and Start Over buttons available

### 7.4 Stage 4 — Roster Dashboard
Displays generated roster in a transposed editor:
- Rows = roles
- Columns = service dates
- Grouped by month

**Requirements:**
- Typing into cells updates stats immediately
- Name matching in stats must be case-insensitive
- Users can manually override generated assignments
- **Lock and regenerate:** leader can lock cells they're happy with, then regenerate — engine only fills unlocked cells
- **Undo/reset:** ability to revert a cell to its originally generated value
- **Highlighted warnings:** when soft constraints are violated (e.g. no male for Member 1, no senior citizen assigned)
- Back and Start Over controls available
- CSV export button

---

## 8. Functional Requirements

### 8.1 Shared Scheduling Engine

**FR-1 Deterministic generation**
Same input data + same seed = same roster.

**FR-2 Qualification enforcement**
Only assign volunteers to roles they are marked qualified for in the source sheet.

**FR-3 Availability enforcement**
Never assign volunteers marked unavailable on a given date.

**FR-4 Single-role-per-service**
Do not assign the same volunteer to more than one role in the same service. Exception: Media Tech Team Lead is an additional label on top of an existing tech role (see FR-MT-3).

**FR-5 Weekly rest**
Avoid assigning a volunteer on consecutive weeks where possible.

**FR-6 Self-healing**
If weekly rest makes a service impossible to fill, allow assigning someone who served the previous week.

**FR-7 Load balancing**
Prioritize volunteers with the lowest current shift load.

**FR-8 Tie-break resolution**
Resolve ties using deterministic seeded randomization.

**FR-9 Social mixing**
Reduce repeated crew pairings where practical.

**FR-10 Manual edits**
Manual edits persist in the current session and update live statistics.

**FR-11 Lock and regenerate**
Locked cells are preserved during regeneration. Engine only fills unlocked/empty cells.

**FR-12 Previous quarter carry-forward**
Read last quarter's final roster from Google Sheet to:
- Initialize shift counts (so fairness carries across quarters)
- Identify last week's crew (for quarter boundary rest rule)

**FR-13 Quarter boundary rest**
When applying weekly rest to the first Sunday of the new quarter, check the last Sunday of the previous quarter's roster.

**FR-14 Inactive member exclusion**
Volunteers with zero qualifications are skipped entirely.

---

### 8.2 Media Tech Functional Requirements

**Roles per service:**
1. Stream Director
2. Camera 1
3. Projection
4. Sound
5. Media Team Lead (additional label, not a separate slot)
6. Cam 2 (manual placeholder, never auto-filled)

**FR-MT-1 Role qualification mapping**
Role eligibility uses exact sheet headers: Media Team Lead, Stream Director, Camera 1, Projection, Sound.

**FR-MT-2 Required staffing**
The engine fills one person for each of: Stream Director, Camera 1, Projection, Sound.

**FR-MT-3 Leadership logic**
Team Lead is assigned AFTER all tech roles are filled. The process:
1. Check if Gavin, Ben, or Mich Lo is in today's assembled crew
2. **Yes** — assign one of them as Team Lead. They keep their tech role. If multiple are present, pick the one with the lowest lead count. All three are equal priority.
3. **No** — assign Darrell as Team Lead. Darrell is a dedicated lead-only person with no tech qualifications. He is only activated when none of the three primary leads are in the crew.
4. If Darrell is also unavailable — leave Team Lead unfilled for manual resolution.

**FR-MT-4 Lead is an additional hat**
A person assigned as Media Team Lead retains their tech role. Team Lead is a label on top of their existing assignment, not a separate slot. Exception: Darrell, who only fills the lead role.

**FR-MT-5 Lead load-stat exclusion**
Media Team Lead assignments do NOT count toward total shift load statistics. Only tech role assignments count.

**FR-MT-6 Role cross-rotation**
Where multiple valid assignments exist, favor rotation across different tech roles to prevent role stagnation.

**FR-MT-7 Cam 2 placeholder**
Cam 2 is always empty in generated output. Leaders fill it manually if needed.

---

### 8.3 Welcome Functional Requirements

**Roles per service:**
- Welcome Team Lead
- Member 1
- Member 2
- Member 3
- Member 4 (HC services only)

**FR-W-1 HC scaling**
- HC = true: 1 Welcome Team Lead + 4 Members
- HC = false: 1 Welcome Team Lead + 3 Members

**FR-W-2 Lead eligibility**
Only volunteers marked "Welcome Team Lead" may be assigned to the lead role.

**FR-W-3 Member eligibility**
Only volunteers marked "Member" may be assigned to member roles.

**FR-W-4 Lead/member separation**
Welcome Team Leads do not fill member slots and vice versa. Strict separation.

**FR-W-5 Male Member 1**
Member 1 must be assigned to a Male volunteer. If no eligible male is available, fill with a female but **highlight the violation** visually in the roster.

**FR-W-6 Senior citizen requirement**
At least one member per service must be a senior citizen. If none available, leave the requirement unmet but **highlight the violation** visually.

**FR-W-7 Couples policy**
Couples rules apply to members only. Welcome Team Leads are exempt.

**FR-W-8 Couple matching**
If a member with a Couple value is selected, their partner (same Couple ID) must also be assigned to the same service.

**FR-W-9 Partner magnet**
When a coupled member is selected, the partner is placed into the next available member slot.

**FR-W-10 Couple feasibility**
If a coupled member's partner is unavailable or can't be placed (full capacity), that member is not selected.

**FR-W-11 Welcome lead counts toward load**
Unlike Media Tech, Welcome Team Lead assignments DO count toward total shift load statistics.

---

## 9. Load Statistics Requirements

### 9.1 Display
The roster dashboard displays a live-updating load statistics table below the roster, grouped by month.

### 9.2 Name handling
- Case-insensitive matching
- Whitespace-trimmed

### 9.3 Counting rules
- Each assignment = one shift, unless excluded by ministry rule
- Media Team Lead: does NOT count
- All other Media Tech roles: count
- All Welcome roles (including lead): count

### 9.4 Manual edit reactivity
When users type or edit names, statistics update immediately.

### 9.5 Enhanced stats (v1)
- **Fairness indicator** — visual signal showing whether load is balanced or uneven
- **Unscheduled people** — flag anyone in the volunteer pool who wasn't scheduled at all
- **Consecutive weeks** — flag anyone serving consecutive weeks (especially after manual edits)

---

## 10. Generation Logic

### 10.1 Priority Order
1. Build eligible pool by role
2. Remove unavailable people
3. Remove already-assigned people on same date
4. Apply weekly-rest preference (including quarter boundary)
5. Prefer lowest current load (including previous quarter carry-forward)
6. Prefer social mixing
7. Resolve ties using seeded randomization

### 10.2 Self-healing
If constraints fail due only to weekly-rest restrictions, retry while relaxing weekly-rest.

### 10.3 Unfilled slots
If hard constraints make a role impossible to fill, leave it visibly unfilled with a highlight for manual resolution. Never silently violate a hard constraint.

### 10.4 Media Tech Generation Order
1. Fill Stream Director
2. Fill Camera 1
3. Fill Projection
4. Fill Sound
5. Check crew for Gavin/Ben/Mich Lo → assign Team Lead
6. If none present → assign Darrell as lead
7. Cam 2 left empty

### 10.5 Welcome Generation Order
1. Assign Welcome Team Lead
2. Assign Member 1 from male-qualified members
3. Ensure at least one senior citizen among members
4. Fill remaining member slots
5. Enforce couples/partner magnet during member assignment

---

## 11. Service Defaults

| Default | Rule | Toggleable |
|---|---|---|
| HC | 1st and 3rd Sunday of each month | Yes |
| Combined | 1st Sunday of each month | Yes |
| Details row | Auto-built from checkboxes + Notes | N/A |

---

## 12. Export Format

CSV export must match the existing Google Sheet format:
- Monthly blocks with header row "Role \ Date"
- Rows: Details, tech/member roles, Cam 2 (Media), Team Lead
- Columns: service dates (formatted DD-Mon)
- Load statistics table below the roster (Name + shift count, sorted by count descending)

---

## 13. Non-Functional Requirements

### 13.1 Determinism
Same inputs and seed must always produce the same roster.

### 13.2 Responsiveness
Stage 4 edits and stats updates should feel immediate.

### 13.3 Explainability
Role behavior follows visible sheet headers and explicit business rules.

### 13.4 Maintainability
- Rules live in a dedicated config file, not scattered through code
- Role mappings are header-driven, not hard-coded by column index
- Scheduling engine is separated from UI code

### 13.5 Testability
Every rule has an automated test. Tests verify:
- Qualification enforcement
- Unavailability enforcement
- Weekly rest and self-healing
- Load balancing
- Couple matching and feasibility
- Senior citizen requirement
- Male Member 1 constraint
- Lead logic for both ministries
- HC scaling
- Deterministic output with same seed
- Previous quarter carry-forward

### 13.6 Safety
Prefer leaving a slot unfilled over silently violating a hard rule. Highlight violations visually.

---

## 14. Edge Cases

1. **No qualified lead in Media Tech crew** — check for Darrell. If Darrell also unavailable, leave lead unfilled.
2. **No eligible male for Welcome Member 1** — fill with female, highlight the violation.
3. **No available senior citizen** — leave requirement unmet, highlight visually.
4. **Couple only partially available** — do not assign one without the other (members only).
5. **Manual edits introduce invalid names** — stats count typed names case-insensitively. Optionally flag names not in the volunteer pool.
6. **Header mismatch** — if sheet headers differ from expected names, generation fails. Header names must be exact.
7. **All volunteers served last week** — self-healing activates, weekly rest relaxed.
8. **Quarter boundary** — first Sunday of new quarter checks last Sunday of previous quarter for weekly rest.
9. **Multiple primary leads in same crew** — pick the one with lowest lead count; all three are equal priority.

---

## 15. Open Issues / Deferred Items

1. **Combined service logic** — Combined field exists in Stage 2 as informational only. No staffing impact currently. May change in future.
2. **Validation/warning UI specifics** — exact visual treatment of highlighted warnings TBD during build.
3. **Previous quarter tab format** — exact layout of the "paste last quarter's roster" tab TBD during build.
4. **Media Tech partner rule** — identified in original PRD but not yet specified. Deferred.

---

## 16. Success Criteria

The product is successful if users can:
- Select their ministry and create rosters in one guided flow
- Trust that assignments respect qualifications and availability
- See fair rotation across the selected period and across quarters
- Meet HC Welcome requirements automatically
- Lock cells and regenerate remaining slots without losing manual work
- Manually adjust rosters with undo capability
- See live, enhanced load statistics
- Export CSV that pastes directly into Google Sheets without reformatting
- Rely on deterministic outputs

---

## 17. Tech Stack

- **Framework:** Streamlit
- **Hosting:** Streamlit Cloud
- **Data:** Google Sheets (read via CSV export URL)
- **GitHub:** `colin1201` personal account
- **Architecture:**
  - `rules.py` — all rules as testable config
  - `engine.py` — scheduling logic (separate from UI)
  - `app.py` — Streamlit UI
  - `tests/` — automated tests for every rule

---

## 18. v2 Roadmap

1. **Google Form integration** — volunteers self-report unavailability via a form; app auto-imports responses. Auto-populate form with next quarter's Sundays.
2. **Copy as image** — generate a clean table image for direct WhatsApp sharing.
3. **Google Sheets push** — write final roster directly to a Google Sheet instead of CSV export.
