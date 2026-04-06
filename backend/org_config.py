# Organization Configuration
# --------------------------
# Edit this file to define your organization's departments and teams.
# Changes are auto-detected at runtime — no server restart needed.
# You can also manually run: python manage.py sync_org_config
# New departments/teams will be created automatically.
# Existing ones (matched by name) will NOT be duplicated.

DEPARTMENTS = {
    "Customer Support": [
        "Billing Inquiries",
        "General Questions",
        "Technical Support",
    ],
    "Finance": [
        "Accounts Payable",
        "Accounts Receivable",
        "Budgeting",
    ],
    "HR": [
        "Benefits",
        "Employee Relations",
        "Leave Requests",
        "Onboarding",
        "Recruitment",
    ],
    "IT": [
        "Access & Permissions",
        "Hardware",
        "Network",
        "Software",
    ],
    "Marketing": [
        "Campaigns",
        "Content Creation",
        "Social Media",
    ],
    "Operations": [
        "Logistics",
    ],
}

# Default SLA Policy Configuration
# ---------------------------------
# This defines the system's default (factory) SLA policy.
# It is automatically created/synced when the server starts.
# Changes made via admin panel are stored in the database.
# To reset the default policy to factory settings, use the "Reset to Factory" option.
# Note: Custom SLA policies created via admin panel are NOT stored here.

DEFAULT_SLA_POLICY = {
    "name": "Standard SLA Policy",
    "description": "Default SLA policy applied when no specific policy matches. This is the system's factory default policy.",
    "is_active": True,
    "targets": {
        # Format: "metric": {"urgent": mins, "high": mins, "normal": mins, "low": mins}
        "first_reply_time": {"urgent": 30, "high": 60, "normal": 240, "low": 480},
        "next_reply_time": {"urgent": 30, "high": 60, "normal": 240, "low": 480},
        "total_resolution_time": {"urgent": 240, "high": 480, "normal": 1440, "low": 2880},
        "requester_wait_time": {"urgent": 120, "high": 240, "normal": 720, "low": 1440},
        "agent_work_time": {"urgent": 120, "high": 240, "normal": 480, "low": 960},
    },
}
