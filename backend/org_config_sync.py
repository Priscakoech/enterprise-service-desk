"""
Reusable sync logic for org_config.py ↔ database.
- Reads org_config.py → creates departments/teams in DB
- Reads org_config.py → creates/syncs default SLA policy in DB
- Writes DB state back → org_config.py when teams/departments change via UI
Tracks the file's last-modified time so it only re-syncs when the file changes.
"""
import sys
import os
from pathlib import Path

_last_mtime = 0.0
_write_lock = False  # Prevent feedback loop when we write the file ourselves


def get_config_path():
    return Path(__file__).resolve().parent / 'org_config.py'


def has_config_changed():
    """Return True if org_config.py has been modified since last sync."""
    global _last_mtime
    config_file = get_config_path()
    if not config_file.exists():
        return False
    current_mtime = os.path.getmtime(config_file)
    return current_mtime != _last_mtime


def get_factory_sla_defaults():
    """
    Get the factory default SLA policy configuration from org_config.py.
    Returns the DEFAULT_SLA_POLICY dict or None if not defined.
    """
    config_file = get_config_path()
    if not config_file.exists():
        return None

    config_dir = str(config_file.parent)
    if config_dir not in sys.path:
        sys.path.insert(0, config_dir)

    # Force re-import to get fresh values
    if 'org_config' in sys.modules:
        del sys.modules['org_config']

    try:
        from org_config import DEFAULT_SLA_POLICY
        return DEFAULT_SLA_POLICY
    except ImportError:
        return None


def sync_default_sla_policy(force=False):
    """
    Sync the default SLA policy from org_config.py into the database.
    Creates the policy and its targets if they don't exist.
    If the system default policy exists but has no targets, recreates them.
    Returns True if the policy was created or updated, False otherwise.
    """
    factory_config = get_factory_sla_defaults()
    if not factory_config:
        return False

    from servicedesk.models import SLAPolicy, SLATarget

    # Find or create the system default policy
    system_policy = SLAPolicy.objects.filter(is_system_default=True).first()

    if system_policy is None:
        # Create the system default policy
        system_policy = SLAPolicy.objects.create(
            name=factory_config.get('name', 'Standard SLA Policy'),
            description=factory_config.get('description', 'System default SLA policy'),
            is_active=factory_config.get('is_active', True),
            is_default=True,  # Also set as the default fallback
            is_system_default=True,
            position=9999,  # Low priority - should match last
        )
        _create_sla_targets(system_policy, factory_config.get('targets', {}))
        return True

    # Check if the policy has targets; if not, recreate them
    if not system_policy.targets.exists():
        _create_sla_targets(system_policy, factory_config.get('targets', {}))
        return True

    return False


def reset_sla_to_factory():
    """
    Reset the system default SLA policy to factory settings from org_config.py.
    This deletes all existing targets and recreates them from the config file.
    Returns True if reset was successful, False otherwise.
    """
    factory_config = get_factory_sla_defaults()
    if not factory_config:
        return False

    from servicedesk.models import SLAPolicy, SLATarget

    # Find the system default policy
    system_policy = SLAPolicy.objects.filter(is_system_default=True).first()

    if system_policy is None:
        # Create it if it doesn't exist
        return sync_default_sla_policy(force=True)

    # Update policy fields from factory config
    system_policy.name = factory_config.get('name', 'Standard SLA Policy')
    system_policy.description = factory_config.get('description', 'System default SLA policy')
    system_policy.is_active = factory_config.get('is_active', True)
    system_policy.is_default = True
    system_policy.team = None
    system_policy.department = None
    system_policy.save()

    # Delete all existing targets and recreate from factory config
    system_policy.targets.all().delete()
    _create_sla_targets(system_policy, factory_config.get('targets', {}))

    return True


def _create_sla_targets(policy, targets_config):
    """
    Create SLATarget records for a policy from the targets configuration.
    targets_config format: {"metric": {"priority": minutes, ...}, ...}
    """
    from servicedesk.models import SLATarget

    for metric, priorities in targets_config.items():
        for priority, minutes in priorities.items():
            SLATarget.objects.get_or_create(
                policy=policy,
                metric=metric,
                priority=priority,
                defaults={'target_minutes': minutes},
            )


def sync_org_config(force=False):
    """
    Sync departments/teams and default SLA policy from org_config.py into the database.
    Skips if the file hasn't changed since last sync (unless force=True).
    Returns (created_depts, created_teams) tuple.
    """
    global _last_mtime

    config_file = get_config_path()
    if not config_file.exists():
        return 0, 0

    current_mtime = os.path.getmtime(config_file)
    if not force and current_mtime == _last_mtime:
        return 0, 0

    # Import the config
    config_dir = str(config_file.parent)
    if config_dir not in sys.path:
        sys.path.insert(0, config_dir)

    # Force re-import in case file changed
    if 'org_config' in sys.modules:
        del sys.modules['org_config']

    try:
        from org_config import DEPARTMENTS
    except ImportError:
        return 0, 0

    from teams.models import Department, Team

    created_depts = 0
    created_teams = 0

    config_dept_names = set(DEPARTMENTS.keys())
    config_team_map = {}  # dept_name -> set of team names
    for dept_name, teams in DEPARTMENTS.items():
        config_team_map[dept_name] = set(teams)

    for dept_name, teams in DEPARTMENTS.items():
        dept, dept_created = Department.objects.get_or_create(
            name=dept_name,
            defaults={'description': ''},
        )
        if dept_created:
            created_depts += 1

        for team_name in teams:
            _, team_created = Team.objects.get_or_create(
                name=team_name,
                department=dept,
                defaults={'description': ''},
            )
            if team_created:
                created_teams += 1

        # Delete teams no longer in the config for this department
        Team.objects.filter(department=dept).exclude(
            name__in=config_team_map[dept_name]
        ).delete()

    # Delete departments no longer in the config
    Department.objects.exclude(name__in=config_dept_names).delete()

    # Sync the default SLA policy
    sync_default_sla_policy()

    _last_mtime = current_mtime
    return created_depts, created_teams


def write_config_from_db():
    """
    Write the current DB state of departments/teams back to org_config.py.
    Called when a team or department is created/updated/deleted via the UI.
    """
    global _last_mtime, _write_lock

    if _write_lock:
        return
    _write_lock = True

    try:
        from teams.models import Department, Team

        departments = Department.objects.all().order_by('name')
        data = {}
        for dept in departments:
            teams = list(
                Team.objects.filter(department=dept)
                .order_by('name')
                .values_list('name', flat=True)
            )
            data[dept.name] = teams

        config_file = get_config_path()
        lines = [
            '# Organization Configuration',
            '# --------------------------',
            '# Edit this file to define your organization\'s departments and teams.',
            '# Changes are auto-detected at runtime — no server restart needed.',
            '# You can also manually run: python manage.py sync_org_config',
            '# New departments/teams will be created automatically.',
            '# Existing ones (matched by name) will NOT be duplicated.',
            '',
            'DEPARTMENTS = {',
        ]

        dept_items = list(data.items())
        for i, (dept_name, teams) in enumerate(dept_items):
            lines.append(f'    "{dept_name}": [')
            for team in teams:
                lines.append(f'        "{team}",')
            lines.append('    ],')

        lines.append('}')
        lines.append('')

        # Append the DEFAULT_SLA_POLICY section (read from file to preserve factory defaults)
        factory_sla = get_factory_sla_defaults()
        if factory_sla:
            lines.append('# Default SLA Policy Configuration')
            lines.append('# ---------------------------------')
            lines.append("# This defines the system's default (factory) SLA policy.")
            lines.append('# It is automatically created/synced when the server starts.')
            lines.append('# Changes made via admin panel are stored in the database.')
            lines.append('# To reset the default policy to factory settings, use the "Reset to Factory" option.')
            lines.append('# Note: Custom SLA policies created via admin panel are NOT stored here.')
            lines.append('')
            lines.append('DEFAULT_SLA_POLICY = {')
            lines.append(f'    "name": "{factory_sla.get("name", "Standard SLA Policy")}",')
            lines.append(f'    "description": "{factory_sla.get("description", "")}",')
            lines.append(f'    "is_active": {factory_sla.get("is_active", True)},')
            lines.append('    "targets": {')
            lines.append('        # Format: "metric": {"urgent": mins, "high": mins, "normal": mins, "low": mins}')
            targets = factory_sla.get('targets', {})
            for metric, priorities in targets.items():
                priority_str = ', '.join(f'"{p}": {m}' for p, m in priorities.items())
                lines.append(f'        "{metric}": {{{priority_str}}},')
            lines.append('    },')
            lines.append('}')
            lines.append('')

        config_file.write_text('\n'.join(lines), encoding='utf-8')
        _last_mtime = os.path.getmtime(config_file)
    finally:
        _write_lock = False
