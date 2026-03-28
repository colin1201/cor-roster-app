"""
COR Roster App — Rules Configuration

Every scheduling constant lives here. No logic, no side effects.
Each constant maps to a rule in RULES.md and a test in tests/.
"""

# ---------------------------------------------------------------------------
# Google Sheets
# ---------------------------------------------------------------------------
SHEET_ID = "1jh6ScfqpHe7rRN1s-9NYPsm7hwqWWLjdLKTYThRRGUo"
MT_GID = "0"
WELCOME_GID = "2080125013"

GSHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

# ---------------------------------------------------------------------------
# Ministries
# ---------------------------------------------------------------------------
MINISTRY_MEDIA_TECH = "Media Tech"
MINISTRY_WELCOME = "Welcome"

# ---------------------------------------------------------------------------
# Media Tech — Roles
# ---------------------------------------------------------------------------
MT_TECH_ROLES = ["Stream Director", "Camera 1", "Projection", "Sound"]
MT_LEAD_ROLE = "Media Team Lead"
MT_CAM2_ROLE = "Cam 2"

# Display order for the roster grid (rows)
MT_ROLES_DISPLAY = [
    "Details",
    "Stream Director",
    "Camera 1",
    "Projection",
    "Sound",
    "Cam 2",
    "Media Team Lead",
]

# ---------------------------------------------------------------------------
# Media Tech — Lead Logic
# ---------------------------------------------------------------------------
# These three are equal priority. If any are in the crew, one becomes lead.
MT_PRIMARY_LEADS = {"Gavin", "Ben", "Mich Lo"}

# Darrell is activated ONLY when no primary lead is in the crew.
MT_FALLBACK_LEAD = "Darrell"

# ---------------------------------------------------------------------------
# Media Tech — Sheet Column Headers
# ---------------------------------------------------------------------------
MT_SHEET_COLUMNS = {
    "name": "Name",
    "lead": "Media Team Lead",
    "stream_director": "Stream Director",
    "camera_1": "Camera 1",
    "projection": "Projection",
    "sound": "Sound",
}

# ---------------------------------------------------------------------------
# Welcome — Roles
# ---------------------------------------------------------------------------
W_LEAD_ROLE = "Welcome Team Lead"
W_MEMBER_ROLES_HC = ["Member 1", "Member 2", "Member 3", "Member 4"]
W_MEMBER_ROLES_NON_HC = ["Member 1", "Member 2", "Member 3"]

# Display order for the roster grid (rows)
W_ROLES_DISPLAY_HC = [
    "Details",
    "Welcome Team Lead",
    "Member 1",
    "Member 2",
    "Member 3",
    "Member 4",
]
W_ROLES_DISPLAY_NON_HC = [
    "Details",
    "Welcome Team Lead",
    "Member 1",
    "Member 2",
    "Member 3",
]

# ---------------------------------------------------------------------------
# Welcome — Sheet Column Headers
# ---------------------------------------------------------------------------
W_SHEET_COLUMNS = {
    "name": "Name",
    "lead": "Welcome Team Lead",
    "member": "Member",
    "gender": "Gender",
    "couple": "Couple",
    "senior": "Senior citizen",
}

# ---------------------------------------------------------------------------
# Service Defaults
# ---------------------------------------------------------------------------
# Which Sundays of the month get HC auto-checked (1st and 3rd)
HC_DEFAULT_SUNDAYS = [1, 3]

# Which Sundays of the month get Combined auto-checked (1st)
COMBINED_DEFAULT_SUNDAYS = [1]

# Always generate 3 consecutive months
ROSTER_MONTH_COUNT = 3

# ---------------------------------------------------------------------------
# Welcome — Staffing
# ---------------------------------------------------------------------------
W_HC_MEMBER_COUNT = 4
W_NON_HC_MEMBER_COUNT = 3
