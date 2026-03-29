"""
COR Roster App — Streamlit UI

6-stage wizard for generating church volunteer rosters.
Stage 0: Ministry Selection
Stage 1: Date Selection
Stage 2: Rules Review
Stage 3: Service Details
Stage 4: Unavailability
Stage 5: Roster Dashboard
"""

import calendar
from datetime import date

import pandas as pd
import streamlit as st

import data
import engine
import export
import rules

# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="COR Roster App",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    /* Prominent next button */
    div[data-testid="stButton"] button[kind="primary"] {
        font-size: 1.1rem;
        padding: 0.6rem 2rem;
    }
    /* Details row styling in data editor */
    .details-row { color: #64748b; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
DEFAULTS = {
    "stage": 0,
    "ministry": None,
    "start_ym": None,       # (year, month)
    "end_ym": None,          # (year, month)
    "volunteers": None,      # list of volunteer dicts
    "session_rules": None,   # editable rules for this session
    "services": None,        # list of service dicts [{date, hc, combined, notes}, ...]
    "unavailability": None,  # dict: date_str -> set of unavailable names
    "prev_quarter_data": None, # {load_counts, last_week_crew} from previous CSV
    "roster": None,          # generated roster data
    "original_roster": None, # for undo/reset
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


def reset_all():
    """Full state reset."""
    for key, val in DEFAULTS.items():
        st.session_state[key] = val


def reset_from_stage(stage: int):
    """Reset state from a given stage onward."""
    if stage <= 1:
        st.session_state.volunteers = None
        st.session_state.start_ym = None
        st.session_state.end_ym = None
    if stage <= 2:
        st.session_state.session_rules = None
    if stage <= 3:
        st.session_state.services = None
    if stage <= 4:
        st.session_state.unavailability = None
        st.session_state.unavail_grid = None
    if stage <= 5:
        st.session_state.roster = None
        st.session_state.original_roster = None


# ---------------------------------------------------------------------------
# Navigation helpers
# ---------------------------------------------------------------------------
STAGE_LABELS = ["Ministry", "Dates", "Rules", "Services", "Unavailability", "Roster"]


def render_progress_bar(current_stage: int):
    """Show a step indicator at the top of each stage."""
    if current_stage == 0:
        return
    parts = []
    for i in range(1, 6):
        if i < current_stage:
            parts.append(f"~~{i}. {STAGE_LABELS[i]}~~")
        elif i == current_stage:
            parts.append(f"**{i}. {STAGE_LABELS[i]}**")
        else:
            parts.append(f"{i}. {STAGE_LABELS[i]}")
    st.caption(" → ".join(parts))


def go_to(stage: int):
    # Clear any pending "Start Over" confirmations from other stages
    for i in range(6):
        key = f"confirm_restart_{i}"
        if key in st.session_state:
            st.session_state[key] = False
    st.session_state.stage = stage


def nav_buttons(current_stage: int, back_label="Back", next_label="Next", next_disabled=False):
    """Render Back / Start Over buttons on left, prominent Next button centred below."""
    cols = st.columns([1, 1, 4])
    with cols[0]:
        if current_stage > 0:
            if st.button(f"← {back_label}", key=f"back_{current_stage}"):
                go_to(current_stage - 1)
                st.rerun()
    with cols[1]:
        confirm_key = f"confirm_restart_{current_stage}"
        if st.session_state.get(confirm_key):
            if st.button("Confirm reset?", key=f"restart2_{current_stage}", type="primary"):
                st.session_state[confirm_key] = False
                reset_all()
                st.rerun()
        else:
            if st.button("Start Over", key=f"restart_{current_stage}"):
                st.session_state[confirm_key] = True
                st.rerun()

    # Prominent centred Next button
    st.markdown("")
    _, center, _ = st.columns([2, 2, 2])
    with center:
        if st.button(f"{next_label} →", key=f"next_{current_stage}",
                      type="primary", disabled=next_disabled, use_container_width=True):
            return True
    return False


# ---------------------------------------------------------------------------
# Stage 0: Ministry Selection
# ---------------------------------------------------------------------------
def render_stage_0():
    st.markdown("")
    st.markdown("")
    st.markdown("<h1 style='text-align: center;'>COR Roster App</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 1.1rem;'>Church of the Redeemer — Volunteer Roster Generator</p>", unsafe_allow_html=True)
    st.markdown("")
    st.markdown("<h4 style='text-align: center;'>Which ministry are you from?</h4>", unsafe_allow_html=True)
    st.markdown("")

    def _select_ministry(ministry):
        if st.session_state.ministry != ministry:
            reset_all()
            st.session_state.ministry = ministry
        with st.spinner(f"Loading {ministry} volunteers..."):
            try:
                if ministry == rules.MINISTRY_MEDIA_TECH:
                    vols, role_names = data.load_mt_volunteers()
                    st.session_state.mt_role_names = role_names
                else:
                    vols = data.load_welcome_volunteers()
                st.session_state.volunteers = vols
                go_to(1)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to load volunteers: {e}")

    _, col1, col2, _ = st.columns([1, 2, 2, 1])
    with col1:
        st.markdown(
            "<div style='text-align: center; padding: 1rem; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;'>"
            "<div style='font-size: 2rem;'>⚙️</div>"
            "<div style='font-weight: 600; margin-top: 0.5rem;'>Media Tech</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button("Select Media Tech", use_container_width=True, type="primary"):
            _select_ministry(rules.MINISTRY_MEDIA_TECH)

    with col2:
        st.markdown(
            "<div style='text-align: center; padding: 1rem; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;'>"
            "<div style='font-size: 2rem;'>👋</div>"
            "<div style='font-weight: 600; margin-top: 0.5rem;'>Welcome</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button("Select Welcome", use_container_width=True, type="primary"):
            _select_ministry(rules.MINISTRY_WELCOME)


# ---------------------------------------------------------------------------
# Stage 1: Date Selection
# ---------------------------------------------------------------------------
def render_stage_1():
    render_progress_bar(1)
    st.title("Stage 1 — Date Selection")
    st.caption(f"Ministry: **{st.session_state.ministry}**")

    # Auto-suggest next quarter
    (def_sy, def_sm), (def_ey, def_em) = engine.suggest_next_quarter()

    # Build month options for the next 24 months
    today = date.today()
    month_options = []
    y, m = today.year, today.month
    for _ in range(24):
        month_options.append((y, m, f"{calendar.month_name[m]} {y}"))
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1

    labels = [opt[2] for opt in month_options]

    # Find default indices
    def find_idx(year, month):
        for i, (oy, om, _) in enumerate(month_options):
            if oy == year and om == month:
                return i
        return 0

    start_default = find_idx(def_sy, def_sm)
    end_default = find_idx(def_ey, def_em)

    col1, col2 = st.columns(2)
    with col1:
        start_idx = st.selectbox(
            "Start month",
            range(len(labels)),
            index=start_default,
            format_func=lambda i: labels[i],
            key="start_month_select",
        )
    with col2:
        end_idx = st.selectbox(
            "End month",
            range(len(labels)),
            index=end_default,
            format_func=lambda i: labels[i],
            key="end_month_select",
        )

    start_y, start_m, start_label = month_options[start_idx]
    end_y, end_m, end_label = month_options[end_idx]

    # Validate: end must be >= start
    if (end_y, end_m) < (start_y, start_m):
        st.error("End month must be the same as or after the start month.")
        return

    # Show selected range
    sundays = engine.get_sundays_in_range(start_y, start_m, end_y, end_m)
    st.info(f"**{start_label}** to **{end_label}** — {len(sundays)} Sundays")

    # Volunteer summary (loaded in Stage 0)
    if st.session_state.volunteers:
        with st.expander(f"Volunteers ({len(st.session_state.volunteers)} loaded)"):
            if st.session_state.ministry == rules.MINISTRY_MEDIA_TECH:
                role_names = st.session_state.get("mt_role_names", [])
                vol_rows = []
                for v in st.session_state.volunteers:
                    row = {"Name": v["name"]}
                    for r in role_names:
                        row[r] = "✓" if v.get("roles", {}).get(r, False) else ""
                    vol_rows.append(row)
                vol_df = pd.DataFrame(vol_rows)
            else:
                vol_df = pd.DataFrame([
                    {
                        "Name": v["name"],
                        "Lead": "✓" if v["lead"] else "",
                        "Member": "✓" if v["member"] else "",
                        "Gender": v["gender"].title(),
                        "Couple": v["couple_id"] if v["couple_id"] else "",
                        "Senior": "✓" if v["senior"] else "",
                    }
                    for v in st.session_state.volunteers
                ])
            st.dataframe(vol_df, hide_index=True, use_container_width=True)
            if st.button("Reload from Google Sheet"):
                data.clear_cache()
                # Reset ALL downstream state — sheet is master
                reset_from_stage(2)
                if st.session_state.ministry == rules.MINISTRY_MEDIA_TECH:
                    vols, role_names = data.load_mt_volunteers()
                    st.session_state.volunteers = vols
                    st.session_state.mt_role_names = role_names
                else:
                    st.session_state.volunteers = data.load_welcome_volunteers()
                st.rerun()

    # Previous quarter carry-forward (optional)
    st.divider()
    with st.expander("Previous quarter (optional)"):
        st.markdown("Upload last quarter's CSV export to carry forward shift counts and avoid back-to-back scheduling across quarters.")
        uploaded = st.file_uploader(
            "Upload previous quarter CSV",
            type=["csv"],
            key="prev_quarter_upload",
        )
        if uploaded:
            try:
                csv_text = uploaded.read().decode("utf-8")
                sr = st.session_state.session_rules or {}
                lead_name = sr.get("lead_role_name", rules.MT_LEAD_ROLE) if st.session_state.ministry == rules.MINISTRY_MEDIA_TECH else rules.W_LEAD_ROLE
                prev_data = data.parse_previous_quarter_csv(
                    csv_text, st.session_state.ministry, lead_name
                )
                st.session_state.prev_quarter_data = prev_data
                st.success(f"Loaded {len(prev_data['load_counts'])} people's shift counts. Last week's crew: {len(prev_data['last_week_crew'])} people.")
                with st.expander("View imported data"):
                    st.write("**Shift counts:**", prev_data["load_counts"])
                    st.write("**Last week's crew:**", prev_data["last_week_crew"])
            except Exception as e:
                st.error(f"Failed to parse CSV: {e}")
        elif st.session_state.get("prev_quarter_data"):
            st.success("Previous quarter data loaded.")
            if st.button("Clear previous quarter data"):
                st.session_state.prev_quarter_data = None
                st.rerun()

    # Next button
    st.divider()
    can_proceed = st.session_state.volunteers is not None and len(sundays) > 0
    if nav_buttons(1, next_label="Review Rules", next_disabled=not can_proceed):
        st.session_state.start_ym = (start_y, start_m)
        st.session_state.end_ym = (end_y, end_m)
        reset_from_stage(3)
        go_to(2)
        st.rerun()


# ---------------------------------------------------------------------------
# Stage 2: Rules Review
# ---------------------------------------------------------------------------
def _get_default_rules(ministry):
    """Build default editable rules for a ministry."""
    if ministry == rules.MINISTRY_MEDIA_TECH:
        # Build role_counts from discovered sheet headers
        role_names = st.session_state.get("mt_role_names", rules.MT_TECH_ROLES)
        lead_col = rules.MT_SHEET_COLUMNS.get("lead", "Media Team Lead")
        # Default: 1 per role, except the lead column (handled separately)
        role_counts = {}
        for r in role_names:
            if r.lower() == lead_col.lower():
                continue  # Lead is handled by leadership logic, not role_counts
            role_counts[r] = 1
        return {
            "primary_leads": list(rules.MT_PRIMARY_LEADS),
            "fallback_lead": rules.MT_FALLBACK_LEAD,
            "lead_role_name": lead_col,
            "role_counts": role_counts,
            "weekly_rest": True,
            "cross_rotation": True,
            "hc_sundays": list(rules.HC_DEFAULT_SUNDAYS),
            "combined_sundays": list(rules.COMBINED_DEFAULT_SUNDAYS),
        }
    else:
        return {
            "hc_member_count": rules.W_HC_MEMBER_COUNT,
            "non_hc_member_count": rules.W_NON_HC_MEMBER_COUNT,
            "min_males": 1,
            "min_seniors": 1,
            "couples_together": True,
            "weekly_rest": True,
            "hc_sundays": list(rules.HC_DEFAULT_SUNDAYS),
            "combined_sundays": list(rules.COMBINED_DEFAULT_SUNDAYS),
        }


def render_stage_2():
    render_progress_bar(2)
    st.title("Stage 2 — Rules Review")
    st.caption(f"Ministry: **{st.session_state.ministry}**")
    st.markdown("Review the scheduling rules below. Edit if needed, then confirm to continue.")

    ministry = st.session_state.ministry
    volunteers = st.session_state.volunteers

    # Initialize session rules from defaults
    if st.session_state.session_rules is None:
        st.session_state.session_rules = _get_default_rules(ministry)

    sr = st.session_state.session_rules

    # Reload button — refresh from Google Sheet without going back
    if st.button("Refresh roles from Google Sheet", key="reload_stage2"):
        data.clear_cache()
        reset_from_stage(2)
        if ministry == rules.MINISTRY_MEDIA_TECH:
            vols, role_names = data.load_mt_volunteers()
            st.session_state.volunteers = vols
            st.session_state.mt_role_names = role_names
        else:
            st.session_state.volunteers = data.load_welcome_volunteers()
        st.session_state.session_rules = _get_default_rules(ministry)
        st.rerun()

    if ministry == rules.MINISTRY_MEDIA_TECH:
        # --- Media Tech Rules ---
        st.subheader("Staffing per service")
        st.markdown("How many people are needed for each tech role per service?")

        role_counts = sr.get("role_counts", {})

        # Display roles from Google Sheet in a grid
        if role_counts:
            max_cols = min(len(role_counts), 4)
            for chunk_start in range(0, len(role_counts), max_cols):
                chunk = list(role_counts.items())[chunk_start:chunk_start + max_cols]
                rc_cols = st.columns(max_cols)
                for i, (role, default_count) in enumerate(chunk):
                    with rc_cols[i]:
                        role_counts[role] = st.number_input(
                            role, min_value=0, max_value=5, value=default_count,
                            key=f"rule_rc_{role}",
                            help="Set to 0 to make this a manual-only placeholder",
                        )

        st.caption("Roles are read from your Google Sheet column headers. To add a new role, add a column to the sheet and reload volunteers in Stage 1.")
        sr["role_counts"] = role_counts

        st.divider()
        st.subheader("Leadership")
        st.markdown("These people get the **Team Lead** label when they're in the crew. If none are in the crew, the fallback lead is assigned instead.")

        vol_names = [v["name"] for v in volunteers]

        primary_leads = st.multiselect(
            "Primary leads (equal priority)",
            options=vol_names,
            default=[n for n in sr["primary_leads"] if n in vol_names],
            key="rule_primary_leads",
        )
        sr["primary_leads"] = primary_leads

        fallback = st.text_input(
            "Fallback lead (dedicated lead-only, activated when no primary lead in crew)",
            value=sr.get("fallback_lead", ""),
            key="rule_fallback_lead",
            help="This person doesn't need to be in the volunteer list — they only serve as lead when no primary lead is in the crew",
        )
        sr["fallback_lead"] = fallback.strip()

        if not sr["primary_leads"] and not sr["fallback_lead"]:
            st.error("No primary leads and no fallback lead set — Team Lead will be empty every week.")
        elif not sr["primary_leads"]:
            st.warning("No primary leads set — only the fallback lead will be assigned.")

        st.divider()
        st.subheader("Scheduling")
        sr["weekly_rest"] = st.checkbox("Weekly rest (avoid scheduling someone on consecutive weeks)", value=sr["weekly_rest"], key="rule_weekly_rest")
        sr["cross_rotation"] = st.checkbox("Cross-rotation (rotate people through different tech roles)", value=sr["cross_rotation"], key="rule_cross_rotation")

    else:
        # --- Welcome Rules ---
        st.subheader("Team Size")
        col1, col2 = st.columns(2)
        with col1:
            sr["hc_member_count"] = st.number_input("Members for HC service", min_value=1, max_value=10, value=sr["hc_member_count"], key="rule_hc_count")
        with col2:
            sr["non_hc_member_count"] = st.number_input("Members for non-HC service", min_value=1, max_value=10, value=sr["non_hc_member_count"], key="rule_non_hc_count")

        st.divider()
        st.subheader("Member Requirements")
        col1, col2 = st.columns(2)
        with col1:
            sr["min_males"] = st.number_input(
                "Minimum male members per service",
                min_value=0, max_value=5, value=sr.get("min_males", 1),
                help="If not enough males are available, females will fill in with a warning",
                key="rule_min_males",
            )
        with col2:
            sr["min_seniors"] = st.number_input(
                "Minimum senior citizens per service",
                min_value=0, max_value=5, value=sr.get("min_seniors", 1),
                help="If not enough seniors are available, others will fill in with a warning",
                key="rule_min_seniors",
            )

        sr["couples_together"] = st.checkbox("Couples must serve together (if one is selected, partner auto-fills next slot)", value=sr["couples_together"], key="rule_couples")

        st.divider()
        st.subheader("Scheduling")
        sr["weekly_rest"] = st.checkbox("Weekly rest (avoid scheduling someone on consecutive weeks)", value=sr["weekly_rest"], key="rule_weekly_rest")

    # --- Shared: HC and Combined defaults ---
    st.divider()
    st.subheader("Service Defaults")
    st.markdown("Which Sundays of the month should auto-check HC and Combined?")

    sunday_options = [1, 2, 3, 4, 5]
    sunday_labels = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th"}

    col1, col2 = st.columns(2)
    with col1:
        hc_suns = st.multiselect(
            "HC (Holy Communion) Sundays",
            options=sunday_options,
            default=sr["hc_sundays"],
            format_func=lambda x: f"{sunday_labels[x]} Sunday",
            key="rule_hc_sundays",
        )
        sr["hc_sundays"] = hc_suns
    with col2:
        combined_suns = st.multiselect(
            "Combined service Sundays",
            options=sunday_options,
            default=sr["combined_sundays"],
            format_func=lambda x: f"{sunday_labels[x]} Sunday",
            key="rule_combined_sundays",
        )
        sr["combined_sundays"] = combined_suns

    st.session_state.session_rules = sr

    # Navigation
    st.divider()
    if nav_buttons(2, next_label="Service Details"):
        # Build services using the session rules for HC/Combined defaults
        sundays = engine.get_sundays_in_range(
            st.session_state.start_ym[0], st.session_state.start_ym[1],
            st.session_state.end_ym[0], st.session_state.end_ym[1],
        )
        services = []
        for d in sundays:
            ordinal = engine.sunday_ordinal(d)
            services.append({
                "date": d,
                "hc": ordinal in sr["hc_sundays"],
                "combined": ordinal in sr["combined_sundays"],
                "notes": "",
            })
        st.session_state.services = services
        reset_from_stage(4)
        go_to(3)
        st.rerun()


# ---------------------------------------------------------------------------
# Stage 3: Service Details
# ---------------------------------------------------------------------------
def render_stage_3_services():
    render_progress_bar(3)
    st.title("Stage 3 — Service Details")
    st.caption(f"Ministry: **{st.session_state.ministry}**")
    st.markdown("Review and edit service details. HC and Combined are auto-filled based on which Sunday of the month. Add notes as needed.")

    services = st.session_state.services
    if not services:
        st.warning("No services defined. Go back to Stage 1.")
        return

    # --- Add Date ---
    with st.expander("Add a date"):
        add_col1, add_col2 = st.columns([2, 1])
        with add_col1:
            new_date = st.date_input(
                "Select date to add",
                value=None,
                key="add_date_input",
            )
        with add_col2:
            st.write("")  # spacing
            st.write("")
            if st.button("Add Date", key="add_date_btn"):
                if new_date:
                    # Check not already in list
                    existing_dates = {s["date"] for s in services}
                    if new_date in existing_dates:
                        st.warning("This date is already in the list.")
                    else:
                        sr = st.session_state.session_rules or {}
                        ordinal = engine.sunday_ordinal(new_date) if new_date.weekday() == 6 else 0
                        services.append({
                            "date": new_date,
                            "hc": ordinal in sr.get("hc_sundays", rules.HC_DEFAULT_SUNDAYS),
                            "combined": ordinal in sr.get("combined_sundays", rules.COMBINED_DEFAULT_SUNDAYS),
                            "notes": "",
                        })
                        services.sort(key=lambda s: s["date"])
                        st.session_state.services = services
                        st.rerun()

    # --- Service Table ---
    # Build a DataFrame for editing
    rows = []
    for s in services:
        rows.append({
            "Date": s["date"],
            "Day": s["date"].strftime("%A"),
            "HC": s["hc"],
            "Combined": s["combined"],
            "Notes": s["notes"],
            "Remove": False,
        })

    df = pd.DataFrame(rows)

    edited_df = st.data_editor(
        df,
        column_config={
            "Date": st.column_config.DateColumn("Date", format="DD-MMM-YYYY"),
            "Day": st.column_config.TextColumn("Day", disabled=True),
            "HC": st.column_config.CheckboxColumn("HC"),
            "Combined": st.column_config.CheckboxColumn("Combined"),
            "Notes": st.column_config.TextColumn("Notes"),
            "Remove": st.column_config.CheckboxColumn("Remove?"),
        },
        use_container_width=True,
        hide_index=True,
        key="service_editor",
    )

    # Process removals
    remove_indices = edited_df[edited_df["Remove"] == True].index.tolist()
    if remove_indices:
        if st.button(f"Confirm remove {len(remove_indices)} date(s)", type="primary"):
            keep = [i for i in range(len(services)) if i not in remove_indices]
            st.session_state.services = [services[i] for i in keep]
            st.rerun()

    # Sync edits back (HC, Combined, Notes)
    updated_services = []
    for i, row in edited_df.iterrows():
        if i < len(services):
            updated_services.append({
                "date": services[i]["date"],
                "hc": bool(row["HC"]),
                "combined": bool(row["Combined"]),
                "notes": str(row["Notes"]) if row["Notes"] else "",
            })
    st.session_state.services = updated_services

    # Navigation
    st.divider()
    if nav_buttons(3, next_label="Unavailability"):
        reset_from_stage(5)
        go_to(4)
        st.rerun()


# ---------------------------------------------------------------------------
# Stage 4: Unavailability
# ---------------------------------------------------------------------------
def render_stage_4_unavail():
    render_progress_bar(4)
    st.title("Stage 4 — Unavailability")
    st.caption(f"Ministry: **{st.session_state.ministry}**")
    st.markdown("For each volunteer, select the dates they are **unavailable**.")

    volunteers = st.session_state.volunteers
    services = st.session_state.services
    if not volunteers or not services:
        st.warning("Missing data. Go back to previous stages.")
        return

    vol_names = [v["name"] for v in volunteers]
    service_dates = [s["date"] for s in services]
    date_options = [d.isoformat() for d in service_dates]
    date_display = {d.isoformat(): engine.format_date_col(d) for d in service_dates}

    # "Mark all dates" shortcut
    mark_col1, mark_col2 = st.columns([3, 1])
    with mark_col1:
        mark_all_person = st.selectbox(
            "Quick: mark someone unavailable for ALL dates",
            options=[""] + vol_names,
            key="mark_all_person",
        )
    with mark_col2:
        st.write("")
        st.write("")
        if st.button("Mark all dates", key="mark_all_btn"):
            if mark_all_person:
                st.session_state[f"unavail_{mark_all_person}"] = list(date_options)
                st.rerun()

    st.divider()

    # Per-person multiselect — two columns
    # format_func uses date_display dict (defined once, safe for closure)
    _fmt = lambda x: date_display.get(x, x)
    col_left, col_right = st.columns(2)
    for i, name in enumerate(vol_names):
        target_col = col_left if i % 2 == 0 else col_right
        with target_col:
            st.multiselect(
                name,
                options=date_options,
                format_func=_fmt,
                key=f"unavail_{name}",
            )

    # Build unavailability dict from multiselect keys
    unavailability = {}
    for name in vol_names:
        selected = st.session_state.get(f"unavail_{name}", [])
        for d_str in selected:
            unavailability.setdefault(d_str, set()).add(name)
    st.session_state.unavailability = unavailability

    # Show summary
    total_marked = sum(len(v) for v in unavailability.values())
    if total_marked:
        st.caption(f"{total_marked} unavailability entries marked across {len(unavailability)} dates.")

    # Navigation
    st.divider()
    if nav_buttons(4, next_label="Generate Roster"):
        go_to(5)
        st.rerun()


# ---------------------------------------------------------------------------
# Stage 5: Roster Dashboard
# ---------------------------------------------------------------------------
def render_stage_5_roster():
    render_progress_bar(5)
    st.title("Stage 5 — Roster Dashboard")
    st.caption(f"Ministry: **{st.session_state.ministry}**")

    volunteers = st.session_state.volunteers
    services = st.session_state.services
    if not volunteers or not services:
        st.warning("Missing data. Go back to previous stages.")
        return

    # Build unavailability in the format the engine expects: {date -> set of names}
    unavail_raw = st.session_state.unavailability or {}
    unavailability = {}
    for d_str, names in unavail_raw.items():
        d = date.fromisoformat(d_str)
        unavailability[d] = names

    # Generate roster if not already done
    if st.session_state.roster is None:
        # New random seed each generation so Regenerate gives different results
        import random as _rng
        seed = _rng.randint(0, 2**31)

        sr = st.session_state.session_rules or {}

        prev_data = st.session_state.get("prev_quarter_data")

        if st.session_state.ministry == rules.MINISTRY_MEDIA_TECH:
            result = engine.generate_mt_roster(
                volunteers, services, unavailability, seed=seed,
                session_rules=sr, prev_quarter_data=prev_data,
            )
        else:
            result = engine.generate_welcome_roster(
                volunteers, services, unavailability, seed=seed,
                session_rules=sr, prev_quarter_data=prev_data,
            )

        st.session_state.roster = result
        st.session_state.original_roster = {
            d: dict(roles) for d, roles in result["roster"].items()
        }

    result = st.session_state.roster

    # Show warnings
    if result.get("warnings"):
        with st.expander(f"⚠ {len(result['warnings'])} warnings", expanded=True):
            for w in result["warnings"]:
                st.warning(f"**{w['date'].strftime('%d-%b')}** — {w['role']}: {w['message']}")

    # Display roster grouped by month
    service_dates = [s["date"] for s in services]
    months_seen = []
    month_dates = {}
    for d in service_dates:
        ml = engine.month_label(d)
        if ml not in month_dates:
            months_seen.append(ml)
            month_dates[ml] = []
        month_dates[ml].append(d)

    # Determine role display order
    if st.session_state.ministry == rules.MINISTRY_MEDIA_TECH:
        sr = st.session_state.session_rules or {}
        role_counts = sr.get("role_counts", {})
        lead_role_name = sr.get("lead_role_name", rules.MT_LEAD_ROLE)
        # Expand counts into slot names matching engine output
        auto_slots = []
        for role, count in role_counts.items():
            if count <= 0:
                continue
            for i in range(count):
                auto_slots.append(role if i == 0 else f"{role} {i + 1}")
        manual_slots = [r for r, c in role_counts.items() if c == 0]
        display_roles = auto_slots + manual_slots + [lead_role_name]
    else:
        sr = st.session_state.session_rules or {}
        has_hc = any(s.get("hc") for s in services)
        max_members = sr.get("hc_member_count", rules.W_HC_MEMBER_COUNT) if has_hc else sr.get("non_hc_member_count", rules.W_NON_HC_MEMBER_COUNT)
        display_roles = [rules.W_LEAD_ROLE] + [f"Member {i}" for i in range(1, max_members + 1)]

    # Build available names per date (all volunteers minus unavailable)
    unavail_raw = st.session_state.unavailability or {}
    all_vol_names = sorted([v["name"] for v in volunteers])

    for month_name in months_seen:
        st.subheader(month_name)
        dates_in_month = month_dates[month_name]
        col_labels = [engine.format_date_col(d) for d in dates_in_month]

        # Details row
        details_row = {}
        for d in dates_in_month:
            svc = next(s for s in services if s["date"] == d)
            details_row[engine.format_date_col(d)] = engine.build_details_string(
                svc["hc"], svc["combined"], svc["notes"]
            )

        grid_data = {"Details": details_row}
        for role in display_roles:
            if role == "Details":
                continue
            row = {}
            for d in dates_in_month:
                row[engine.format_date_col(d)] = result["roster"].get(d, {}).get(role, "")
            grid_data[role] = row

        grid_df = pd.DataFrame(grid_data).T
        grid_df.index.name = "Role \\ Date"

        # Build per-column dropdown options (available names for that date)
        col_config = {}
        for d in dates_in_month:
            col = engine.format_date_col(d)
            unavail = unavail_raw.get(d.isoformat(), set())
            available = [n for n in all_vol_names if n not in unavail]
            col_config[col] = st.column_config.SelectboxColumn(
                col,
                options=available,
                required=False,
            )

        edited_grid = st.data_editor(
            grid_df,
            column_config=col_config,
            use_container_width=True,
            key=f"roster_editor_{month_name}",
            disabled=["Details"] if "Details" in grid_df.index else [],
        )

        # Sync edits back to roster
        for role in display_roles:
            if role == "Details":
                continue
            for d in dates_in_month:
                col = engine.format_date_col(d)
                if role in edited_grid.index and col in edited_grid.columns:
                    new_val = edited_grid.loc[role, col]
                    result["roster"][d][role] = str(new_val).strip() if new_val else ""

    # Lock-and-regenerate
    st.divider()
    _render_lock_and_regen(result, services, volunteers, unavailability, display_roles)

    # Reset to generated values
    if st.session_state.original_roster:
        with st.expander("Undo manual edits"):
            st.markdown("Reset all cells back to the originally generated values.")
            if st.button("Reset all to generated", key="reset_to_generated"):
                for d, roles in st.session_state.original_roster.items():
                    for role, name in roles.items():
                        result["roster"][d][role] = name
                st.rerun()

    # Live load statistics
    st.divider()
    st.subheader("Load Statistics")
    _render_load_stats(result, services)

    # Navigation
    st.divider()
    _render_stage_5_nav()


def _render_lock_and_regen(result, services, volunteers, unavailability, display_roles):
    """Lock-and-regenerate: leader locks cells, regenerates the rest."""
    with st.expander("Lock & Regenerate"):
        st.markdown("Select cells to **lock**, then regenerate. Locked cells stay; everything else gets reassigned.")

        service_dates = [s["date"] for s in services]

        # Initialize locked cells in session state
        if "locked_cells" not in st.session_state:
            st.session_state.locked_cells = {}

        # Show lock grid as multiselects per date
        cols_per_row = min(len(service_dates), 4)
        for chunk_start in range(0, len(service_dates), cols_per_row):
            chunk = service_dates[chunk_start:chunk_start + cols_per_row]
            cols = st.columns(len(chunk))
            for i, d in enumerate(chunk):
                with cols[i]:
                    d_key = d.isoformat()
                    roster_for_date = result["roster"].get(d, {})
                    # Build options: only roles that have someone assigned
                    lockable = []
                    for role in display_roles:
                        if role == "Details":
                            continue
                        person = roster_for_date.get(role, "")
                        if person:
                            lockable.append(f"{role}: {person}")

                    st.multiselect(
                        engine.format_date_col(d),
                        options=lockable,
                        key=f"lock_{d_key}",
                    )

        if st.button("Regenerate (keep locked cells)", type="primary"):
            # Build locked_cells dict from selections
            locked = {}
            for d in service_dates:
                d_key = d.isoformat()
                selected = st.session_state.get(f"lock_{d_key}", [])
                if selected:
                    locked[d] = {}
                    for item in selected:
                        role, person = item.split(": ", 1)
                        locked[d][role] = person

            import random as _rng
            seed = _rng.randint(0, 2**31)

            sr = st.session_state.session_rules or {}

            prev_data = st.session_state.get("prev_quarter_data")

            if st.session_state.ministry == rules.MINISTRY_MEDIA_TECH:
                new_result = engine.generate_mt_roster(
                    volunteers, services, unavailability, seed=seed,
                    locked_cells=locked, session_rules=sr, prev_quarter_data=prev_data,
                )
            else:
                new_result = engine.generate_welcome_roster(
                    volunteers, services, unavailability, seed=seed,
                    locked_cells=locked, session_rules=sr, prev_quarter_data=prev_data,
                )

            st.session_state.roster = new_result
            st.session_state.original_roster = {
                d: dict(roles) for d, roles in new_result["roster"].items()
            }
            st.rerun()


def _render_load_stats(result, services):
    """Render live load statistics from current roster state."""
    live_load = _count_live_load(result["roster"])

    if live_load:
        stats_rows = [
            {"Name": name, "Shifts": count}
            for name, count in sorted(live_load.items(), key=lambda x: (-x[1], x[0]))
        ]
        max_shifts = max(r["Shifts"] for r in stats_rows) if stats_rows else 1

        # Styled load table with bar visualization
        stats_df = pd.DataFrame(stats_rows)
        st.dataframe(
            stats_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Shifts": st.column_config.ProgressColumn(
                    "Shifts",
                    min_value=0,
                    max_value=max_shifts,
                    format="%d",
                ),
            },
        )

        # Fairness indicator
        counts = [r["Shifts"] for r in stats_rows]
        if len(counts) > 1:
            avg = sum(counts) / len(counts)
            spread = max(counts) - min(counts)
            if spread <= 1:
                st.success("Load is well balanced")
            elif spread <= 2:
                st.info("Load is fairly balanced")
            else:
                st.warning(f"Load is uneven — spread of {spread} shifts between most and least active")

        # Bottleneck roles — flag roles with few qualified volunteers
        if st.session_state.ministry == rules.MINISTRY_MEDIA_TECH:
            volunteers = st.session_state.volunteers
            sr = st.session_state.get("session_rules") or {}
            rc = sr.get("role_counts", {})
            for role, count in rc.items():
                if count == 0:
                    continue
                qualified = sum(1 for v in volunteers if v.get("roles", {}).get(role, False))
                if qualified <= 4:
                    st.caption(f"Note: Only {qualified} people are qualified for **{role}** — they will be scheduled more often")

        # Unscheduled volunteers
        all_vol_names = {v["name"] for v in st.session_state.volunteers}
        scheduled_names = set(live_load.keys())
        unscheduled = all_vol_names - scheduled_names
        if unscheduled:
            st.caption(f"Not scheduled: {', '.join(sorted(unscheduled))}")

        # Consecutive weeks detection
        _detect_consecutive_weeks(result["roster"], services)
    else:
        st.caption("No assignments yet.")


def _detect_consecutive_weeks(roster, services):
    """Flag anyone serving consecutive weeks."""
    from datetime import timedelta
    service_dates = sorted(roster.keys())
    ministry = st.session_state.ministry

    if ministry == rules.MINISTRY_MEDIA_TECH:
        sr = st.session_state.get("session_rules") or {}
        rc = sr.get("role_counts", {})
        counted_roles = []
        if rc:
            for r, c in rc.items():
                for i in range(c):
                    counted_roles.append(r if i == 0 else f"{r} {i + 1}")
        else:
            counted_roles = list(rules.MT_TECH_ROLES)
    else:
        counted_roles = [rules.W_LEAD_ROLE] + [f"Member {i}" for i in range(1, 5)]

    # Build per-date crew
    date_crews = {}
    for d in service_dates:
        crew = set()
        for role in counted_roles:
            person = roster[d].get(role, "").strip()
            if person:
                crew.add(person)
        date_crews[d] = crew

    # Find consecutive
    consecutive = set()
    for i in range(1, len(service_dates)):
        d_prev = service_dates[i - 1]
        d_curr = service_dates[i]
        if (d_curr - d_prev).days == 7:
            overlap = date_crews.get(d_prev, set()) & date_crews.get(d_curr, set())
            for person in overlap:
                consecutive.add((person, d_prev, d_curr))

    if consecutive:
        names = sorted({c[0] for c in consecutive})
        st.warning(f"Serving consecutive weeks: {', '.join(names)}")


def _render_stage_5_nav():
    """Navigation buttons and export for Stage 5."""
    result = st.session_state.roster
    services = st.session_state.services

    cols = st.columns([1, 1, 1, 1, 2])
    with cols[0]:
        if st.button("← Back"):
            go_to(4)
            st.rerun()
    with cols[1]:
        if st.button("Regenerate"):
            st.session_state.roster = None
            st.rerun()
    with cols[2]:
        confirm_key = "confirm_restart_5"
        if st.session_state.get(confirm_key):
            if st.button("Confirm reset?", key="restart2_5", type="primary"):
                st.session_state[confirm_key] = False
                reset_all()
                st.rerun()
        else:
            if st.button("Start Over", key="restart_5"):
                st.session_state[confirm_key] = True
                st.rerun()

    # CSV Export + Google Sheets copy
    if result and services:
        live_load = _count_live_load(result["roster"])
        csv_str = export.roster_to_csv(
            result["roster"],
            services,
            st.session_state.ministry,
            live_load,
        )
        ministry_slug = st.session_state.ministry.lower().replace(" ", "_")
        with cols[3]:
            st.download_button(
                "Download CSV",
                data=csv_str,
                file_name=f"{ministry_slug}_roster.csv",
                mime="text/csv",
                type="primary",
            )

        # Google Sheets paste-ready format
        st.divider()
        with st.expander("Copy to Google Sheets"):
            st.markdown("Copy the text below and paste directly into Google Sheets (Ctrl+V).")
            tsv_str = data.format_for_sheets_paste(csv_str)
            st.text_area(
                "Tab-separated (select all → copy → paste into Google Sheets)",
                value=tsv_str,
                height=300,
                key="sheets_paste",
            )


def _count_live_load(roster):
    """Recount load from current roster state (supports manual edits)."""
    ministry = st.session_state.ministry
    if ministry == rules.MINISTRY_MEDIA_TECH:
        sr = st.session_state.get("session_rules") or {}
        rc = sr.get("role_counts", {})
        counted_roles = []
        if rc:
            for r, c in rc.items():
                for i in range(c):
                    counted_roles.append(r if i == 0 else f"{r} {i + 1}")
        else:
            counted_roles = list(rules.MT_TECH_ROLES)
    else:
        counted_roles = [rules.W_LEAD_ROLE] + [f"Member {i}" for i in range(1, 5)]

    counts = {}
    for d_roster in roster.values():
        for role in counted_roles:
            person = d_roster.get(role, "").strip()
            if person:
                key = person.lower()
                if key not in counts:
                    counts[key] = {"display": person, "count": 0}
                counts[key]["count"] += 1

    return {info["display"]: info["count"] for info in counts.values()}


# ---------------------------------------------------------------------------
# Sidebar — session summary (always visible)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### COR Roster App")
    st.caption("Church of the Redeemer")
    st.divider()

    ministry = st.session_state.ministry
    if ministry:
        st.markdown(f"**Ministry:** {ministry}")
    else:
        st.markdown("**Ministry:** —")

    if st.session_state.start_ym and st.session_state.end_ym:
        sy, sm = st.session_state.start_ym
        ey, em = st.session_state.end_ym
        import calendar as _cal
        st.markdown(f"**Period:** {_cal.month_abbr[sm]} – {_cal.month_abbr[em]} {ey}")
    else:
        st.markdown("**Period:** —")

    vol_count = len(st.session_state.volunteers) if st.session_state.volunteers else 0
    st.markdown(f"**Volunteers:** {vol_count}")

    svc_count = len(st.session_state.services) if st.session_state.services else 0
    st.markdown(f"**Services:** {svc_count}")

    st.divider()
    current = st.session_state.stage
    total = 5
    if current > 0:
        st.progress(current / total, text=f"Step {current} of {total}")


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
stage = st.session_state.stage

if stage == 0:
    render_stage_0()
elif stage == 1:
    render_stage_1()
elif stage == 2:
    render_stage_2()
elif stage == 3:
    render_stage_3_services()
elif stage == 4:
    render_stage_4_unavail()
elif stage == 5:
    render_stage_5_roster()
