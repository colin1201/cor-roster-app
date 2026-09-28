# COR Roster App — Dev Rules

## Architecture Boundaries
- `engine.py` — ZERO Streamlit imports, ZERO network calls. Pure scheduling logic only.
- `data.py` — All Google Sheets I/O. No Streamlit imports.
- `rules.py` — Constants only. No logic, no imports beyond typing.
- `app.py` — Streamlit UI. Calls engine and data, never duplicates their logic.
- `export.py` — CSV formatting. No Streamlit imports.

## Testing
- Run unit tests: `pytest tests/test_*.py -v` — plain `pytest tests/` crashes, because it also collects `full_flow_test.py`/`comprehensive_test.py`, which are scripts that call `sys.exit`
- Integration script (reads the LIVE sheet): `PYTHONPATH=. python tests/full_flow_test.py`. Its sheet-size checks are floors (≥18 vols, ≥5 roles), never exact counts — the sheet grows and an exact count fails like a code regression
- Live check: Playwright into the `iframe[title="streamlitApp"]`; the primary button (`stBaseButton-primary`) advances each stage. The grid is canvas-rendered, so read results by screenshot or by alert text, not cell text
- Every rule in RULES.md must have a corresponding test
- Tests use mocked data (no network calls in tests)
- Write tests BEFORE engine code for critical rules (especially MT lead logic)

## Key Rule: Media Tech Lead Logic
The lead logic was wrong in BOTH previous prototypes. The correct logic is:
1. Fill 4 tech roles first (Stream Director, Camera 1, Projection, Sound)
2. Check if Gavin/Ben/Mich Lo are in the crew — if yes, one gets Team Lead label AND keeps tech role
3. If none present → Darrell as dedicated lead-only
4. If Darrell unavailable → leave unfilled
5. Lead does NOT count toward shift load

## Google Sheet is the Master List
The Google Sheet is the single source of truth for volunteers and roles. The app MUST always reflect the current state of the sheet:
- Roles come from sheet column headers — never hardcoded in the app
- **Row ORDER comes from the sheet too** — the roster and CSV follow the Media Tech sheet's columns left to right, lead included (`engine.order_mt_display_roles`). Admins reorder by moving columns. When Colin asks for a new order, the fix is moving the sheet columns, not an order list in code. 28 Sep 2026 I shipped a hardcoded order list first and he had to ask for it to follow the sheet ("so that future admin members can edit the order")
- Clash warning (Stage 5, red box): lists anyone rostered on a date they marked unavailable, generated or hand-edited. Warning only. Needed because Back → change unavailability → Next keeps the OLD roster until Regenerate
- Volunteer qualifications come from the sheet — never cached across reloads
- When volunteers are reloaded, ALL downstream state must reset (session_rules, services, unavailability, roster) to prevent stale data
- Never store sheet-derived data that could go stale without a clear reload path

## Deployment
- Hosted on Streamlit Cloud: https://cor-mediatech-welcome.streamlit.app/
- GitHub repo: colin1201/cor-roster-app
- Auto-deploys on push to master
