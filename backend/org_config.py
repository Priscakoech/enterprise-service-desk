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
