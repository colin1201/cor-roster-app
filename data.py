"""
COR Roster App — Data Loading

Handles all Google Sheets I/O. No Streamlit imports.
"""

import io
import re
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import requests

import rules


def build_csv_url(sheet_id: str, gid: str) -> str:
    """Build a Google Sheets CSV export URL."""
    return rules.GSHEET_CSV_URL.format(sheet_id=sheet_id, gid=gid)


def _normalize_name(name) -> str:
    """Strip whitespace and collapse multiple spaces."""
    if name is None or pd.isna(name):
        return ""
    s = str(name).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _is_yes(value) -> bool:
    """Check if a cell value means 'qualified' (non-empty, non-zero)."""
    if value is None or pd.isna(value):
        return False
    s = str(value).strip().lower()
    return s != "" and s != "0" and s != "no" and s != "false"


def _find_column(df: pd.DataFrame, target: str) -> Optional[str]:
    """Find a column by case-insensitive match."""
    for col in df.columns:
        if str(col).strip().lower() == target.strip().lower():
            return col
    return None


_sheet_cache: Dict[str, pd.DataFrame] = {}


def clear_cache():
    """Clear the sheet cache. Call when user wants to reload fresh data."""
    _sheet_cache.clear()


def fetch_sheet(sheet_id: str, gid: str, use_cache: bool = True) -> pd.DataFrame:
    """Fetch a Google Sheet tab as a DataFrame. Cached per session."""
    cache_key = f"{sheet_id}_{gid}"
    if use_cache and cache_key in _sheet_cache:
        return _sheet_cache[cache_key].copy()

    url = build_csv_url(sheet_id, gid)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text))
    # Strip whitespace from column headers
    df.columns = [str(c).strip() for c in df.columns]

    _sheet_cache[cache_key] = df
    return df.copy()


def load_mt_volunteers(sheet_id: str = rules.SHEET_ID, gid: str = rules.MT_GID) -> Tuple[List[Dict], List[str]]:
    """
    Load Media Tech volunteers from Google Sheet.
    Returns (volunteers, role_names) where:
    - volunteers: list of dicts with "name", "roles" (dict of role->bool)
    - role_names: list of role column headers discovered from the sheet (excludes "Name")
    """
    df = fetch_sheet(sheet_id, gid)
    return parse_mt_volunteers(df)


# Columns in the MT sheet that are NOT tech roles
_MT_NON_ROLE_COLUMNS = {"name"}


def parse_mt_volunteers(df: pd.DataFrame) -> Tuple[List[Dict], List[str]]:
    """
    Parse a Media Tech DataFrame into volunteer dicts.
    Dynamically discovers roles from column headers.
    Returns (volunteers, role_names).
    """
    col_name = _find_column(df, "Name")
    if not col_name:
        raise ValueError("Missing 'Name' column in Media Tech sheet")

    # Discover role columns: everything except "Name"
    role_columns = []
    for col in df.columns:
        if col.strip().lower() != "name":
            role_columns.append(col.strip())

    volunteers = []
    for _, row in df.iterrows():
        name = _normalize_name(row.get(col_name))
        if not name:
            continue

        # Build role qualifications dynamically
        roles = {}
        has_any_qual = False
        for role_col in role_columns:
            actual_col = _find_column(df, role_col)
            qualified = _is_yes(row.get(actual_col)) if actual_col else False
            roles[role_col] = qualified
            if qualified:
                has_any_qual = True

        # Rule U13: skip inactive volunteers (zero qualifications)
        if not has_any_qual:
            continue

        volunteers.append({
            "name": name,
            "roles": roles,
        })

    return volunteers, role_columns


def load_welcome_volunteers(sheet_id: str = rules.SHEET_ID, gid: str = rules.WELCOME_GID) -> List[Dict]:
    """
    Load Welcome volunteers from Google Sheet.
    Returns list of dicts, one per active volunteer:
    {
        "name": str,
        "lead": bool,
        "member": bool,
        "gender": str,          # "male" or "female" (lowercase)
        "couple_id": int|None,  # numeric ID, partners share same ID
        "senior": bool,
    }
    Inactive volunteers (not lead AND not member) are excluded.
    """
    df = fetch_sheet(sheet_id, gid)
    return parse_welcome_volunteers(df)


def parse_welcome_volunteers(df: pd.DataFrame) -> List[Dict]:
    """Parse a Welcome DataFrame into volunteer dicts. Testable without network."""
    cols = rules.W_SHEET_COLUMNS

    col_name = _find_column(df, cols["name"])
    col_lead = _find_column(df, cols["lead"])
    col_member = _find_column(df, cols["member"])
    col_gender = _find_column(df, cols["gender"])
    col_couple = _find_column(df, cols["couple"])
    col_senior = _find_column(df, cols["senior"])

    if not col_name:
        raise ValueError("Missing 'Name' column in Welcome sheet")

    volunteers = []
    for _, row in df.iterrows():
        name = _normalize_name(row.get(col_name))
        if not name:
            continue

        lead = _is_yes(row.get(col_lead)) if col_lead else False
        member = _is_yes(row.get(col_member)) if col_member else False

        # Skip inactive (not lead and not member)
        if not lead and not member:
            continue

        gender_raw = str(row.get(col_gender, "")).strip().lower() if col_gender else ""
        gender = gender_raw if gender_raw in ("male", "female") else ""

        couple_raw = row.get(col_couple) if col_couple else None
        couple_id = None
        if couple_raw is not None and not pd.isna(couple_raw):
            try:
                couple_id = int(float(couple_raw))
            except (ValueError, TypeError):
                couple_id = None

        senior = _is_yes(row.get(col_senior)) if col_senior else False

        volunteers.append({
            "name": name,
            "lead": lead,
            "member": member,
            "gender": gender,
            "couple_id": couple_id,
            "senior": senior,
        })

    return volunteers


def get_couple_map(volunteers: List[Dict]) -> Dict[str, str]:
    """
    Build a map of person -> partner for couples.
    Only includes pairs (couple_id shared by exactly 2 people).
    """
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
