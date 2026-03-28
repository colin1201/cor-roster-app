"""
COR Roster App — CSV Export

Formats roster data for CSV export matching the Google Sheet format:
- Monthly blocks with "Role \\ Date" header
- Load statistics table below
No Streamlit imports.
"""

from datetime import date
from typing import Dict, List

import engine
import rules


def roster_to_csv(
    roster: Dict[date, Dict[str, str]],
    services: List[Dict],
    ministry: str,
    load_counts: Dict[str, int],
) -> str:
    """
    Generate CSV string matching the screenshot format.
    Monthly blocks + load stats at bottom.
    """
    lines = []
    service_dates = sorted(roster.keys())

    # Group dates by month
    months_order = []
    month_dates: Dict[str, List[date]] = {}
    for d in service_dates:
        ml = engine.month_label(d)
        if ml not in month_dates:
            months_order.append(ml)
            month_dates[ml] = []
        month_dates[ml].append(d)

    # Discover display roles from the roster data (handles dynamic roles like Projection 2)
    all_roles = set()
    for d_roster in roster.values():
        all_roles.update(d_roster.keys())
    # Remove "Details" if present, and sort with a stable order
    all_roles.discard("Details")

    if ministry == rules.MINISTRY_MEDIA_TECH:
        # Order: tech roles first (sorted), then lead at the end
        lead_role = None
        tech_roles = []
        for r in sorted(all_roles):
            if "lead" in r.lower() or "Lead" in r:
                lead_role = r
            else:
                tech_roles.append(r)
        display_roles = tech_roles + ([lead_role] if lead_role else [])
    else:
        # Welcome: Lead, then Members in order
        display_roles = []
        if rules.W_LEAD_ROLE in all_roles:
            display_roles.append(rules.W_LEAD_ROLE)
            all_roles.discard(rules.W_LEAD_ROLE)
        display_roles += sorted(all_roles)

    # Service lookup for details
    svc_by_date = {s["date"]: s for s in services}

    for month_name in months_order:
        dates = month_dates[month_name]
        col_labels = [engine.format_date_col(d) for d in dates]

        # Month header
        lines.append(month_name)

        # Header row
        lines.append(_csv_row(["Role \\ Date"] + col_labels))

        # Details row
        details = []
        for d in dates:
            svc = svc_by_date.get(d, {})
            details.append(engine.build_details_string(
                svc.get("hc", False), svc.get("combined", False), svc.get("notes", "")
            ))
        lines.append(_csv_row(["Details"] + details))

        # Role rows
        for role in display_roles:
            row = [role]
            for d in dates:
                row.append(roster.get(d, {}).get(role, ""))
            lines.append(_csv_row(row))

        # Blank line between months
        lines.append("")

    # Load statistics
    lines.append("Load Statistics")
    lines.append(_csv_row(["Name", "Shifts"]))

    sorted_load = sorted(
        [(name, count) for name, count in load_counts.items() if count > 0],
        key=lambda x: (-x[1], x[0]),
    )
    for name, count in sorted_load:
        lines.append(_csv_row([name, str(count)]))

    return "\n".join(lines)


def _csv_row(cells: List[str]) -> str:
    """Build a CSV row, quoting cells that contain commas."""
    escaped = []
    for cell in cells:
        s = str(cell) if cell else ""
        if "," in s or '"' in s:
            s = '"' + s.replace('"', '""') + '"'
        escaped.append(s)
    return ",".join(escaped)
